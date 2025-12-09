from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet
from .cart_views import CartViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'cart', CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
]
