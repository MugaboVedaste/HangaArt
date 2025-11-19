from rest_framework import permissions


class IsArtistOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission:
    - Read access for everyone
    - Write access only for the artist who created the artwork
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the artist owner
        return obj.artist == request.user and request.user.role == 'artist'


class IsArtist(permissions.BasePermission):
    """
    Only allow artists to access.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'artist'
        )


class IsAdminUser(permissions.BasePermission):
    """
    Only allow admin users to access.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'admin'
        )
