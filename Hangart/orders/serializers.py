from rest_framework import serializers
from .models import Order, OrderItem
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
