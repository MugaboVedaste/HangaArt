from rest_framework import serializers
from .models import Order, OrderItem, RefundRequest
from artworks.serializers import ArtworkListSerializer
from accounts.serializers import UserSerializer
import uuid


class OrderItemSerializer(serializers.ModelSerializer):
    artwork = ArtworkListSerializer(read_only=True)
    artwork_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'artwork', 'artwork_id', 'price', 'quantity']
        read_only_fields = ['price']
    
    def validate_artwork_id(self, value):
        from artworks.models import Artwork
        try:
            artwork = Artwork.objects.get(id=value)
            if artwork.status != 'approved':
                raise serializers.ValidationError("This artwork is not available for purchase.")
            if not artwork.is_available:
                raise serializers.ValidationError("This artwork is no longer available.")
        except Artwork.DoesNotExist:
            raise serializers.ValidationError("Artwork not found.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    buyer = UserSerializer(read_only=True)
    items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'buyer', 'order_number', 'payment_method', 'payment_reference',
            'status', 'subtotal', 'shipping_fee', 'commission', 'total_amount',
            'shipping_address', 'tracking_number', 'admin_notes',
            'created_at', 'updated_at', 'items'
        ]
        read_only_fields = [
            'order_number', 'payment_reference', 'subtotal', 'total_amount',
            'shipping_fee', 'commission', 'tracking_number', 'admin_notes', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        from artworks.models import Artwork
        from decimal import Decimal
        
        items_data = validated_data.pop('items')
        shipping_address = validated_data.pop('shipping_address', '')
        
        # Fixed shipping fee: $10
        FIXED_SHIPPING_FEE = Decimal('10.00')
        
        # Commission rate: 10%
        COMMISSION_RATE = Decimal('0.10')
        
        # Generate unique order number
        order_number = f"HGA-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate subtotal (artworks total)
        subtotal = Decimal('0.00')
        for item_data in items_data:
            artwork = Artwork.objects.get(id=item_data['artwork_id'])
            subtotal += artwork.price * item_data['quantity']
        
        # Calculate commission (10% of subtotal - deducted from artist earnings)
        commission = subtotal * COMMISSION_RATE
        
        # Calculate total: subtotal + shipping (commission is NOT added to buyer's price)
        total_amount = subtotal + FIXED_SHIPPING_FEE
        
        # Create order
        order = Order.objects.create(
            buyer=self.context['request'].user,
            order_number=order_number,
            subtotal=subtotal,
            shipping_fee=FIXED_SHIPPING_FEE,
            commission=commission,  # Stored for record keeping (artist payout calculation)
            total_amount=total_amount,
            shipping_address=shipping_address,
            status='pending_payment'
        )
        
        # Create order items
        for item_data in items_data:
            artwork = Artwork.objects.get(id=item_data['artwork_id'])
            OrderItem.objects.create(
                order=order,
                artwork=artwork,
                price=artwork.price,  # Snapshot current price
                quantity=item_data['quantity']
            )
        
        # Clear the cart after successful order creation
        try:
            from .models import Cart
            cart = Cart.objects.filter(user=self.context['request'].user).first()
            if cart:
                cart.items.all().delete()
        except Exception as e:
            # Don't fail order creation if cart clearing fails
            pass
        
        return order


class OrderListSerializer(serializers.ModelSerializer):
    """Lighter serializer for order lists"""
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)
    items_count = serializers.IntegerField(source='items.count', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'buyer_name', 'order_number', 'status',
            'total_amount', 'created_at', 'items_count'
        ]


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """Admin-only serializer for updating order status"""
    class Meta:
        model = Order
        fields = ['status', 'tracking_number', 'admin_notes']
    
    def validate_status(self, value):
        allowed_statuses = [
            'pending_payment', 'paid', 'processing', 
            'shipped', 'delivered', 'cancelled', 'refunded'
        ]
        if value not in allowed_statuses:
            raise serializers.ValidationError(f"Invalid status. Choose from: {', '.join(allowed_statuses)}")
        return value


class RefundRequestSerializer(serializers.ModelSerializer):
    """Serializer for refund requests"""
    buyer = UserSerializer(read_only=True)
    order_details = OrderListSerializer(source='order', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = RefundRequest
        fields = [
            'id', 'order', 'order_details', 'buyer', 'reason', 'description',
            'status', 'admin_response', 'reviewed_by_name', 'refund_amount',
            'created_at', 'updated_at', 'reviewed_at'
        ]
        read_only_fields = [
            'buyer', 'status', 'admin_response', 'reviewed_by_name', 
            'refund_amount', 'reviewed_at', 'order_details'
        ]
    
    def validate_order(self, value):
        """Validate that order can be refunded"""
        # Check if order is paid
        if value.status != 'paid':
            raise serializers.ValidationError("Only paid orders can be refunded.")
        
        # Check if refund request already exists
        if hasattr(value, 'refund_request'):
            raise serializers.ValidationError("A refund request already exists for this order.")
        
        # Check if order belongs to the requesting user
        request = self.context.get('request')
        if request and value.buyer != request.user:
            raise serializers.ValidationError("You can only request refunds for your own orders.")
        
        return value
    
    def create(self, validated_data):
        """Create refund request with the order's total amount"""
        validated_data['refund_amount'] = validated_data['order'].total_amount
        validated_data['buyer'] = self.context['request'].user
        return super().create(validated_data)


class RefundRequestListSerializer(serializers.ModelSerializer):
    """Lighter serializer for refund request lists"""
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = RefundRequest
        fields = [
            'id', 'order_number', 'buyer_name', 'reason', 
            'status', 'refund_amount', 'created_at'
        ]


class RefundReviewSerializer(serializers.ModelSerializer):
    """Admin-only serializer for reviewing refund requests"""
    class Meta:
        model = RefundRequest
        fields = ['status', 'admin_response']
    
    def validate_status(self, value):
        """Only allow approved, rejected, or processed status"""
        allowed_statuses = ['approved', 'rejected', 'processed']
        if value not in allowed_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Choose from: {', '.join(allowed_statuses)}"
            )
        return value
    
    def update(self, instance, validated_data):
        """Update refund request and handle order status changes"""
        from django.utils import timezone
        
        instance.status = validated_data.get('status', instance.status)
        instance.admin_response = validated_data.get('admin_response', instance.admin_response)
        instance.reviewed_by = self.context['request'].user
        instance.reviewed_at = timezone.now()
        instance.save()
        
        # If approved, update order status to refunded
        if instance.status == 'approved':
            order = instance.order
            order.status = 'refunded'
            order.save()
            
            # Make artworks available again
            for item in order.items.all():
                artwork = item.artwork
                artwork.is_available = True
                artwork.status = 'approved'
                artwork.save()
        
        # If processed, update payment transaction
        if instance.status == 'processed':
            try:
                payment = instance.order.payment
                payment.status = 'refunded'
                payment.save()
            except:
                pass
        
        return instance
