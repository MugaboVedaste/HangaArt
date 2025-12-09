from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .serializers import (
    UserSerializer, UserRegistrationSerializer, 
    ArtistProfileSerializer, BuyerProfileSerializer,
    PasswordChangeSerializer, ArtistVerificationSerializer
)
from .models import ArtistProfile, BuyerProfile
from .permissions import IsOwner, IsAdmin

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    Register a new user (artist or buyer).
    POST /api/auth/register/
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    Get or update the current authenticated user's details.
    GET/PUT/PATCH /api/auth/me/
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class PasswordChangeView(APIView):
    """
    Change password for authenticated user.
    POST /api/auth/change-password/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ArtistProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update artist profile for the current user.
    GET/PUT/PATCH /api/profiles/artist/
    """
    serializer_class = ArtistProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    
    def get_object(self):
        # Get or create artist profile for current user
        profile, created = ArtistProfile.objects.get_or_create(user=self.request.user)
        return profile


class BuyerProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update buyer profile for the current user.
    GET/PUT/PATCH /api/profiles/buyer/
    """
    serializer_class = BuyerProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    
    def get_object(self):
        # Get or create buyer profile for current user
        profile, created = BuyerProfile.objects.get_or_create(user=self.request.user)
        return profile


class PublicArtistProfileView(generics.RetrieveAPIView):
    """
    Public view of an artist's profile by user ID.
    GET /api/profiles/artist/<user_id>/
    """
    serializer_class = ArtistProfileSerializer
    permission_classes = [permissions.AllowAny]
    queryset = ArtistProfile.objects.all()
    lookup_field = 'user__id'
    lookup_url_kwarg = 'user_id'


class ArtistListView(generics.ListAPIView):
    """
    List artists.
    - Admins: See all artists (verified and unverified)
    - Others: See only verified artists
    GET /api/artists/
    """
    serializer_class = ArtistProfileSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin sees all artists
        if user.is_authenticated and (user.role == 'admin' or user.is_staff):
            return ArtistProfile.objects.all().select_related('user').order_by('-verified_by_admin', 'user__username')
        
        # Others see only verified artists
        return ArtistProfile.objects.filter(verified_by_admin=True).select_related('user').order_by('user__username')


class ArtistVerificationView(generics.UpdateAPIView):
    """
    Admin-only endpoint to verify/unverify artists.
    PATCH /api/artists/<artist_profile_id>/verify/
    
    Request body:
    {
        "verified_by_admin": true
    }
    """
    serializer_class = ArtistVerificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    queryset = ArtistProfile.objects.all()
    lookup_url_kwarg = 'profile_id'
    
    def perform_update(self, serializer):
        artist_profile = serializer.save()
        verified = serializer.validated_data.get('verified_by_admin')
        
        # Log the verification action
        action = 'verified' if verified else 'unverified'
        print(f"Admin {self.request.user.username} {action} artist {artist_profile.user.username}")
        
        return artist_profile


class BuyerListView(generics.ListAPIView):
    """
    Admin-only endpoint to view all buyers.
    GET /api/buyers/
    """
    serializer_class = BuyerProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    
    def get_queryset(self):
        # Get all buyer users
        buyer_users = User.objects.filter(role='buyer')
        
        # Ensure all buyers have profiles (for existing data)
        for user in buyer_users:
            BuyerProfile.objects.get_or_create(user=user)
        
        # Return all buyer profiles
        return BuyerProfile.objects.all().select_related('user').order_by('user__username')
