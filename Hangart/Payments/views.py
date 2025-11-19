from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import PaymentTransaction, PaymentLog
from .serializers import (
    PaymentTransactionSerializer,
    PaymentTransactionListSerializer,
    PaymentWebhookSerializer
)
from .permissions import IsPaymentOwnerOrAdmin, IsBuyer, IsAdminUser
from orders.models import Order
import uuid


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
@permission_classes([permissions.IsAuthenticated])
def initiate_payment(request, order_id):
    """
    Initiate payment for an order.
    POST /api/payments/initiate/<order_id>/
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
    
    serializer = PaymentTransactionSerializer(payment)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
