from rest_framework import permissions


class IsBuyerOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to allow:
    - Buyers to view/edit their own orders
    - Admins to view/edit all orders
    """
    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.role == 'admin':
            return True
        
        # Buyer can only access their own orders
        if request.user.role == 'buyer':
            return obj.buyer == request.user
        
        return False


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
