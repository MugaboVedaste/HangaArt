from rest_framework import serializers
from .models import PaymentTransaction, PaymentLog
from orders.serializers import OrderListSerializer


class PaymentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLog
        fields = ['id', 'message', 'timestamp']


class PaymentTransactionSerializer(serializers.ModelSerializer):
    order = OrderListSerializer(read_only=True)
    order_id = serializers.IntegerField(write_only=True)
    logs = PaymentLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'order', 'order_id', 'user', 'payment_method',
            'amount', 'transaction_id', 'provider_response',
            'status', 'created_at', 'updated_at', 'logs'
        ]
        read_only_fields = ['user', 'transaction_id', 'provider_response', 'created_at', 'updated_at']
    
    def validate_order_id(self, value):
        from orders.models import Order
        try:
            order = Order.objects.get(id=value)
            if order.buyer != self.context['request'].user:
                raise serializers.ValidationError("You can only create payments for your own orders.")
            if hasattr(order, 'payment'):
                raise serializers.ValidationError("Payment already exists for this order.")
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")
        return value
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PaymentTransactionListSerializer(serializers.ModelSerializer):
    """Lighter serializer for payment lists"""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'order_number', 'payment_method', 'amount',
            'status', 'created_at'
        ]


class PaymentWebhookSerializer(serializers.Serializer):
    """
    Serializer for payment gateway webhooks.
    Adjust fields based on your payment provider's webhook format.
    """
    transaction_id = serializers.CharField(required=True)
    status = serializers.ChoiceField(
        choices=['successful', 'failed', 'cancelled'],
        required=True
    )
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    provider_response = serializers.JSONField(required=False)
    order_number = serializers.CharField(required=False)
    
    def validate_transaction_id(self, value):
        """Validate that the transaction exists"""
        try:
            PaymentTransaction.objects.get(transaction_id=value)
        except PaymentTransaction.DoesNotExist:
            raise serializers.ValidationError("Payment transaction not found.")
        return value
