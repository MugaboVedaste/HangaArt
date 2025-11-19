from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.user == request.user


class IsArtist(permissions.BasePermission):
    """
    Permission to only allow artists to access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'artist'


class IsBuyer(permissions.BasePermission):
    """
    Permission to only allow buyers to access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'buyer'


class IsAdmin(permissions.BasePermission):
    """
    Permission to only allow admins to access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsOwner(permissions.BasePermission):
    """
    Permission to only allow owners of a profile to edit it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
