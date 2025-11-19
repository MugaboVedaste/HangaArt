from django.db import models
from django.conf import settings

class Order(models.Model):
    PAYMENT_METHODS = [
        ("card", "Debit/Credit Card"),
        ("mobile", "Mobile Money"),
        ("paypal", "PayPal"),
        ("bank", "Bank Transfer"),
    ]

    ORDER_STATUS = [
        ("pending_payment", "Pending Payment"),
        ("paid", "Paid"),
        ("processing", "Processing"),          # packaging stage
        ("shipped", "Shipped"),                # in transit
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=30, unique=True)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, blank=True, null=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)  # from gateway
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default="pending_payment")

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    shipping_address = models.TextField(blank=True, null=True)
    tracking_number = models.CharField(max_length=50, blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.order_number} - {self.buyer.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    artwork = models.ForeignKey("artworks.Artwork", on_delete=models.PROTECT, related_name="order_items")

    price = models.DecimalField(max_digits=12, decimal_places=2)    # snapshot to avoid price updates
    quantity = models.PositiveIntegerField(default=1)               # in case digital prints allowed later

    def __str__(self):
        return f"{self.artwork.title} (Order {self.order.order_number})"
