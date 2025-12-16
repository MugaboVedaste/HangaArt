from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Order, OrderItem, RefundRequest
from .serializers import (
    OrderSerializer,
    OrderListSerializer,
    OrderStatusUpdateSerializer,
    RefundRequestSerializer,
    RefundRequestListSerializer,
    RefundReviewSerializer
)
from .permissions import IsBuyerOwnerOrAdmin, IsBuyer, IsAdminUser


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for order management.
    
    - List: Buyer sees their own orders, Admin sees all
    - Retrieve: Buyer sees own order, Admin sees any
    - Create: Buyers only
    - Update: Admin only (for status updates)
    """
    queryset = Order.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'update_status':
            return OrderStatusUpdateSerializer
        return OrderSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsBuyer]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        elif self.action == 'update_status':
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated, IsBuyerOwnerOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin sees all orders
        if user.role == 'admin':
            return Order.objects.all()
        
        # Buyers see only their own orders
        if user.role == 'buyer':
            return Order.objects.filter(buyer=user)
        
        # Artists shouldn't access orders directly
        return Order.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)
    
    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        """
        Admin-only: Update order status and tracking info.
        PATCH /api/orders/{id}/update-status/
        """
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            
            # If order is marked as paid, update artworks availability
            if order.status == 'paid':
                for item in order.items.all():
                    artwork = item.artwork
                    artwork.is_available = False
                    artwork.status = 'sold'
                    artwork.save()
            
            return Response(OrderSerializer(order).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='my-orders')
    def my_orders(self, request):
        """
        Get all orders for the authenticated buyer.
        GET /api/orders/my-orders/
        """
        if request.user.role != 'buyer':
            return Response(
                {'error': 'Only buyers can access this endpoint.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RefundRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for refund request management.
    
    - List: Buyer sees their own refund requests, Admin sees all
    - Create: Buyers only (for paid orders)
    - Update: Admin only (for reviewing requests)
    """
    queryset = RefundRequest.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'reason']
    ordering_fields = ['created_at', 'refund_amount']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RefundRequestListSerializer
        elif self.action == 'review':
            return RefundReviewSerializer
        return RefundRequestSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsBuyer]
        elif self.action in ['update', 'partial_update', 'destroy', 'review']:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin sees all refund requests
        if user.role == 'admin':
            return RefundRequest.objects.all()
        
        # Buyers see only their own refund requests
        if user.role == 'buyer':
            return RefundRequest.objects.filter(buyer=user)
        
        return RefundRequest.objects.none()
    
    def perform_create(self, serializer):
        """Create refund request for buyer"""
        serializer.save(buyer=self.request.user)
    
    @action(detail=True, methods=['patch'], url_path='review')
    def review(self, request, pk=None):
        """
        Admin-only: Review and approve/reject refund request.
        PATCH /api/refund-requests/{id}/review/
        
        Body: {
            "status": "approved" | "rejected" | "processed",
            "admin_response": "Reason for decision"
        }
        """
        refund_request = self.get_object()
        
        if refund_request.status != 'pending':
            return Response(
                {'error': 'Only pending refund requests can be reviewed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = RefundReviewSerializer(
            refund_request, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(RefundRequestSerializer(refund_request).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='my-refund-requests')
    def my_refund_requests(self, request):
        """
        Get all refund requests for the authenticated buyer.
        GET /api/refund-requests/my-refund-requests/
        """
        if request.user.role != 'buyer':
            return Response(
                {'error': 'Only buyers can access this endpoint.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='pending')
    def pending_requests(self, request):
        """
        Admin-only: Get all pending refund requests.
        GET /api/refund-requests/pending/
        """
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admins can access this endpoint.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = RefundRequest.objects.filter(status='pending')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = RefundRequestListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = RefundRequestListSerializer(queryset, many=True)
        return Response(serializer.data)
