from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .serializers import (
    UserSerializer, UserRegistrationSerializer, 
    ArtistProfileSerializer, BuyerProfileSerializer,
    PasswordChangeSerializer
)
from .models import ArtistProfile, BuyerProfile
from .permissions import IsOwner

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
    List all verified artists.
    GET /api/artists/
    """
    serializer_class = ArtistProfileSerializer
    permission_classes = [permissions.AllowAny]
    queryset = ArtistProfile.objects.filter(verified_by_admin=True)
