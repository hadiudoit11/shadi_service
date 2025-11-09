from django.http import JsonResponse
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema_view
from ..models import EventUser
from .auth_views import Auth0LoginRequiredMixin
from .api_views import APIResponseMixin
from .auth0_mixins import (
    CanCreateEventsMixin, 
    CanManageVendorsMixin, 
    CanManageGuestsMixin,
    CanEditSchedulesMixin,
    CanAccessAnalyticsMixin,
)
from ..auth0_permissions import (
    can_create_events,
    can_manage_vendors,
    can_manage_guests,
    can_edit_schedules,
    can_access_analytics,
)
from ..schemas import (
    event_creation_schema,
    guest_management_schema,
    schedule_management_schema,
    analytics_schema,
    vendor_management_schema,
)
import json


@method_decorator(csrf_exempt, name='dispatch')
@extend_schema_view(
    get=event_creation_schema,
    post=event_creation_schema,
)
class EventCreationAPIView(Auth0LoginRequiredMixin, APIResponseMixin, View):
    """API endpoint for event creation and management"""
    
    def get(self, request):
        """Get user's event creation status and limits"""
        user = request.user
        
        # Sync Auth0 permissions if needed
        if user.needs_permission_sync():
            user.sync_auth0_permissions()
        
        data = {
            'can_create_events': can_create_events(user),
            'max_events_allowed': user.max_events_allowed,
            'subscription_tier': user.subscription_tier,
            'has_premium_access': user.has_premium_access,
            'event_creation_settings': {
                'requires_wedding_date': user.is_bride_or_groom,
                'requires_partner': user.is_bride_or_groom,
                'can_create_unlimited': user.can_create_unlimited_events,
            }
        }
        
        return self.success_response(data)
    
    def post(self, request):
        """Validate event creation request"""
        try:
            data = json.loads(request.body)
            user = request.user
            
            # Check Auth0 permissions
            if not can_create_events(user):
                return self.error_response(
                    "You don't have permission to create events", 
                    status=403
                )
            
            # Validate required fields for bride/groom
            if user.is_bride_or_groom:
                if not user.wedding_date:
                    return self.error_response(
                        "Wedding date is required before creating events"
                    )
                
                if not user.get_wedding_partner():
                    return self.error_response(
                        "Wedding partner must be linked before creating events"
                    )
            
            # This would integrate with your events app
            # For now, just return success with validation
            event_data = {
                'event_type': data.get('event_type', 'wedding'),
                'organizer': user.display_name,
                'organizer_role': user.primary_role,
                'permissions_validated': True,
            }
            
            return self.success_response(
                data=event_data,
                message="Event creation validation passed"
            )
            
        except json.JSONDecodeError:
            return self.error_response("Invalid JSON data")
        except Exception as e:
            return self.error_response(f"Validation failed: {str(e)}")


@extend_schema_view(
    get=vendor_management_schema,
    post=vendor_management_schema,
    patch=vendor_management_schema,
)
class VendorManagementAPIView(CanManageVendorsMixin, Auth0LoginRequiredMixin, APIResponseMixin, View):
    """API endpoint for vendor management - requires manage:vendors permission"""
    
    def get(self, request):
        """Get vendor management capabilities"""
        user = request.user
        
        data = {
            'can_manage_vendors': can_manage_vendors(user),
            'is_vendor': user.has_role(EventUser.VENDOR),
            'vendor_permissions': {
                'can_view_vendor_list': can_manage_vendors(user),
                'can_add_vendors': can_manage_vendors(user),
                'can_remove_vendors': can_manage_vendors(user),
                'can_communicate_with_vendors': can_manage_vendors(user),
            },
            'vendor_categories': [
                'photographer', 'videographer', 'florist', 'caterer',
                'dj', 'band', 'venue', 'decorator', 'baker', 'other'
            ]
        }
        
        return self.success_response(data)


@extend_schema_view(
    get=guest_management_schema,
    post=guest_management_schema,
    patch=guest_management_schema,
)
class GuestManagementAPIView(Auth0LoginRequiredMixin, APIResponseMixin, View):
    """API endpoint for guest management"""
    
    def get(self, request):
        """Get guest management capabilities"""
        user = request.user
        
        data = {
            'can_manage_attendees': user.can_manage_attendees,
            'guest_management_permissions': {
                'can_add_guests': user.can_manage_attendees,
                'can_remove_guests': user.can_manage_attendees,
                'can_send_invitations': user.can_manage_attendees or user.is_bride_or_groom,
                'can_track_rsvp': user.has_wedding_planning_access,
                'can_manage_seating': user.can_manage_attendees,
            },
            'guest_categories': [
                'family', 'friends', 'colleagues', 'plus_ones', 'vendors', 'wedding_party'
            ],
            'estimated_guest_count': user.guest_count_estimate,
        }
        
        return self.success_response(data)


@extend_schema_view(
    get=schedule_management_schema,
    post=schedule_management_schema,
    patch=schedule_management_schema,
)
class ScheduleManagementAPIView(Auth0LoginRequiredMixin, APIResponseMixin, View):
    """API endpoint for schedule/timeline management"""
    
    def get(self, request):
        """Get schedule management capabilities"""
        user = request.user
        
        data = {
            'can_edit_schedules': user.can_edit_schedules,
            'schedule_permissions': {
                'can_create_timeline': user.can_edit_schedules,
                'can_modify_timeline': user.can_edit_schedules,
                'can_view_timeline': user.has_wedding_planning_access or user.has_role(EventUser.VENDOR),
                'can_add_tasks': user.can_edit_schedules,
                'can_assign_tasks': user.can_manage_attendees,
            },
            'wedding_date': user.wedding_date.isoformat() if user.wedding_date else None,
            'timeline_templates': [
                'traditional_wedding', 'modern_wedding', 'destination_wedding', 
                'intimate_ceremony', 'outdoor_wedding', 'custom'
            ]
        }
        
        return self.success_response(data)


@extend_schema_view(
    get=analytics_schema,
)
class AnalyticsAPIView(Auth0LoginRequiredMixin, APIResponseMixin, View):
    """API endpoint for wedding analytics and insights"""
    
    def get(self, request):
        """Get analytics capabilities and basic stats"""
        user = request.user
        
        if not user.can_access_analytics:
            return self.error_response(
                "You don't have permission to access analytics", 
                status=403
            )
        
        # Mock analytics data - replace with real data from your events app
        partner = user.get_wedding_partner()
        
        data = {
            'analytics_permissions': {
                'can_view_budget_analytics': user.can_manage_payments,
                'can_view_guest_analytics': user.can_manage_attendees,
                'can_view_vendor_analytics': user.can_manage_vendors,
                'can_export_reports': user.has_premium_access,
            },
            'wedding_overview': {
                'days_until_wedding': None,  # Calculate based on wedding_date
                'total_guests_invited': 0,
                'rsvp_response_rate': 0,
                'budget_utilization': 0,
                'tasks_completed': 0,
                'vendors_confirmed': 0,
            },
            'couple_info': {
                'bride_name': user.display_name if user.has_role(EventUser.BRIDE) else partner.display_name if partner and partner.has_role(EventUser.BRIDE) else None,
                'groom_name': user.display_name if user.has_role(EventUser.GROOM) else partner.display_name if partner and partner.has_role(EventUser.GROOM) else None,
                'wedding_date': user.wedding_date.isoformat() if user.wedding_date else None,
                'wedding_venue': user.wedding_venue,
            }
        }
        
        # Calculate days until wedding
        if user.wedding_date:
            from datetime import date
            days_until = (user.wedding_date - date.today()).days
            data['wedding_overview']['days_until_wedding'] = max(0, days_until)
        
        return self.success_response(data)