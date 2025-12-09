from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    UserRegistrationView,
    CurrentUserView,
    PasswordChangeView,
    ArtistProfileView,
    BuyerProfileView,
    PublicArtistProfileView,
    ArtistListView,
    ArtistVerificationView,
    BuyerListView,
)

urlpatterns = [
    # Authentication
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', CurrentUserView.as_view(), name='current_user'),
    path('auth/change-password/', PasswordChangeView.as_view(), name='change_password'),
    
    # Profiles
    path('profiles/artist/', ArtistProfileView.as_view(), name='artist_profile'),
    path('profiles/buyer/', BuyerProfileView.as_view(), name='buyer_profile'),
    path('profiles/artist/<int:user_id>/', PublicArtistProfileView.as_view(), name='public_artist_profile'),
    
    # Public artist listing
    path('artists/', ArtistListView.as_view(), name='artist_list'),
    
    # Admin: Artist verification
    path('artists/<int:profile_id>/verify/', ArtistVerificationView.as_view(), name='artist_verify'),
    
    # Admin: Buyer listing
    path('buyers/', BuyerListView.as_view(), name='buyer_list'),
]
