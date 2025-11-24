from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from ..models import EventUser
from ..auth0_permissions import Auth0PermissionChecker
from ..schemas import (
    EventUserSchema,
    VendorSchema,
    ServiceSchema,
)
from datetime import datetime
import json


class UserProfileAPIView(APIView):
    """API endpoint for user profile management"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get user profile",
        description="Retrieve current user's profile data including roles, permissions, and wedding details",
        responses={
            200: EventUserSchema,
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=['User Management']
    )
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
        
        return Response({
            'success': True,
            'message': 'Profile retrieved successfully',
            'data': data
        })
    
    @extend_schema(
        summary="Update user profile",
        description="Update user profile information including personal details and wedding information",
        request=EventUserSchema,
        responses={
            200: OpenApiResponse(description="Profile updated successfully"),
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=['User Management']
    )
    def patch(self, request):
        """Update user profile"""
        try:
            data = request.data
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
                user.wedding_date = datetime.fromisoformat(data['wedding_date']).date()
            
            # Handle roles
            if 'add_role' in data:
                user.add_role(data['add_role'])
            
            if 'remove_role' in data:
                user.remove_role(data['remove_role'])
            
            user.full_clean()
            user.save()
            
            return Response({
                'success': True,
                'message': 'Profile updated successfully'
            })
            
        except ValidationError as e:
            return Response({
                'success': False,
                'message': 'Validation error',
                'errors': e.message_dict
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Update failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class WeddingPartnerAPIView(APIView):
    """API endpoint for wedding partner management"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Link wedding partner",
        description="Link current user with their wedding partner",
        request=None,
        responses={
            200: OpenApiResponse(description="Partner linked successfully"),
            400: OpenApiResponse(description="Invalid data or linking error"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=['User Management']
    )
    def post(self, request):
        """Link wedding partner"""
        try:
            data = request.data
            partner_email = data.get('partner_email')
            
            if not partner_email:
                return Response({
                    'success': False,
                    'message': 'Partner email is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                partner = EventUser.objects.get(email=partner_email)
            except EventUser.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Partner not found'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = request.user
            
            if not (user.is_bride_or_groom and partner.is_bride_or_groom):
                return Response({
                    'success': False,
                    'message': 'Both users must be bride or groom to link as partners'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user.link_wedding_partner(partner)
            
            return Response({
                'success': True,
                'message': 'Wedding partner linked successfully',
                'data': {'partner_name': partner.display_name}
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Partner linking failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Unlink wedding partner",
        description="Remove link between current user and their wedding partner",
        responses={
            200: OpenApiResponse(description="Partner unlinked successfully"),
            400: OpenApiResponse(description="No partner to unlink"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=['User Management']
    )
    def delete(self, request):
        """Unlink wedding partner"""
        try:
            user = request.user
            partner = user.get_wedding_partner()
            
            if not partner:
                return Response({
                    'success': False,
                    'message': 'No partner to unlink'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Unlink both sides
            user.partner = None
            partner.partner = None
            user.save()
            partner.save()
            
            return Response({
                'success': True,
                'message': 'Wedding partner unlinked successfully'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Partner unlinking failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class RoleManagementAPIView(APIView):
    """API endpoint for role management"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get user roles",
        description="Retrieve available roles and user's current role assignments",
        responses={
            200: EventUserSchema,
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=['User Management']
    )
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
        
        return Response({
            'success': True,
            'message': 'Roles retrieved successfully',
            'data': data
        })


class PermissionsAPIView(APIView):
    """API endpoint for user permissions"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get user permissions",
        description="Retrieve user's current Auth0 permissions and subscription details",
        responses={
            200: EventUserSchema,
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=['Permissions']
    )
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
        
        return Response({
            'success': True,
            'message': 'Permissions retrieved successfully',
            'data': data
        })
    
    @extend_schema(
        summary="Refresh Auth0 permissions",
        description="Sync user permissions from Auth0",
        responses={
            200: OpenApiResponse(description="Permissions refreshed successfully"),
            400: OpenApiResponse(description="Refresh failed"),
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=['Permissions']
    )
    def post(self, request):
        """Refresh permissions from Auth0"""
        try:
            user = request.user
            user.sync_auth0_permissions()
            
            return Response({
                'success': True,
                'message': 'Permissions refreshed successfully'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Permission refresh failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class WeddingDataAPIView(APIView):
    """API endpoint for wedding-specific data"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get wedding data",
        description="Retrieve shared wedding information (bride/groom only)",
        responses={
            200: EventUserSchema,
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Only bride/groom can access wedding data"),
        },
        tags=['User Management']
    )
    def get(self, request):
        """Get shared wedding data"""
        user = request.user
        
        if not user.is_bride_or_groom:
            return Response({
                'success': False,
                'message': 'Only bride/groom can access wedding data'
            }, status=status.HTTP_403_FORBIDDEN)
        
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
        
        return Response({
            'success': True,
            'message': 'Wedding data retrieved successfully',
            'data': wedding_data
        })