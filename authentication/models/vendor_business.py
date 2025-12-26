from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from .user_profile import EventUser
from .vendor_category import VendorCategory


class Vendor(models.Model):
    """Wedding vendors/service providers - separate from users"""
    
    # Business Information
    business_name = models.CharField(max_length=200, blank=True)
    business_email = models.EmailField(blank=True)
    business_phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    admin = models.ForeignKey(EventUser, on_delete=models.CASCADE, null=True, blank=True)
    
    # Service Information
    category = models.ForeignKey(VendorCategory, on_delete=models.CASCADE, related_name='vendors', null=True, blank=True)
    services_offered = models.JSONField(default=list, help_text="List of specific services")
    
    # Location
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    service_radius_miles = models.PositiveIntegerField(
        default=25, 
        validators=[MinValueValidator(1), MaxValueValidator(500)]
    )
    
    # Business Details
    description = models.TextField(blank=True)
    years_in_business = models.PositiveIntegerField(null=True, blank=True)
    insurance_verified = models.BooleanField(default=False)
    license_number = models.CharField(max_length=100, blank=True)
    
    # Pricing
    price_range_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_range_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pricing_structure = models.CharField(
        max_length=50,
        choices=[
            ('hourly', 'Hourly Rate'),
            ('package', 'Package Pricing'),
            ('per_guest', 'Per Guest'),
            ('flat_rate', 'Flat Rate'),
            ('custom', 'Custom Quote'),
        ],
        default='custom'
    )
    
    # Availability
    booking_lead_time_days = models.PositiveIntegerField(default=30)
    max_events_per_day = models.PositiveIntegerField(default=1)
    available_days = models.JSONField(
        default=list, 
        help_text="Days of week available (0=Monday, 6=Sunday)"
    )
    
    # Social Proof
    portfolio_images = models.JSONField(default=list, help_text="URLs to portfolio images")
    testimonials = models.JSONField(default=list, help_text="Customer testimonials")
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Vendor"
        verbose_name_plural = "Vendors"
        ordering = ['business_name']
        indexes = [
            models.Index(fields=['category', 'city']),
            models.Index(fields=['is_active', 'is_verified']),
        ]
    
    def __str__(self):
        return f"{self.business_name} ({self.category.name})"
    
    @property
    def price_range_display(self):
        """Display formatted price range"""
        if self.price_range_min and self.price_range_max:
            return f"${self.price_range_min:,.0f} - ${self.price_range_max:,.0f}"
        elif self.price_range_min:
            return f"Starting at ${self.price_range_min:,.0f}"
        return "Contact for pricing"
    
    @property
    def location_display(self):
        """Display formatted location"""
        parts = [self.city, self.state]
        return ", ".join(filter(None, parts))
    
    def clean(self):
        super().clean()
        if self.price_range_min and self.price_range_max:
            if self.price_range_min > self.price_range_max:
                raise ValidationError("Minimum price cannot be greater than maximum price")







