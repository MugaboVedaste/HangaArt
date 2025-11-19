from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Artwork
from .serializers import (
    ArtworkSerializer, 
    ArtworkListSerializer,
    ArtworkStatusUpdateSerializer
)
from .permissions import IsArtistOwnerOrReadOnly, IsArtist, IsAdminUser


class ArtworkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for artwork CRUD operations.
    
    - List: Public (only approved artworks) or artist's own artworks
    - Retrieve: Public (approved) or artist's own
    - Create: Artists only
    - Update/Delete: Artist owner only
    - Admin actions: Update status
    """
    queryset = Artwork.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'medium', 'status', 'artist']
    search_fields = ['title', 'description', 'artist__username']
    ordering_fields = ['created_at', 'price', 'title']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ArtworkListSerializer
        elif self.action == 'update_status':
            return ArtworkStatusUpdateSerializer
        return ArtworkSerializer
    
    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated, IsArtist]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsArtistOwnerOrReadOnly]
        elif self.action == 'update_status':
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        elif self.action in ['my_artworks', 'submit_for_review']:
            permission_classes = [permissions.IsAuthenticated, IsArtist]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = Artwork.objects.all()
        
        # If user is authenticated artist, show their own artworks
        if self.request.user.is_authenticated and self.request.user.role == 'artist':
            if self.action in ['my_artworks']:
                return queryset.filter(artist=self.request.user)
        
        # If user is admin, show all artworks
        if self.request.user.is_authenticated and self.request.user.role == 'admin':
            return queryset
        
        # For public access, only show approved artworks
        if self.action in ['list', 'retrieve']:
            return queryset.filter(status='approved', is_available=True)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(artist=self.request.user, status='draft')
    
    @action(detail=False, methods=['get'], url_path='my-artworks')
    def my_artworks(self, request):
        """
        Get all artworks for the authenticated artist.
        GET /api/artworks/my-artworks/
        """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='submit')
    def submit_for_review(self, request, pk=None):
        """
        Submit artwork for admin review.
        POST /api/artworks/{id}/submit/
        """
        artwork = self.get_object()
        
        if artwork.artist != request.user:
            return Response(
                {'error': 'You can only submit your own artworks.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if artwork.status not in ['draft', 'rejected']:
            return Response(
                {'error': f'Cannot submit artwork with status: {artwork.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        artwork.status = 'submitted'
        artwork.save()
        
        serializer = self.get_serializer(artwork)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        """
        Admin-only: Update artwork status and add comments.
        PATCH /api/artworks/{id}/update-status/
        """
        artwork = self.get_object()
        serializer = ArtworkStatusUpdateSerializer(artwork, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(ArtworkSerializer(artwork).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
