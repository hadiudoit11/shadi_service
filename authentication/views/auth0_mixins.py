
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from ..auth0_permissions import Auth0PermissionChecker, Auth0Permissions
import logging



logger = logging.getLogger(__name__)


class Auth0PermissionRequiredMixin(AccessMixin):
    """
    Mixin that checks Auth0 permissions instead of Django permissions
    """
    permission_required = None
    
    def has_permission(self):
        """Check if user has the required Auth0 permission"""
        user = self.request.user
        
        if not user.is_authenticated:
            return False
        
        if not self.permission_required:
            return True
        
        # Sync permissions if needed
        if user.needs_permission_sync():
            user.sync_auth0_permissions()
        
        # Check single permission or list of permissions
        if isinstance(self.permission_required, str):
            return Auth0PermissionChecker.has_permission(user, self.permission_required)
        elif isinstance(self.permission_required, list):
            # User needs ALL permissions in the list
            return Auth0PermissionChecker.has_all_permissions(user, self.permission_required)
        
        return False
    
    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def handle_no_permission(self):
        """Handle permission denied - return JSON for API views"""
        if hasattr(self, 'error_response'):
            # API view
            return self.error_response(
                "You don't have permission to access this resource",
                status=403
            )
        else:
            # Regular view
            raise PermissionDenied


class Auth0RoleRequiredMixin(AccessMixin):
    """
    Mixin that checks Auth0 roles instead of Django groups
    """
    role_required = None
    
    def has_role(self):
        """Check if user has the required Auth0 role"""
        user = self.request.user
        
        if not user.is_authenticated:
            return False
        
        if not self.role_required:
            return True
        
        # Sync permissions if needed
        if user.needs_permission_sync():
            user.sync_auth0_permissions()
        
        # Check single role or list of roles
        if isinstance(self.role_required, str):
            return Auth0PermissionChecker.has_role(user, self.role_required)
        elif isinstance(self.role_required, list):
            # User needs ANY role in the list
            return any(Auth0PermissionChecker.has_role(user, role) for role in self.role_required)
        
        return False
    
    def dispatch(self, request, *args, **kwargs):
        if not self.has_role():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def handle_no_permission(self):
        """Handle permission denied"""
        if hasattr(self, 'error_response'):
            # API view
            return self.error_response(
                "Your role doesn't allow access to this resource",
                status=403
            )
        else:
            # Regular view
            raise PermissionDenied


# Convenience mixins for common permissions
class CanCreateEventsMixin(Auth0PermissionRequiredMixin):
    permission_required = Auth0Permissions.CREATE_EVENTS


class CanManageVendorsMixin(Auth0PermissionRequiredMixin):
    permission_required = Auth0Permissions.MANAGE_VENDOR_RELATIONSHIPS


class CanManageGuestsMixin(Auth0PermissionRequiredMixin):
    permission_required = Auth0Permissions.MANAGE_GUESTS


class CanEditSchedulesMixin(Auth0PermissionRequiredMixin):
    permission_required = Auth0Permissions.EDIT_SCHEDULES


class CanAccessAnalyticsMixin(Auth0PermissionRequiredMixin):
    permission_required = Auth0Permissions.ACCESS_ANALYTICS


class CanManagePaymentsMixin(Auth0PermissionRequiredMixin):
    permission_required = Auth0Permissions.MANAGE_PAYMENTS


class WeddingPlanningAccessMixin(Auth0PermissionRequiredMixin):
    permission_required = Auth0Permissions.PLAN_WEDDING