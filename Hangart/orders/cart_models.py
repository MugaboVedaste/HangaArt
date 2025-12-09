from django.db import models
from django.conf import settings


class Cart(models.Model):
    """Shopping cart for buyers"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart - {self.user.username}"
    
    @property
    def total_items(self):
        return self.items.count()
    
    @property
    def total_price(self):
        return sum(item.artwork.price * item.quantity for item in self.items.all())


class CartItem(models.Model):
    """Items in shopping cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    artwork = models.ForeignKey('artworks.Artwork', on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'artwork')

    def __str__(self):
        return f"{self.artwork.title} x{self.quantity} in {self.cart.user.username}'s cart"
