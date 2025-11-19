from rest_framework import permissions


class IsPaymentOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to allow:
    - Users to view their own payments
    - Admins to view all payments
    """
    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.role == 'admin':
            return True
        
        # User can only access their own payments
        return obj.user == request.user


class IsBuyer(permissions.BasePermission):
    """
    Only allow buyers to access.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'buyer'
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
