from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.views.decorators.csrf import csrf_exempt
from .views import PaymentTransactionViewSet, PaymentWebhookView, initiate_payment, check_payment_status

router = DefaultRouter()
router.register(r'payments', PaymentTransactionViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('payments/webhook/', PaymentWebhookView.as_view(), name='payment_webhook'),
    path('payments/initiate/<int:order_id>/', csrf_exempt(initiate_payment), name='initiate_payment'),
    path('payments/check/<int:payment_id>/', csrf_exempt(check_payment_status), name='check_payment_status'),
]
