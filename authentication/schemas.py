"""
OpenAPI Schema definitions for Shadi Wedding Service API
Provides comprehensive schema documentation for all models and API endpoints
"""

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.openapi import AutoSchema
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Vendor, VendorCategory, VendorUser, VendorAvailability, VendorInquiry,
    Service, Package, PackageService, ServiceAvailability
)

EventUser = get_user_model()

# ===== MODEL SERIALIZERS FOR SCHEMA =====

class EventUserSchema(serializers.ModelSerializer):
    """Schema for EventUser model"""
    display_name = serializers.CharField(read_only=True)
    all_roles = serializers.ListField(read_only=True)
    is_bride_or_groom = serializers.BooleanField(read_only=True)
    is_event_organizer = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = EventUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'display_name',
            'auth0_user_id', 'auth0_email', 'auth0_picture', 'auth0_nickname',
            'auth0_roles', 'auth0_permissions', 'last_auth0_sync',
            'all_roles', 'is_bride_or_groom', 'is_event_organizer',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'auth0_user_id']

class VendorCategorySchema(serializers.ModelSerializer):
    """Schema for VendorCategory model"""
    
    class Meta:
        model = VendorCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'is_active', 'created_at']

class VendorSchema(serializers.ModelSerializer):
    """Schema for Vendor model"""
    admin = EventUserSchema(read_only=True)
    category = VendorCategorySchema(read_only=True)
    price_range_display = serializers.CharField(read_only=True)
    location_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Vendor
        fields = [
            'id', 'business_name', 'business_email', 'business_phone', 'website',
            'admin', 'category', 'services_offered', 'address', 'city', 'state',
            'zip_code', 'service_radius_miles', 'description', 'years_in_business',
            'insurance_verified', 'license_number', 'price_range_min', 'price_range_max',
            'pricing_structure', 'booking_lead_time_days', 'max_events_per_day',
            'available_days', 'portfolio_images', 'testimonials', 'is_verified',
            'is_active', 'is_featured', 'created_at', 'updated_at',
            'price_range_display', 'location_display'
        ]

class VendorUserSchema(serializers.ModelSerializer):
    """Schema for VendorUser model"""
    vendor = VendorSchema(read_only=True)
    user = EventUserSchema(read_only=True)
    
    class Meta:
        model = VendorUser
        fields = ['id', 'vendor', 'user', 'role', 'is_active', 'created_at']

class ServiceSchema(serializers.ModelSerializer):
    """Schema for Service model"""
    vendor = VendorSchema(read_only=True)
    category = VendorCategorySchema(read_only=True)
    total_duration_minutes = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'vendor', 'name', 'description', 'category', 'service_type',
            'base_price', 'price_per_unit', 'minimum_order', 'maximum_order',
            'duration_value', 'duration_unit', 'setup_time', 'teardown_time',
            'max_concurrent_bookings', 'advance_booking_days', 'available_days_of_week',
            'blackout_dates', 'seasonal_availability', 'venue_requirements',
            'guest_count_min', 'guest_count_max', 'special_requirements',
            'images', 'videos', 'documents', 'tags', 'is_active', 'is_featured',
            'is_customizable', 'requires_consultation', 'created_at', 'updated_at',
            'total_duration_minutes'
        ]

class PackageSchema(serializers.ModelSerializer):
    """Schema for Package model"""
    vendor = VendorSchema(read_only=True)
    services_total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discounted_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    savings_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    savings_percentage = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Package
        fields = [
            'id', 'vendor', 'name', 'description', 'package_type', 'discount_type',
            'discount_value', 'minimum_spend', 'bundle_price', 'valid_from',
            'valid_until', 'max_bookings', 'current_bookings', 'minimum_guest_count',
            'maximum_guest_count', 'requires_all_services', 'images', 'featured_image',
            'is_active', 'is_featured', 'is_public', 'created_at', 'updated_at',
            'services_total_price', 'discounted_price', 'savings_amount', 'savings_percentage'
        ]

class VendorInquirySchema(serializers.ModelSerializer):
    """Schema for VendorInquiry model"""
    vendor = VendorSchema(read_only=True)
    submitted_by = EventUserSchema(read_only=True)
    
    class Meta:
        model = VendorInquiry
        fields = [
            'id', 'vendor', 'submitted_by', 'event_date', 'event_location',
            'guest_count', 'budget_range_high', 'budget_range_low', 'message',
            'package_requested', 'status', 'vendor_response', 'vendor_quote',
            'created_at'
        ]

# ===== API RESPONSE SCHEMAS =====

class PermissionsResponseSchema(serializers.Serializer):
    """Schema for permissions API response"""
    can_create_events = serializers.BooleanField()
    can_manage_vendors = serializers.BooleanField()
    can_edit_schedules = serializers.BooleanField()
    can_manage_guests = serializers.BooleanField()
    can_access_analytics = serializers.BooleanField()
    can_manage_payments = serializers.BooleanField()

class SubscriptionResponseSchema(serializers.Serializer):
    """Schema for subscription info in API responses"""
    tier = serializers.CharField()
    active = serializers.BooleanField()
    max_events = serializers.IntegerField()
    has_premium_access = serializers.BooleanField()

class WeddingPartnerResponseSchema(serializers.Serializer):
    """Schema for wedding partner in API responses"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField()
    auth0_picture = serializers.URLField(allow_null=True)

class UserProfileResponseSchema(serializers.Serializer):
    """Schema for user profile API response"""
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    display_name = serializers.CharField()
    primary_role = serializers.CharField()
    all_roles = serializers.ListField()
    auth0_picture = serializers.URLField(allow_null=True)
    organization = serializers.CharField(allow_null=True)
    phone_number = serializers.CharField(allow_null=True)
    wedding_date = serializers.DateField(allow_null=True)
    wedding_venue = serializers.CharField(allow_null=True)
    guest_count_estimate = serializers.IntegerField(allow_null=True)
    partner = WeddingPartnerResponseSchema(allow_null=True)
    subscription_tier = serializers.CharField()
    subscription_active = serializers.BooleanField()
    auth0_roles = serializers.ListField()
    auth0_permissions = serializers.ListField()
    permissions = PermissionsResponseSchema()
    last_auth0_sync = serializers.DateTimeField(allow_null=True)

class APIResponseSchema(serializers.Serializer):
    """Standard API response schema"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.DictField()

class APIErrorResponseSchema(serializers.Serializer):
    """Standard API error response schema"""
    success = serializers.BooleanField(default=False)
    message = serializers.CharField()
    errors = serializers.DictField(required=False)

# ===== OPENAPI DECORATORS FOR VIEWS =====

# User Profile API Schema
user_profile_get_schema = extend_schema(
    tags=['User Management'],
    summary='Get user profile',
    description='Retrieve authenticated user\'s profile information including Auth0 data, roles, and permissions',
    responses={
        200: OpenApiResponse(
            response=APIResponseSchema,
            description='User profile retrieved successfully',
            examples=[
                OpenApiExample(
                    'Successful Response',
                    value={
                        'success': True,
                        'message': 'Success',
                        'data': {
                            'id': 1,
                            'email': 'bride@example.com',
                            'display_name': 'Jane Smith',
                            'primary_role': 'bride',
                            'permissions': {
                                'can_create_events': True,
                                'can_manage_vendors': False
                            }
                        }
                    }
                )
            ]
        ),
        401: APIErrorResponseSchema,
        403: APIErrorResponseSchema,
    }
)

user_profile_patch_schema = extend_schema(
    tags=['User Management'],
    summary='Update user profile',
    description='Update authenticated user\'s profile information',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'},
                'organization': {'type': 'string'},
                'phone_number': {'type': 'string'},
                'wedding_venue': {'type': 'string'},
                'guest_count_estimate': {'type': 'integer'},
                'wedding_date': {'type': 'string', 'format': 'date'},
                'add_role': {'type': 'string'},
                'remove_role': {'type': 'string'},
            }
        }
    },
    responses={
        200: APIResponseSchema,
        400: APIErrorResponseSchema,
        401: APIErrorResponseSchema,
    }
)

# Wedding Partner API Schema
wedding_partner_post_schema = extend_schema(
    tags=['User Management'],
    summary='Link wedding partner',
    description='Link two users as wedding partners (bride/groom)',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'partner_email': {'type': 'string', 'format': 'email'}
            },
            'required': ['partner_email']
        }
    },
    responses={
        200: APIResponseSchema,
        400: APIErrorResponseSchema,
        404: APIErrorResponseSchema,
    }
)

wedding_partner_delete_schema = extend_schema(
    tags=['User Management'],
    summary='Unlink wedding partner',
    description='Remove wedding partner relationship',
    responses={
        200: APIResponseSchema,
        400: APIErrorResponseSchema,
        401: APIErrorResponseSchema,
    }
)

# Permissions API Schema
permissions_get_schema = extend_schema(
    tags=['Permissions'],
    summary='Get user permissions',
    description='Retrieve user\'s current Auth0 permissions and subscription info',
    responses={
        200: OpenApiResponse(
            response=APIResponseSchema,
            description='Permissions retrieved successfully'
        ),
        401: APIErrorResponseSchema,
    }
)

permissions_post_schema = extend_schema(
    tags=['Permissions'],
    summary='Refresh permissions',
    description='Refresh user permissions from Auth0',
    responses={
        200: APIResponseSchema,
        400: APIErrorResponseSchema,
        401: APIErrorResponseSchema,
    }
)

# Event Management API Schemas
event_creation_schema = extend_schema(
    tags=['Event Management'],
    summary='Create or manage events',
    description='Create new wedding events or manage existing ones',
    responses={
        200: APIResponseSchema,
        400: APIErrorResponseSchema,
        401: APIErrorResponseSchema,
        403: APIErrorResponseSchema,
    }
)

guest_management_schema = extend_schema(
    tags=['Event Management'],
    summary='Manage event guests',
    description='Add, update, or remove guests from wedding events',
    responses={
        200: APIResponseSchema,
        400: APIErrorResponseSchema,
        401: APIErrorResponseSchema,
        403: APIErrorResponseSchema,
    }
)

schedule_management_schema = extend_schema(
    tags=['Event Management'],
    summary='Manage event schedule',
    description='Create and update wedding event schedules',
    responses={
        200: APIResponseSchema,
        400: APIErrorResponseSchema,
        401: APIErrorResponseSchema,
        403: APIErrorResponseSchema,
    }
)

analytics_schema = extend_schema(
    tags=['Event Management'],
    summary='Get event analytics',
    description='Retrieve analytics and insights for wedding events',
    responses={
        200: APIResponseSchema,
        401: APIErrorResponseSchema,
        403: APIErrorResponseSchema,
    }
)

# Vendor Management API Schema
vendor_management_schema = extend_schema(
    tags=['Vendor Management'],
    summary='Manage vendor relationships',
    description='Manage relationships with vendors (for couples/planners)',
    responses={
        200: APIResponseSchema,
        400: APIErrorResponseSchema,
        401: APIErrorResponseSchema,
        403: APIErrorResponseSchema,
    }
)

# Role Management API Schema
role_management_get_schema = extend_schema(
    tags=['User Management'],
    summary='Get available roles',
    description='Retrieve available roles and user\'s current roles',
    responses={
        200: OpenApiResponse(
            response=APIResponseSchema,
            description='Roles retrieved successfully',
            examples=[
                OpenApiExample(
                    'Successful Response',
                    value={
                        'success': True,
                        'message': 'Success',
                        'data': {
                            'available_roles': [
                                {'value': 'bride', 'label': 'Bride'},
                                {'value': 'groom', 'label': 'Groom'},
                                {'value': 'organizer', 'label': 'Event Organizer'}
                            ],
                            'current_roles': ['bride'],
                            'primary_role': 'bride',
                            'role_permissions': {
                                'is_bride_or_groom': True,
                                'is_event_organizer': False,
                                'has_wedding_planning_access': True
                            }
                        }
                    }
                )
            ]
        ),
        401: APIErrorResponseSchema,
    }
)

# Wedding Data API Schema
wedding_data_get_schema = extend_schema(
    tags=['User Management'],
    summary='Get wedding data',
    description='Retrieve shared wedding data between partners (bride/groom only)',
    responses={
        200: APIResponseSchema,
        401: APIErrorResponseSchema,
        403: APIErrorResponseSchema,
    }
)