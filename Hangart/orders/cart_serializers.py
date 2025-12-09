from rest_framework import serializers
from .models import Cart, CartItem
from artworks.serializers import ArtworkListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    artwork = ArtworkListSerializer(read_only=True)
    artwork_id = serializers.IntegerField(write_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'artwork', 'artwork_id', 'quantity', 'subtotal', 'added_at']
        read_only_fields = ['added_at']

    def get_subtotal(self, obj):
        return obj.artwork.price * obj.quantity

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

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        if value > 1:
            raise serializers.ValidationError("Only one quantity per artwork is allowed.")
        return value


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_items', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class AddToCartSerializer(serializers.Serializer):
    artwork_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1)

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

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        if value > 1:
            raise serializers.ValidationError("Only one quantity per artwork is allowed.")
        return value
