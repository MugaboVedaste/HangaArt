from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import PaymentTransaction, PaymentLog
from .serializers import (
    PaymentTransactionSerializer,
    PaymentTransactionListSerializer,
    PaymentWebhookSerializer
)
from .permissions import IsPaymentOwnerOrAdmin, IsBuyer, IsAdminUser
from .services import MoMoPaymentService, FlutterwavePaymentService
from .mock_payment_service import MockMoMoPaymentService
from orders.models import Order
import uuid

# Use mock service if MoMo credentials not configured
USE_MOCK_PAYMENT = not getattr(settings, 'MOMO_API_USER', '') or not getattr(settings, 'MOMO_API_KEY', '')


class PaymentTransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for payment transaction management.
    
    - List: User sees their own payments, Admin sees all
    - Retrieve: User sees own payment, Admin sees any
    - Create: Buyers only
    - Update: Admin only
    """
    queryset = PaymentTransaction.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment_method', 'order']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PaymentTransactionListSerializer
        return PaymentTransactionSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsBuyer]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated, IsPaymentOwnerOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin sees all payments
        if user.role == 'admin':
            return PaymentTransaction.objects.all()
        
        # Users see only their own payments
        return PaymentTransaction.objects.filter(user=user)
    
    def perform_create(self, serializer):
        # Generate unique transaction ID
        transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        payment = serializer.save(
            user=self.request.user,
            transaction_id=transaction_id
        )
        
        # Create initial log
        PaymentLog.objects.create(
            payment=payment,
            message=f"Payment initiated with {payment.payment_method}"
        )
    
    @action(detail=False, methods=['get'], url_path='my-payments')
    def my_payments(self, request):
        """
        Get all payment transactions for the authenticated user.
        GET /api/payments/my-payments/
        """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PaymentWebhookView(APIView):
    """
    Webhook endpoint for payment gateway callbacks.
    POST /api/payments/webhook/
    
    This endpoint should be called by the payment provider to update payment status.
    No authentication required (payment providers can't authenticate).
    Consider adding signature verification for production.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PaymentWebhookSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        transaction_id = serializer.validated_data['transaction_id']
        payment_status = serializer.validated_data['status']
        provider_response = serializer.validated_data.get('provider_response', {})
        
        try:
            payment = PaymentTransaction.objects.get(transaction_id=transaction_id)
            
            # Update payment status
            payment.status = payment_status
            payment.provider_response = provider_response
            payment.save()
            
            # Log the webhook
            PaymentLog.objects.create(
                payment=payment,
                message=f"Webhook received: status changed to {payment_status}"
            )
            
            # If payment successful, update order status
            if payment_status == 'successful':
                order = payment.order
                order.status = 'paid'
                order.payment_reference = transaction_id
                order.save()
                
                # Mark artworks as sold
                for item in order.items.all():
                    artwork = item.artwork
                    artwork.is_available = False
                    artwork.status = 'sold'
                    artwork.save()
                
                PaymentLog.objects.create(
                    payment=payment,
                    message=f"Order {order.order_number} marked as paid"
                )
            
            elif payment_status == 'failed':
                PaymentLog.objects.create(
                    payment=payment,
                    message="Payment failed - order remains unpaid"
                )
            
            return Response({
                'message': 'Webhook processed successfully',
                'transaction_id': transaction_id,
                'status': payment_status
            }, status=status.HTTP_200_OK)
        
        except PaymentTransaction.DoesNotExist:
            return Response(
                {'error': 'Payment transaction not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([permissions.IsAuthenticated])
def initiate_payment(request, order_id):
    """
    Initiate payment for an order.
    POST /api/payments/initiate/<order_id>/
    
    Body: {"payment_method": "momo", "phone": "250788123456"}
    """
    try:
        order = Order.objects.get(id=order_id, buyer=request.user)
    except Order.DoesNotExist:
        return Response(
            {'error': 'Order not found or does not belong to you'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if payment already exists
    if hasattr(order, 'payment'):
        return Response(
            {'error': 'Payment already exists for this order',
             'payment_id': order.payment.id},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    payment_method = request.data.get('payment_method')
    if not payment_method:
        return Response(
            {'error': 'payment_method is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get phone number from request (optional - will use profile phone if not provided)
    phone_number = request.data.get('phone')
    
    # Update order payment method
    order.payment_method = payment_method
    order.save()
    
    # Create payment transaction
    transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    payment = PaymentTransaction.objects.create(
        order=order,
        user=request.user,
        payment_method=payment_method,
        amount=order.total_amount,
        transaction_id=transaction_id,
        status='pending'
    )
    
    PaymentLog.objects.create(
        payment=payment,
        message=f"Payment initiated for order {order.order_number}"
    )
    
    # Process payment based on method
    if payment_method == 'momo':
        # Use mock service if MoMo not configured, otherwise use real service
        if USE_MOCK_PAYMENT:
            momo_service = MockMoMoPaymentService()
            payment.provider_response = {'mode': 'MOCK'}
            payment.save()
        else:
            momo_service = MoMoPaymentService()
        
        result = momo_service.request_to_pay(payment, phone_number=phone_number)
        
        if result.get('success'):
            serializer = PaymentTransactionSerializer(payment)
            response_data = {
                'success': True,
                'payment': serializer.data,
                'message': result.get('message'),
                'phone': result.get('phone'),
                'reference': result.get('reference'),
                'instructions': 'Please check your phone and approve the payment request.'
            }
            
            # Add mock warning if in mock mode
            if USE_MOCK_PAYMENT or result.get('mock'):
                response_data['mode'] = 'MOCK'
                response_data['warning'] = '⚠️  MOCK MODE: Payment will auto-approve in 5 seconds. Configure MOMO_API_USER and MOMO_API_KEY for real payments.'
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            payment.status = 'failed'
            payment.save()
            return Response({
                'success': False,
                'error': 'Payment initiation failed',
                'details': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    elif payment_method in ['card', 'paypal', 'bank']:
        # Future implementation for Flutterwave
        return Response({
            'error': 'This payment method is not yet configured. Please use Mobile Money (momo).'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    else:
        return Response({
            'error': f'Invalid payment method: {payment_method}. Use "momo" for Mobile Money.'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([permissions.IsAuthenticated])
def check_payment_status(request, payment_id):
    """
    Check payment status (poll this endpoint for MoMo payments)
    GET /api/payments/check/<payment_id>/
    """
    try:
        payment = PaymentTransaction.objects.get(id=payment_id)
    except PaymentTransaction.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check permission
    if payment.user != request.user and request.user.role != 'admin':
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    # If payment already completed, return current status
    if payment.status in ['successful', 'failed', 'cancelled', 'refunded']:
        serializer = PaymentTransactionSerializer(payment)
        return Response({
            'status': payment.status,
            'payment': serializer.data
        })
    
    # Check with MoMo if payment is pending
    if payment.payment_method == 'momo' and payment.status == 'pending':
        # Use mock service if MoMo not configured
        if USE_MOCK_PAYMENT or payment.provider_response.get('mock'):
            momo_service = MockMoMoPaymentService()
        else:
            momo_service = MoMoPaymentService()
        
        result = momo_service.update_payment_from_status_check(payment)
        
        # Refresh payment from DB
        payment.refresh_from_db()
        serializer = PaymentTransactionSerializer(payment)
        
        return Response({
            'status': payment.status,
            'payment': serializer.data,
            'checked_at': result
        })
    
    serializer = PaymentTransactionSerializer(payment)
    return Response({
        'status': payment.status,
        'payment': serializer.data
    })
