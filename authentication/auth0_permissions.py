"""
Auth0 Permission Management
Handles Auth0 roles and permissions instead of hard-coded database fields
"""

import requests
import logging
from django.conf import settings
from django.utils import timezone
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Auth0 Permission Constants
class Auth0Permissions:
    """Auth0 permission constants - these should match your Auth0 setup"""
    
    # Event Management
    CREATE_EVENTS = 'create:events'
    READ_EVENTS = 'read:events'
    UPDATE_EVENTS = 'update:events'
    DELETE_EVENTS = 'delete:events'
    
    # Vendor Management (for couples/planners managing vendor relationships)
    MANAGE_VENDOR_RELATIONSHIPS = 'manage:vendor_relationships'
    VIEW_VENDORS = 'view:vendors'
    INQUIRE_VENDORS = 'inquire:vendors'
    
    # Vendor Business Management (for vendor representatives)
    # These should be scoped to specific vendor organizations in Auth0
    READ_VENDOR_INFO = 'read:vendor_info'
    EDIT_VENDOR_INFO = 'edit:vendor_info'
    MANAGE_VENDOR_BOOKINGS = 'manage:vendor_bookings'
    RESPOND_VENDOR_INQUIRIES = 'respond:vendor_inquiries'
    VIEW_VENDOR_ANALYTICS = 'view:vendor_analytics'
    MANAGE_VENDOR_TEAM = 'manage:vendor_team'
    
    # Legacy - will be replaced by vendor-specific permissions
    MANAGE_VENDOR_BUSINESS = 'manage:vendor_business'
    RESPOND_TO_INQUIRIES = 'respond:inquiries'
    
    # Guest Management
    MANAGE_GUESTS = 'manage:guests'
    READ_GUESTS = 'read:guests'
    INVITE_GUESTS = 'invite:guests'
    
    # Schedule Management
    EDIT_SCHEDULES = 'edit:schedules'
    READ_SCHEDULES = 'read:schedules'
    
    # Analytics
    ACCESS_ANALYTICS = 'access:analytics'
    EXPORT_REPORTS = 'export:reports'
    
    # Payment Management
    MANAGE_PAYMENTS = 'manage:payments'
    VIEW_PAYMENTS = 'view:payments'
    
    # Wedding Planning
    PLAN_WEDDING = 'plan:wedding'
    VIEW_WEDDING = 'view:wedding'


class Auth0Roles:
    """Auth0 role constants - these should match your Auth0 setup"""
    
    BRIDE = 'Bride'
    GROOM = 'Groom'
    WEDDING_PLANNER = 'Wedding Planner'
    EVENT_ORGANIZER = 'Event Organizer'
    VENDOR_REPRESENTATIVE = 'Vendor Representative'  # Person who works for a vendor business
    GUEST = 'Guest'
    ADMIN = 'Admin'
    
    # Vendor-specific roles (should be scoped to vendor organizations in Auth0)
    VENDOR_OWNER = 'Vendor Owner'
    VENDOR_MANAGER = 'Vendor Manager'
    VENDOR_EMPLOYEE = 'Vendor Employee'


class Auth0VendorRoles:
    """Vendor-specific Auth0 roles that should be organization-scoped"""
    
    OWNER = 'Vendor Owner'
    MANAGER = 'Vendor Manager'
    EMPLOYEE = 'Vendor Employee'
    REPRESENTATIVE = 'Vendor Representative'


class Auth0PermissionChecker:
    """Utility class for checking Auth0 permissions"""
    
    @staticmethod
    def has_permission(user, permission: str) -> bool:
        """Check if user has a specific Auth0 permission"""
        if not user.is_authenticated or not user.auth0_permissions:
            return False
        
        return permission in user.auth0_permissions
    
    @staticmethod
    def has_role(user, role: str) -> bool:
        """Check if user has a specific Auth0 role"""
        if not user.is_authenticated or not user.auth0_roles:
            return False
        
        return role in user.auth0_roles
    
    @staticmethod
    def has_any_permission(user, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions"""
        if not user.is_authenticated or not user.auth0_permissions:
            return False
        
        return any(perm in user.auth0_permissions for perm in permissions)
    
    @staticmethod
    def has_all_permissions(user, permissions: List[str]) -> bool:
        """Check if user has all of the specified permissions"""
        if not user.is_authenticated or not user.auth0_permissions:
            return False
        
        return all(perm in user.auth0_permissions for perm in permissions)


class Auth0VendorPermissionChecker:
    """Utility class for checking vendor-specific Auth0 permissions"""
    
    @staticmethod
    def has_vendor_permission(user, vendor, permission: str) -> bool:
        """Check if user has permission for a specific vendor (future: use Auth0 Organizations)"""
        if not user.is_authenticated:
            return False
        
        # For now, check if user is associated with the vendor and has the permission
        # In future, this should check Auth0 Organizations and scoped permissions
        try:
            vendor_user = user.managed_vendors.get(vendor=vendor, is_active=True)
            vendor_permissions = vendor_user.get_vendor_permissions()
            return permission in vendor_permissions
        except:
            return False
    
    @staticmethod 
    def has_vendor_role(user, vendor, role: str) -> bool:
        """Check if user has a specific role for a vendor"""
        if not user.is_authenticated:
            return False
        
        try:
            vendor_user = user.managed_vendors.get(vendor=vendor, is_active=True)
            return vendor_user.role == role
        except:
            return False
    
    @staticmethod
    def get_vendor_permissions(user, vendor) -> List[str]:
        """Get all permissions user has for a specific vendor"""
        if not user.is_authenticated:
            return []
        
        try:
            vendor_user = user.managed_vendors.get(vendor=vendor, is_active=True)
            return vendor_user.get_vendor_permissions()
        except:
            return []


class Auth0UserSync:
    """Handles syncing user roles and permissions from Auth0"""
    
    def __init__(self):
        self.domain = settings.AUTH0_DOMAIN
        self.client_id = settings.AUTH0_CLIENT_ID
        self.client_secret = settings.AUTH0_CLIENT_SECRET
        self._management_token = None
    
    def get_management_token(self) -> str:
        """Get Auth0 Management API token"""
        if self._management_token:
            return self._management_token
        
        url = f"https://{self.domain}/oauth/token"
        
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'audience': f'https://{self.domain}/api/v2/',
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            self._management_token = data['access_token']
            return self._management_token
            
        except requests.RequestException as e:
            logger.error(f"Failed to get Auth0 management token: {e}")
            raise
    
    def get_user_roles_and_permissions(self, auth0_user_id: str) -> Dict[str, Any]:
        """Get user's roles and permissions from Auth0"""
        token = self.get_management_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Get user roles
            roles_url = f"https://{self.domain}/api/v2/users/{auth0_user_id}/roles"
            roles_response = requests.get(roles_url, headers=headers)
            roles_response.raise_for_status()
            roles = [role['name'] for role in roles_response.json()]
            
            # Get user permissions
            permissions_url = f"https://{self.domain}/api/v2/users/{auth0_user_id}/permissions"
            perms_response = requests.get(permissions_url, headers=headers)
            perms_response.raise_for_status()
            permissions = [perm['permission_name'] for perm in perms_response.json()]
            
            return {
                'roles': roles,
                'permissions': permissions
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Auth0 roles/permissions for {auth0_user_id}: {e}")
            return {'roles': [], 'permissions': []}
    
    def sync_user_permissions(self, user) -> bool:
        """Sync user's Auth0 roles and permissions to local database"""
        if not user.auth0_user_id:
            logger.warning(f"Cannot sync permissions for user {user.email}: no Auth0 ID")
            return False
        
        try:
            auth0_data = self.get_user_roles_and_permissions(user.auth0_user_id)
            
            user.auth0_roles = auth0_data['roles']
            user.auth0_permissions = auth0_data['permissions']
            user.last_auth0_sync = timezone.now()
            user.save()
            
            logger.info(f"Synced Auth0 permissions for user {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync Auth0 permissions for user {user.email}: {e}")
            return False


# Convenience functions for common permission checks
def can_create_events(user) -> bool:
    """Check if user can create events"""
    return Auth0PermissionChecker.has_permission(user, Auth0Permissions.CREATE_EVENTS)

def can_manage_vendor_relationships(user) -> bool:
    """Check if user can manage vendor relationships (couples/planners)"""
    return Auth0PermissionChecker.has_permission(user, Auth0Permissions.MANAGE_VENDOR_RELATIONSHIPS)

def can_view_vendors(user) -> bool:
    """Check if user can view vendor listings"""
    return Auth0PermissionChecker.has_permission(user, Auth0Permissions.VIEW_VENDORS)

def can_inquire_vendors(user) -> bool:
    """Check if user can send inquiries to vendors"""
    return Auth0PermissionChecker.has_permission(user, Auth0Permissions.INQUIRE_VENDORS)

def can_manage_vendor_business(user) -> bool:
    """Check if user can manage vendor business (vendor representatives)"""
    return Auth0PermissionChecker.has_permission(user, Auth0Permissions.MANAGE_VENDOR_BUSINESS)

def can_respond_to_inquiries(user) -> bool:
    """Check if user can respond to vendor inquiries"""
    return Auth0PermissionChecker.has_permission(user, Auth0Permissions.RESPOND_TO_INQUIRIES)

def can_manage_guests(user) -> bool:
    """Check if user can manage guests"""
    return Auth0PermissionChecker.has_permission(user, Auth0Permissions.MANAGE_GUESTS)

def can_edit_schedules(user) -> bool:
    """Check if user can edit schedules"""
    return Auth0PermissionChecker.has_permission(user, Auth0Permissions.EDIT_SCHEDULES)

def can_access_analytics(user) -> bool:
    """Check if user can access analytics"""
    return Auth0PermissionChecker.has_permission(user, Auth0Permissions.ACCESS_ANALYTICS)

def can_manage_payments(user) -> bool:
    """Check if user can manage payments"""
    return Auth0PermissionChecker.has_permission(user, Auth0Permissions.MANAGE_PAYMENTS)

def is_bride_or_groom(user) -> bool:
    """Check if user is bride or groom"""
    return (Auth0PermissionChecker.has_role(user, Auth0Roles.BRIDE) or 
            Auth0PermissionChecker.has_role(user, Auth0Roles.GROOM))

def is_vendor_representative(user) -> bool:
    """Check if user is a vendor representative"""
    return Auth0PermissionChecker.has_role(user, Auth0Roles.VENDOR_REPRESENTATIVE)

def has_wedding_planning_access(user) -> bool:
    """Check if user has wedding planning access"""
    return Auth0PermissionChecker.has_permission(user, Auth0Permissions.PLAN_WEDDING)

# Vendor-specific permission functions
def can_edit_vendor_info(user, vendor) -> bool:
    """Check if user can edit vendor business information"""
    return Auth0VendorPermissionChecker.has_vendor_permission(user, vendor, Auth0Permissions.EDIT_VENDOR_INFO)

def can_manage_vendor_bookings(user, vendor) -> bool:
    """Check if user can manage bookings for vendor"""
    return Auth0VendorPermissionChecker.has_vendor_permission(user, vendor, Auth0Permissions.MANAGE_VENDOR_BOOKINGS)

def can_respond_vendor_inquiries(user, vendor) -> bool:
    """Check if user can respond to inquiries for vendor"""
    return Auth0VendorPermissionChecker.has_vendor_permission(user, vendor, Auth0Permissions.RESPOND_VENDOR_INQUIRIES)

def can_view_vendor_analytics(user, vendor) -> bool:
    """Check if user can view vendor analytics"""
    return Auth0VendorPermissionChecker.has_vendor_permission(user, vendor, Auth0Permissions.VIEW_VENDOR_ANALYTICS)

def can_manage_vendor_team(user, vendor) -> bool:
    """Check if user can manage vendor team members"""
    return Auth0VendorPermissionChecker.has_vendor_permission(user, vendor, Auth0Permissions.MANAGE_VENDOR_TEAM)

def is_vendor_owner(user, vendor) -> bool:
    """Check if user is owner of vendor"""
    return Auth0VendorPermissionChecker.has_vendor_role(user, vendor, 'owner')

def is_vendor_manager(user, vendor) -> bool:
    """Check if user is manager of vendor"""
    return Auth0VendorPermissionChecker.has_vendor_role(user, vendor, 'manager')

# Legacy support - update these to use new vendor permissions
def can_manage_vendors(user) -> bool:
    """Legacy function - use can_manage_vendor_relationships instead"""
    return can_manage_vendor_relationships(user)