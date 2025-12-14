from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    EventUser, Vendor, VendorCategory, VendorUser, VendorAvailability, 
    VendorInquiry, VendorImage, Service, Package, PackageService, ServiceAvailability
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


class VendorImageInline(admin.TabularInline):
    """Inline admin for vendor images"""
    model = VendorImage
    extra = 1
    fields = (
        'image_type', 'image_file', 'title', 'display_locations', 
        'is_primary', 'is_active', 'order', 'image_preview'
    )
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;" />',
                obj.image_url
            )
        return "No image"
    image_preview.short_description = 'Preview'


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    """Enhanced admin for vendors with rich display"""
    
    list_display = [
        'business_name', 'category', 'city_state', 'price_range_display',
        'is_active', 'is_featured', 'is_verified', 'image_count', 'created_at'
    ]
    
    list_filter = [
        'category', 'is_active', 'is_featured', 'is_verified', 
        'pricing_structure', 'state', 'created_at'
    ]
    
    search_fields = [
        'business_name', 'business_email', 'city', 'state', 'description'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'price_range_display', 'image_gallery']
    
    filter_horizontal = []
    
    inlines = [VendorImageInline]
    
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
    
    def image_count(self, obj):
        count = obj.images.count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                count
            )
        return format_html(
            '<span style="color: red;">0</span>'
        )
    image_count.short_description = 'Images'
    
    def image_gallery(self, obj):
        images = obj.images.filter(is_active=True).order_by('image_type', 'order')[:10]
        if images:
            html = '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
            for img in images:
                if img.image_url:
                    html += format_html(
                        '<div style="text-align: center;">'
                        '<img src="{}" width="150" height="150" style="object-fit: cover; border: 1px solid #ddd;" />'
                        '<br><small>{}</small>'
                        '</div>',
                        img.image_url,
                        img.get_image_type_display()
                    )
            html += '</div>'
            return format_html(html)
        return "No images uploaded"
    image_gallery.short_description = 'Image Gallery'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'admin').prefetch_related('images')


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


@admin.register(VendorImage)
class VendorImageAdmin(admin.ModelAdmin):
    """Standalone admin for managing all vendor images"""
    
    list_display = [
        'image_thumbnail', 'vendor', 'image_type', 'title',
        'display_locations_list', 'is_primary', 'is_active', 
        'order', 'uploaded_at'
    ]
    
    list_filter = [
        'image_type', 'is_primary', 'is_active',
        ('vendor', admin.RelatedOnlyFieldListFilter),
        'display_locations', 'uploaded_at'
    ]
    
    search_fields = [
        'vendor__business_name', 'title', 'description', 
        'tags', 'alt_text'
    ]
    
    readonly_fields = [
        'image_preview_large', 'image_url', 'uploaded_at', 
        'updated_at', 'metadata'
    ]
    
    list_editable = ['is_primary', 'is_active', 'order']
    list_per_page = 50
    
    fieldsets = (
        ('Vendor & Classification', {
            'fields': ('vendor', 'image_type', 'title')
        }),
        ('Image Upload', {
            'fields': ('image_file', 'image_url', 'image_preview_large'),
            'description': 'Upload an image file or provide a URL'
        }),
        ('Display Settings', {
            'fields': (
                'display_locations', 'is_primary', 'is_active', 
                'order', 'alt_text'
            )
        }),
        ('Additional Information', {
            'fields': ('description', 'tags', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def image_thumbnail(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" width="60" height="60" style="object-fit: cover; border-radius: 4px;" />',
                obj.image_url
            )
        return "No image"
    image_thumbnail.short_description = 'Thumbnail'
    
    def image_preview_large(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" style="max-width: 500px; max-height: 500px; object-fit: contain;" />',
                obj.image_url
            )
        return "No image uploaded"
    image_preview_large.short_description = 'Preview'
    
    def display_locations_list(self, obj):
        if obj.display_locations:
            return ', '.join(obj.display_locations)
        return '-'
    display_locations_list.short_description = 'Display Locations'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('vendor')
    
    actions = ['activate_images', 'deactivate_images', 'set_as_primary']
    
    def activate_images(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} images activated.')
    activate_images.short_description = 'Activate selected images'
    
    def deactivate_images(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} images deactivated.')
    deactivate_images.short_description = 'Deactivate selected images'
    
    def set_as_primary(self, request, queryset):
        for image in queryset:
            image.is_primary = True
            image.save()
        self.message_user(request, f'{queryset.count()} images set as primary.')
    set_as_primary.short_description = 'Set as primary for their type'


# Customize admin site header and title
admin.site.site_header = "Shadi Wedding Service Admin"
admin.site.site_title = "Shadi Admin"
admin.site.index_title = "Wedding Service Management"
