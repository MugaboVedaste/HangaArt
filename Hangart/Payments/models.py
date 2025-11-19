from django.db import models
from django.conf import settings
from orders.models import Order


class PaymentTransaction(models.Model):

    PAYMENT_METHODS = [
        ("momo", "Mobile Money"),
        ("card", "Credit/Debit Card"),
        ("paypal", "PayPal"),
        ("bank", "Bank Transfer"),
    ]

    PAYMENT_STATUS = [
        ("pending", "Pending"),
        ("successful", "Successful"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Gateway data
    transaction_id = models.CharField(max_length=200, blank=True, null=True)
    provider_response = models.JSONField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for Order {self.order.order_number} - {self.status}"

class PaymentLog(models.Model):
    payment = models.ForeignKey(PaymentTransaction, on_delete=models.CASCADE, related_name="logs")
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for {self.payment.transaction_id}"
