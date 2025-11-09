from django.http import JsonResponse
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema_view
from ..models import EventUser
from .auth_views import Auth0LoginRequiredMixin
from .auth0_mixins import (
    Auth0PermissionRequiredMixin,
    CanCreateEventsMixin,
    CanManageVendorsMixin,
    CanManageGuestsMixin,
    CanEditSchedulesMixin,
    CanAccessAnalyticsMixin,
    CanManagePaymentsMixin,
)
from ..auth0_permissions import Auth0PermissionChecker
from ..schemas import (
    user_profile_get_schema,
    user_profile_patch_schema,
    wedding_partner_post_schema,
    wedding_partner_delete_schema,
    permissions_get_schema,
    permissions_post_schema,
    role_management_get_schema,
    wedding_data_get_schema,
)
import json


class APIResponseMixin:
    """Mixin for consistent API responses"""
    
    def success_response(self, data=None, message="Success"):
        return JsonResponse({
            'success': True,
            'message': message,
            'data': data or {}
        })
    
    def error_response(self, message="Error", status=400, errors=None):
        response_data = {
            'success': False,
            'message': message,
        }
        if errors:
            response_data['errors'] = errors
        
        return JsonResponse(response_data, status=status)


@method_decorator(csrf_exempt, name='dispatch')
@extend_schema_view(
    get=user_profile_get_schema,
    patch=user_profile_patch_schema,
)
class UserProfileAPIView(Auth0LoginRequiredMixin, APIResponseMixin, View):
    """API endpoint for user profile management"""
    
    def get(self, request):
        """Get user profile data"""
        user = request.user
        
        # Sync Auth0 permissions if needed
        if user.needs_permission_sync():
            user.sync_auth0_permissions()
        
        partner = user.get_wedding_partner()
        
        data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'display_name': user.display_name,
            'primary_role': user.primary_role,
            'all_roles': user.all_roles,
            'auth0_picture': user.auth0_picture,
            'organization': user.organization,
            'phone_number': user.phone_number,
            'wedding_date': user.wedding_date.isoformat() if user.wedding_date else None,
            'wedding_venue': user.wedding_venue,
            'guest_count_estimate': user.guest_count_estimate,
            'partner': {
                'id': partner.id,
                'name': partner.display_name,
                'email': partner.email,
                'role': partner.primary_role
            } if partner else None,
            'subscription_tier': user.subscription_tier,
            'subscription_active': user.subscription_active,
            # Auth0-based permissions instead of hard-coded
            'auth0_roles': user.auth0_roles,
            'auth0_permissions': user.auth0_permissions,
            'permissions': {
                'can_create_events': Auth0PermissionChecker.has_permission(user, 'create:events'),
                'can_manage_vendors': Auth0PermissionChecker.has_permission(user, 'manage:vendors'),
                'can_edit_schedules': Auth0PermissionChecker.has_permission(user, 'edit:schedules'),
                'can_manage_guests': Auth0PermissionChecker.has_permission(user, 'manage:guests'),
                'can_access_analytics': Auth0PermissionChecker.has_permission(user, 'access:analytics'),
                'can_manage_payments': Auth0PermissionChecker.has_permission(user, 'manage:payments'),
            },
            'last_auth0_sync': user.last_auth0_sync.isoformat() if user.last_auth0_sync else None,
        }
        
        return self.success_response(data)
    
    def patch(self, request):
        """Update user profile"""
        try:
            data = json.loads(request.body)
            user = request.user
            
            # Update basic fields
            updateable_fields = [
                'first_name', 'last_name', 'organization', 
                'phone_number', 'wedding_venue', 'guest_count_estimate'
            ]
            
            for field in updateable_fields:
                if field in data:
                    setattr(user, field, data[field])
            
            # Handle wedding date
            if 'wedding_date' in data and data['wedding_date']:
                from datetime import datetime
                user.wedding_date = datetime.fromisoformat(data['wedding_date']).date()
            
            # Handle roles
            if 'add_role' in data:
                user.add_role(data['add_role'])
            
            if 'remove_role' in data:
                user.remove_role(data['remove_role'])
            
            user.full_clean()
            user.save()
            
            return self.success_response(message="Profile updated successfully")
            
        except json.JSONDecodeError:
            return self.error_response("Invalid JSON data")
        except ValidationError as e:
            return self.error_response("Validation error", errors=e.message_dict)
        except Exception as e:
            return self.error_response(f"Update failed: {str(e)}")


@method_decorator(csrf_exempt, name='dispatch')
@extend_schema_view(
    post=wedding_partner_post_schema,
    delete=wedding_partner_delete_schema,
)
class WeddingPartnerAPIView(Auth0LoginRequiredMixin, APIResponseMixin, View):
    """API endpoint for wedding partner management"""
    
    def post(self, request):
        """Link wedding partner"""
        try:
            data = json.loads(request.body)
            partner_email = data.get('partner_email')
            
            if not partner_email:
                return self.error_response("Partner email is required")
            
            try:
                partner = EventUser.objects.get(email=partner_email)
            except EventUser.DoesNotExist:
                return self.error_response("Partner not found")
            
            user = request.user
            
            if not (user.is_bride_or_groom and partner.is_bride_or_groom):
                return self.error_response("Both users must be bride or groom to link as partners")
            
            user.link_wedding_partner(partner)
            
            return self.success_response(
                data={'partner_name': partner.display_name},
                message="Wedding partner linked successfully"
            )
            
        except json.JSONDecodeError:
            return self.error_response("Invalid JSON data")
        except Exception as e:
            return self.error_response(f"Partner linking failed: {str(e)}")
    
    def delete(self, request):
        """Unlink wedding partner"""
        try:
            user = request.user
            partner = user.get_wedding_partner()
            
            if not partner:
                return self.error_response("No partner to unlink")
            
            # Unlink both sides
            user.partner = None
            partner.partner = None
            user.save()
            partner.save()
            
            return self.success_response(message="Wedding partner unlinked successfully")
            
        except Exception as e:
            return self.error_response(f"Partner unlinking failed: {str(e)}")


@extend_schema_view(
    get=role_management_get_schema,
)
class RoleManagementAPIView(Auth0LoginRequiredMixin, APIResponseMixin, View):
    """API endpoint for role management"""
    
    def get(self, request):
        """Get available roles and user's current roles"""
        user = request.user
        
        data = {
            'available_roles': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in EventUser.EVENT_ROLE_CHOICES
            ],
            'current_roles': user.all_roles,
            'primary_role': user.primary_role,
            'role_permissions': {
                'is_bride_or_groom': user.is_bride_or_groom,
                'is_event_organizer': user.is_event_organizer,
                'has_wedding_planning_access': user.has_wedding_planning_access,
            }
        }
        
        return self.success_response(data)


@extend_schema_view(
    get=permissions_get_schema,
    post=permissions_post_schema,
)
class PermissionsAPIView(Auth0LoginRequiredMixin, APIResponseMixin, View):
    """API endpoint for user permissions"""
    
    def get(self, request):
        """Get user's current permissions"""
        user = request.user
        
        data = {
            'permissions': {
                'can_create_events': Auth0PermissionChecker.has_permission(user, 'create:events'),
                'can_manage_vendors': Auth0PermissionChecker.has_permission(user, 'manage:vendors'),
                'can_edit_schedules': Auth0PermissionChecker.has_permission(user, 'edit:schedules'),
                'can_manage_guests': Auth0PermissionChecker.has_permission(user, 'manage:guests'),
                'can_access_analytics': Auth0PermissionChecker.has_permission(user, 'access:analytics'),
                'can_manage_payments': Auth0PermissionChecker.has_permission(user, 'manage:payments'),
            },
            'subscription': {
                'tier': user.subscription_tier,
                'active': user.subscription_active,
                'max_events': user.max_events_allowed,
                'has_premium_access': user.has_premium_access,
            }
        }
        
        return self.success_response(data)
    
    def post(self, request):
        """Refresh permissions from Auth0"""
        try:
            user = request.user
            user.sync_auth0_permissions()
            
            return self.success_response(message="Permissions refreshed successfully")
            
        except Exception as e:
            return self.error_response(f"Permission refresh failed: {str(e)}")


@extend_schema_view(
    get=wedding_data_get_schema,
)
class WeddingDataAPIView(Auth0LoginRequiredMixin, APIResponseMixin, View):
    """API endpoint for wedding-specific data"""
    
    def get(self, request):
        """Get shared wedding data"""
        user = request.user
        
        if not user.is_bride_or_groom:
            return self.error_response("Only bride/groom can access wedding data", status=403)
        
        wedding_data = user.get_shared_wedding_data()
        
        # Convert date to string for JSON serialization
        if wedding_data['wedding_date']:
            wedding_data['wedding_date'] = wedding_data['wedding_date'].isoformat()
        
        # Convert partner to dict
        if wedding_data['partner']:
            partner = wedding_data['partner']
            wedding_data['partner'] = {
                'id': partner.id,
                'name': partner.display_name,
                'email': partner.email,
                'role': partner.primary_role,
                'auth0_picture': partner.auth0_picture,
            }
        
        return self.success_response(wedding_data)