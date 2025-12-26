from rest_framework.permissions import BasePermission
from authentication.models import Vendor


class IsVendorOwnerOrStaff(BasePermission):
    """
    Object-level permission to only allow owners/staff of a vendor to edit it.
    Assumes the view has a vendor_id in the URL.
    """
    
    def has_permission(self, request, view):
        # First check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Better: Check for PERMISSION, not role
        # This way any role with update:own_vendor permission works
        return request.user.has_auth0_permission('update:own_vendor')
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access this specific vendor"""
        # Super admins can access any vendor
        if request.user.has_auth0_role('super_admin'):
            return True
        
        # For Vendor objects
        if isinstance(obj, Vendor):
            # Check if user is the vendor admin
            if obj.admin == request.user:
                return True
            
            # Check if user is vendor staff (through VendorUser relationship)
            return obj.vendor_users.filter(
                user=request.user,
                is_active=True
            ).exists()
        
        return False


class CanManageOwnVendor(BasePermission):
    """
    Permission to check if user can manage their own vendor(s).
    Works with Auth0 permissions + object ownership.
    """
    
    def has_permission(self, request, view):
        # User must be authenticated
        if not request.user.is_authenticated:
            return False
        
        # Must have the update:own_vendor permission from Auth0
        return request.user.has_auth0_permission('update:own_vendor')
    
    def has_object_permission(self, request, view, obj):
        """Check if this is user's own vendor"""
        if isinstance(obj, Vendor):
            # Check direct ownership
            if obj.admin == request.user:
                return True
            
            # Check staff relationship
            return obj.vendor_users.filter(
                user=request.user,
                is_active=True,
                can_edit_vendor_info=True  # Additional field to control edit rights
            ).exists()
        
        return False


class IsVendorReadOnly(BasePermission):
    """
    Anyone with read:vendors can view, but only owners can modify
    """
    
    def has_permission(self, request, view):
        # Read permissions for everyone with read:vendors
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user.has_auth0_permission('read:vendors')
        
        # Write permissions only for vendor admins
        return request.user.has_auth0_permission('update:own_vendor')
    
    def has_object_permission(self, request, view, obj):
        # Anyone can read
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Only owner can write
        if isinstance(obj, Vendor):
            return obj.admin == request.user or request.user.has_auth0_role('super_admin')
        
        return False