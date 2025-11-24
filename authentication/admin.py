from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    EventUser, Vendor, VendorCategory, VendorUser, VendorAvailability, 
    VendorInquiry, Service, Package, PackageService, ServiceAvailability
)


@admin.register(EventUser)
class EventUserAdmin(UserAdmin):
    """Enhanced admin for EventUser with Auth0 fields"""
    
    # Display fields in list view  
    list_display = [
        'email', 'display_name', 'primary_role', 'is_active', 
        'is_staff', 'date_joined'
    ]
    
    list_filter = [
        'is_active', 'is_staff', 'last_auth0_sync'
    ]
    
    search_fields = ['email', 'first_name', 'last_name', 'auth0_user_id']
    
    readonly_fields = [
        'auth0_user_id', 'auth0_email', 'auth0_picture', 'auth0_nickname',
        'last_auth0_sync', 'date_joined', 'last_login'
    ]
    
    # Organize fieldsets
    fieldsets = UserAdmin.fieldsets + (
        ('Auth0 Integration', {
            'fields': (
                'auth0_user_id', 'auth0_email', 'auth0_picture', 'auth0_nickname',
                'auth0_roles', 'auth0_permissions', 'last_auth0_sync'
            )
        }),
        ('Wedding Information', {
            'fields': (
                'roles', 'partner', 'wedding_date', 'wedding_venue', 
                'guest_count_estimate'
            )
        }),
        ('Contact Information', {
            'fields': ('organization', 'phone_number')
        })
    )
    
    def display_name(self, obj):
        return obj.display_name
    display_name.short_description = 'Display Name'
    
    def primary_role(self, obj):
        return obj.primary_role
    primary_role.short_description = 'Primary Role'


@admin.register(VendorCategory)
class VendorCategoryAdmin(admin.ModelAdmin):
    """Admin for vendor categories"""
    
    list_display = ['name', 'slug', 'vendor_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']
    
    def vendor_count(self, obj):
        return obj.vendors.count()
    vendor_count.short_description = 'Total Vendors'


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    """Enhanced admin for vendors with rich display"""
    
    list_display = [
        'business_name', 'category', 'city_state', 'price_range_display',
        'is_active', 'is_featured', 'is_verified', 'created_at'
    ]
    
    list_filter = [
        'category', 'is_active', 'is_featured', 'is_verified', 
        'pricing_structure', 'state', 'created_at'
    ]
    
    search_fields = [
        'business_name', 'business_email', 'city', 'state', 'description'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'price_range_display']
    
    filter_horizontal = []
    
    fieldsets = (
        ('Business Information', {
            'fields': (
                'business_name', 'business_email', 'business_phone', 
                'website', 'admin', 'category'
            )
        }),
        ('Services', {
            'fields': ('services_offered', 'description')
        }),
        ('Location', {
            'fields': (
                'address', 'city', 'state', 'zip_code', 'service_radius_miles'
            )
        }),
        ('Pricing', {
            'fields': (
                'price_range_min', 'price_range_max', 'pricing_structure',
                'price_range_display'
            )
        }),
        ('Business Details', {
            'fields': (
                'years_in_business', 'insurance_verified', 'license_number'
            )
        }),
        ('Availability', {
            'fields': (
                'booking_lead_time_days', 'max_events_per_day', 'available_days'
            )
        }),
        ('Marketing', {
            'fields': (
                'portfolio_images', 'testimonials'
            )
        }),
        ('Status', {
            'fields': ('is_verified', 'is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def city_state(self, obj):
        return obj.location_display
    city_state.short_description = 'Location'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'admin')


@admin.register(VendorUser)
class VendorUserAdmin(admin.ModelAdmin):
    """Admin for vendor-user relationships"""
    
    list_display = ['vendor', 'user', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['vendor__business_name', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at']


@admin.register(VendorAvailability)
class VendorAvailabilityAdmin(admin.ModelAdmin):
    """Admin for vendor availability"""
    
    list_display = ['vendor', 'date', 'is_available']
    list_filter = ['is_available', 'date', 'vendor__category']
    search_fields = ['vendor__business_name']
    date_hierarchy = 'date'


@admin.register(VendorInquiry)
class VendorInquiryAdmin(admin.ModelAdmin):
    """Admin for vendor inquiries with status tracking"""
    
    list_display = [
        'vendor', 'submitted_by', 'event_date', 'status', 
        'budget_range', 'created_at', 'responded_at'
    ]
    
    list_filter = [
        'status', 'event_date', 'created_at', 'responded_at',
        'vendor__category'
    ]
    
    search_fields = [
        'vendor__business_name', 'submitted_by__email', 
        'event_location', 'message'
    ]
    
    readonly_fields = ['created_at']
    date_hierarchy = 'event_date'
    
    fieldsets = (
        ('Inquiry Information', {
            'fields': ('vendor', 'submitted_by', 'status')
        }),
        ('Event Details', {
            'fields': (
                'event_date', 'event_location', 'guest_count',
                'budget_range_low', 'budget_range_high'
            )
        }),
        ('Message & Requirements', {
            'fields': ('message', 'package_requested')
        }),
        ('Vendor Response', {
            'fields': ('vendor_response', 'vendor_quote', 'responded_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def budget_range(self, obj):
        if obj.budget_range_low and obj.budget_range_high:
            return f"${obj.budget_range_low:,} - ${obj.budget_range_high:,}"
        elif obj.budget_range_low:
            return f"${obj.budget_range_low:,}+"
        return "Not specified"
    budget_range.short_description = 'Budget Range'


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin for vendor services"""
    
    list_display = [
        'name', 'vendor', 'category', 'base_price', 'is_active'
    ]
    
    list_filter = [
        'category', 'is_active', 'vendor__category', 'created_at'
    ]
    
    search_fields = ['name', 'vendor__business_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Service Information', {
            'fields': ('vendor', 'name', 'description', 'category')
        }),
        ('Pricing & Duration', {
            'fields': ('base_price', 'duration_hours')
        }),
        ('Booking Settings', {
            'fields': ('max_bookings_per_day', 'requires_deposit')
        }),
        ('Requirements & Add-ons', {
            'fields': ('requirements', 'add_ons_available')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    """Admin for vendor packages"""
    
    list_display = [
        'name', 'vendor', 'service_count', 'is_active', 'created_at'
    ]
    
    list_filter = ['is_active', 'vendor__category', 'created_at']
    search_fields = ['name', 'vendor__business_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def service_count(self, obj):
        return obj.packageservice_set.count()
    service_count.short_description = 'Services'


@admin.register(PackageService)
class PackageServiceAdmin(admin.ModelAdmin):
    """Admin for package-service relationships"""
    
    list_display = ['package', 'service', 'quantity', 'custom_price']
    list_filter = ['package__vendor', 'service__category']
    search_fields = ['package__name', 'service__name']


@admin.register(ServiceAvailability)
class ServiceAvailabilityAdmin(admin.ModelAdmin):
    """Admin for service availability"""
    
    list_display = [
        'service', 'date', 'is_available'
    ]
    
    list_filter = ['date', 'service__vendor']
    search_fields = ['service__name', 'service__vendor__business_name']
    date_hierarchy = 'date'


# Customize admin site header and title
admin.site.site_header = "Shadi Wedding Service Admin"
admin.site.site_title = "Shadi Admin"
admin.site.index_title = "Wedding Service Management"
