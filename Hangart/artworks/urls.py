from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArtworkViewSet

router = DefaultRouter()
router.register(r'artworks', ArtworkViewSet, basename='artwork')

urlpatterns = [
    path('', include(router.urls)),
]
