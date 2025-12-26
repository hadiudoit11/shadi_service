from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


def require_auth0_permission(permission):
    """
    Decorator to check if user has specific Auth0 permission
    Usage: @require_auth0_permission('read:vendors')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            if not request.user.has_auth0_permission(permission):
                return JsonResponse({
                    'error': f'Permission denied. Required permission: {permission}'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_auth0_role(role):
    """
    Decorator to check if user has specific Auth0 role
    Usage: @require_auth0_role('vendor_admin')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            if not request.user.has_auth0_role(role):
                return JsonResponse({
                    'error': f'Access denied. Required role: {role}'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_auth0_role(roles):
    """
    Decorator to check if user has any of the specified Auth0 roles
    Usage: @require_any_auth0_role(['vendor_admin', 'super_admin'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            if not any(request.user.has_auth0_role(role) for role in roles):
                return JsonResponse({
                    'error': f'Access denied. Required roles: {", ".join(roles)}'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# DRF Permission Classes
from rest_framework.permissions import BasePermission

class HasAuth0Permission(BasePermission):
    """
    DRF Permission class for Auth0 permissions
    Usage: permission_classes = [HasAuth0Permission('read:vendors')]
    """
    def __init__(self, permission):
        self.permission = permission
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.has_auth0_permission(self.permission)


class HasAuth0Role(BasePermission):
    """
    DRF Permission class for Auth0 roles
    Usage: permission_classes = [HasAuth0Role('vendor_admin')]
    """
    def __init__(self, role):
        self.role = role
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.has_auth0_role(self.role)


class HasAnyAuth0Role(BasePermission):
    """
    DRF Permission class for multiple Auth0 roles
    Usage: permission_classes = [HasAnyAuth0Role(['vendor_admin', 'super_admin'])]
    """
    def __init__(self, roles):
        self.roles = roles
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return any(request.user.has_auth0_role(role) for role in self.roles)