from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from ..decorators import (
    require_auth0_permission, 
    require_auth0_role,
    require_any_auth0_role,
    HasAuth0Permission,
    HasAuth0Role,
    HasAnyAuth0Role
)
from ..models import Vendor


# Function-based view examples
@api_view(['GET'])
@require_auth0_permission('read:vendors')
def protected_vendors_list(request):
    """Only users with 'read:vendors' permission can access"""
    return JsonResponse({
        'message': 'You have permission to read vendors',
        'vendors': []  # Your vendor data here
    })


@api_view(['POST'])
@require_auth0_role('vendor_admin')
def create_vendor(request):
    """Only vendor_admin role can create vendors"""
    return JsonResponse({
        'message': 'Vendor created successfully',
        'user_roles': request.user.auth0_roles
    })


@api_view(['PUT'])
@require_any_auth0_role(['vendor_admin', 'super_admin'])
def update_vendor(request, vendor_id):
    """Vendor admin or super admin can update vendors"""
    return JsonResponse({
        'message': f'Vendor {vendor_id} updated',
        'user_roles': request.user.auth0_roles
    })


# Class-based view examples
class VendorManagementAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """GET - requires read:vendors permission"""
        if not request.user.has_auth0_permission('read:vendors'):
            return Response({
                'error': 'Permission denied. Required: read:vendors'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'message': 'Vendors list',
            'user_permissions': request.user.auth0_permissions
        })
    
    def post(self, request):
        """POST - requires vendor_admin role"""
        if not request.user.has_auth0_role('vendor_admin'):
            return Response({
                'error': 'Access denied. Required role: vendor_admin'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'message': 'Vendor created',
            'user_roles': request.user.auth0_roles
        })


class AdminOnlyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Only super_admin can access"""
        if not request.user.has_auth0_role('super_admin'):
            return Response({
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'message': 'Admin dashboard data',
            'user': {
                'email': request.user.email,
                'roles': request.user.auth0_roles,
                'permissions': request.user.auth0_permissions
            }
        })


class WeddingPlannerAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Wedding planners and couples can access"""
        allowed_roles = ['wedding_planner', 'bride_groom']
        
        if not any(request.user.has_auth0_role(role) for role in allowed_roles):
            return Response({
                'error': f'Access denied. Required roles: {", ".join(allowed_roles)}'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'message': 'Wedding planning data',
            'user_role': [role for role in allowed_roles if request.user.has_auth0_role(role)][0]
        })


# Helper view to check user permissions (useful for debugging)
class UserPermissionsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Debug endpoint to see user's Auth0 roles and permissions"""
        user = request.user
        
        return Response({
            'user': {
                'email': user.email,
                'display_name': user.display_name,
                'auth0_roles': user.auth0_roles or [],
                'auth0_permissions': user.auth0_permissions or [],
                'last_auth0_sync': user.last_auth0_sync,
            },
            'role_checks': {
                'is_bride_or_groom': user.is_bride_or_groom_auth0,
                'is_wedding_planner': user.is_wedding_planner_auth0,
                'is_vendor_admin': user.is_vendor_admin_auth0,
                'is_vendor_staff': user.is_vendor_staff_auth0,
                'is_super_admin': user.is_super_admin_auth0,
            },
            'permission_checks': {
                'can_read_vendors': user.has_auth0_permission('read:vendors'),
                'can_create_events': user.has_auth0_permission('create:events'),
                'can_update_vendor': user.has_auth0_permission('update:vendor'),
                'can_manage_payments': user.has_auth0_permission('manage:payments'),
                'can_access_admin': user.has_auth0_permission('access:admin'),
            }
        })