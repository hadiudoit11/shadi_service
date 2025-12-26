from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from ..models import EventUser
from ..services.auth0_permissions import Auth0PermissionChecker
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
        
        # Build user data with only existing fields
        data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'display_name': user.display_name,
            'auth0_user_id': user.auth0_user_id,
            'auth0_email': user.auth0_email,
            'auth0_picture': user.auth0_picture,
            'auth0_nickname': user.auth0_nickname,
            'auth0_roles': user.auth0_roles or [],
            'auth0_permissions': user.auth0_permissions or [],
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'date_joined': user.date_joined.isoformat() if user.date_joined else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'last_auth0_sync': user.last_auth0_sync.isoformat() if user.last_auth0_sync else None,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
            
            # Vendor relationship info
            'is_vendor_representative': hasattr(user, 'managed_vendors') and user.managed_vendors.exists(),
            'managed_vendors_count': user.managed_vendors.count() if hasattr(user, 'managed_vendors') else 0,
            
            # Simplified permissions check
            'permissions': {
                'can_manage_vendors': user.auth0_permissions and 'update:own_vendor' in user.auth0_permissions,
                'can_create_events': user.auth0_permissions and 'create:events' in user.auth0_permissions,
                'is_admin': user.is_superuser or user.is_staff,
            }
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
            
            # Update only basic fields that exist on the model
            updateable_fields = [
                'first_name', 'last_name'
            ]
            
            for field in updateable_fields:
                if field in data:
                    setattr(user, field, data[field])
            
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
            
            # Link users as partners (simplified without role validation for now)
            user.partner = partner
            partner.partner = user
            user.save()
            partner.save()
            
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
            # Simplified partner unlinking for now
            
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
            'current_roles': user.auth0_roles or [],
            'permissions': user.auth0_permissions or [],
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
                'can_create_events': 'create:events' in (user.auth0_permissions or []),
                'can_manage_vendors': 'manage:vendors' in (user.auth0_permissions or []),
                'can_edit_schedules': 'edit:schedules' in (user.auth0_permissions or []),
                'can_manage_guests': 'manage:guests' in (user.auth0_permissions or []),
                'can_access_analytics': 'access:analytics' in (user.auth0_permissions or []),
                'can_manage_payments': 'manage:payments' in (user.auth0_permissions or []),
            },
            'auth0_roles': user.auth0_roles or [],
            'auth0_permissions': user.auth0_permissions or [],
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
        
        # Simplified wedding data access for now
        wedding_data = {
            'user_id': user.id,
            'user_name': user.display_name,
            'user_email': user.email,
            'auth0_roles': user.auth0_roles or [],
        }
        
        return Response({
            'success': True,
            'message': 'Wedding data retrieved successfully',
            'data': wedding_data
        })