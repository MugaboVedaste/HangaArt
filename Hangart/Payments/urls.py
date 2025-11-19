from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentTransactionViewSet, PaymentWebhookView, initiate_payment

router = DefaultRouter()
router.register(r'payments', PaymentTransactionViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('payments/webhook/', PaymentWebhookView.as_view(), name='payment_webhook'),
    path('payments/initiate/<int:order_id>/', initiate_payment, name='initiate_payment'),
]
