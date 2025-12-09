from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Cart, CartItem
from .cart_serializers import CartSerializer, CartItemSerializer, AddToCartSerializer
from .permissions import IsBuyer


class CartViewSet(viewsets.ViewSet):
    """
    ViewSet for shopping cart management.
    
    Endpoints:
    - GET /api/cart/ - View current cart
    - POST /api/cart/add/ - Add item to cart
    - PATCH /api/cart/update/<item_id>/ - Update item quantity
    - DELETE /api/cart/remove/<item_id>/ - Remove item from cart
    - DELETE /api/cart/clear/ - Clear entire cart
    """
    permission_classes = [permissions.IsAuthenticated, IsBuyer]

    def get_or_create_cart(self, user):
        """Get or create cart for the user"""
        cart, created = Cart.objects.get_or_create(user=user)
        return cart

    def list(self, request):
        """
        GET /api/cart/
        Get current user's cart with all items
        """
        cart = self.get_or_create_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        """
        POST /api/cart/add/
        Add an artwork to cart
        
        Request body:
        {
            "artwork_id": 42,
            "quantity": 1
        }
        """
        serializer = AddToCartSerializer(data=request.data)
        if serializer.is_valid():
            cart = self.get_or_create_cart(request.user)
            artwork_id = serializer.validated_data['artwork_id']
            quantity = serializer.validated_data['quantity']

            # Check if artwork already in cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                artwork_id=artwork_id,
                defaults={'quantity': quantity}
            )

            if not created:
                # Update quantity if already exists
                cart_item.quantity = quantity
                cart_item.save()
                message = "Cart item updated"
            else:
                message = "Item added to cart"

            return Response({
                'message': message,
                'cart': CartSerializer(cart).data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='update')
    def update_item(self, request, pk=None):
        """
        PATCH /api/cart/update/<item_id>/
        Update cart item quantity
        
        Request body:
        {
            "quantity": 1
        }
        """
        try:
            cart = self.get_or_create_cart(request.user)
            cart_item = CartItem.objects.get(id=pk, cart=cart)
            
            quantity = request.data.get('quantity', 1)
            if quantity < 1:
                return Response(
                    {'error': 'Quantity must be at least 1'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cart_item.quantity = quantity
            cart_item.save()
            
            return Response({
                'message': 'Cart item updated',
                'cart': CartSerializer(cart).data
            })
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['delete'], url_path='remove')
    def remove_item(self, request, pk=None):
        """
        DELETE /api/cart/remove/<item_id>/
        Remove an item from cart
        """
        try:
            cart = self.get_or_create_cart(request.user)
            cart_item = CartItem.objects.get(id=pk, cart=cart)
            cart_item.delete()
            
            return Response({
                'message': 'Item removed from cart',
                'cart': CartSerializer(cart).data
            })
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """
        DELETE /api/cart/clear/
        Remove all items from cart
        """
        cart = self.get_or_create_cart(request.user)
        cart.items.all().delete()
        
        return Response({
            'message': 'Cart cleared',
            'cart': CartSerializer(cart).data
        })
