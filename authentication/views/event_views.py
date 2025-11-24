from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from ..models import EventUser
from ..auth0_permissions import (
    can_create_events,
    can_manage_vendors,
    can_manage_guests,
    can_edit_schedules,
    can_access_analytics,
)
from datetime import date
import json


class EventCreationAPIView(APIView):
    """API endpoint for event creation and management"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get event creation status",
        description="Retrieve user's event creation capabilities and limits",
        responses={
            200: OpenApiResponse(description="Event creation status retrieved"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=['Event Management']
    )
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
        
        return Response({
            'success': True,
            'message': 'Event creation status retrieved',
            'data': data
        })
    
    @extend_schema(
        summary="Validate event creation",
        description="Validate event creation request and check permissions",
        responses={
            200: OpenApiResponse(description="Event validation passed"),
            400: OpenApiResponse(description="Validation failed"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Permission denied"),
        },
        tags=['Event Management']
    )
    def post(self, request):
        """Validate event creation request"""
        try:
            data = request.data
            user = request.user
            
            # Check Auth0 permissions
            if not can_create_events(user):
                return Response({
                    'success': False,
                    'message': "You don't have permission to create events"
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Validate required fields for bride/groom
            if user.is_bride_or_groom:
                if not user.wedding_date:
                    return Response({
                        'success': False,
                        'message': "Wedding date is required before creating events"
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if not user.get_wedding_partner():
                    return Response({
                        'success': False,
                        'message': "Wedding partner must be linked before creating events"
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # This would integrate with your events app
            # For now, just return success with validation
            event_data = {
                'event_type': data.get('event_type', 'wedding'),
                'organizer': user.display_name,
                'organizer_role': user.primary_role,
                'permissions_validated': True,
            }
            
            return Response({
                'success': True,
                'message': 'Event creation validation passed',
                'data': event_data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Validation failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class VendorManagementAPIView(APIView):
    """API endpoint for vendor management - requires manage:vendors permission"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get vendor management capabilities",
        description="Retrieve vendor management permissions and capabilities",
        responses={
            200: OpenApiResponse(description="Vendor management info retrieved"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=['Vendor Management']
    )
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
        
        return Response({
            'success': True,
            'message': 'Vendor management info retrieved',
            'data': data
        })


class GuestManagementAPIView(APIView):
    """API endpoint for guest management"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get guest management capabilities",
        description="Retrieve guest management permissions and settings",
        responses={
            200: OpenApiResponse(description="Guest management info retrieved"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=['Guest Management']
    )
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
        
        return Response({
            'success': True,
            'message': 'Guest management info retrieved',
            'data': data
        })


class ScheduleManagementAPIView(APIView):
    """API endpoint for schedule/timeline management"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get schedule management capabilities",
        description="Retrieve schedule management permissions and timeline templates",
        responses={
            200: OpenApiResponse(description="Schedule management info retrieved"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=['Schedule Management']
    )
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
        
        return Response({
            'success': True,
            'message': 'Schedule management info retrieved',
            'data': data
        })


class AnalyticsAPIView(APIView):
    """API endpoint for wedding analytics and insights"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get wedding analytics",
        description="Retrieve wedding analytics and insights (premium feature)",
        responses={
            200: OpenApiResponse(description="Analytics retrieved successfully"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Analytics access denied"),
        },
        tags=['Analytics']
    )
    def get(self, request):
        """Get analytics capabilities and basic stats"""
        user = request.user
        
        if not user.can_access_analytics:
            return Response({
                'success': False,
                'message': "You don't have permission to access analytics"
            }, status=status.HTTP_403_FORBIDDEN)
        
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
            days_until = (user.wedding_date - date.today()).days
            data['wedding_overview']['days_until_wedding'] = max(0, days_until)
        
        return Response({
            'success': True,
            'message': 'Analytics retrieved successfully',
            'data': data
        })