from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid


class Service(models.Model):
    """Individual services that vendors can offer"""
    
    SERVICE_TYPES = [
        ('time_based', 'Time-Based (hourly/daily)'),
        ('per_guest', 'Per Guest'),
        ('flat_rate', 'Flat Rate'),
        ('tiered', 'Tiered Pricing'),
        ('custom', 'Custom Quote Required'),
    ]
    
    DURATION_UNITS = [
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ]
    
    # Basic Info
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey('VendorCategory', on_delete=models.CASCADE)
    
    # Pricing
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES, default='flat_rate')
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    minimum_order = models.PositiveIntegerField(default=1, help_text="Minimum quantity/hours/guests")
    maximum_order = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum quantity/hours/guests")
    
    # Duration & Capacity
    duration_value = models.PositiveIntegerField(null=True, blank=True, help_text="How long the service lasts")
    duration_unit = models.CharField(max_length=10, choices=DURATION_UNITS, default='hours')
    setup_time = models.PositiveIntegerField(default=0, help_text="Setup time in minutes")
    teardown_time = models.PositiveIntegerField(default=0, help_text="Teardown time in minutes") 
    max_concurrent_bookings = models.PositiveIntegerField(default=1, help_text="How many events can book this simultaneously")
    
    # Availability Rules
    advance_booking_days = models.PositiveIntegerField(default=7, help_text="Minimum days advance booking required")
    available_days_of_week = models.JSONField(default=list, help_text="Available days: [0=Mon, 1=Tue, ..., 6=Sun]")
    blackout_dates = models.JSONField(default=list, help_text="Dates service is unavailable")
    seasonal_availability = models.JSONField(default=dict, help_text="Seasonal pricing/availability rules")
    
    # Requirements
    venue_requirements = models.JSONField(default=list, help_text="Required venue features")
    guest_count_min = models.PositiveIntegerField(null=True, blank=True)
    guest_count_max = models.PositiveIntegerField(null=True, blank=True)
    special_requirements = models.TextField(blank=True)
    
    # Media & Details
    images = models.JSONField(default=list, help_text="Service images URLs")
    videos = models.JSONField(default=list, help_text="Service video URLs")
    documents = models.JSONField(default=list, help_text="Contracts, menus, etc.")
    tags = models.JSONField(default=list, help_text="Search tags")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_customizable = models.BooleanField(default=False, help_text="Can be customized for each booking")
    requires_consultation = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['name']
        indexes = [
            models.Index(fields=['vendor', 'is_active']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.vendor.business_name} - {self.name}"
    
    @property
    def total_duration_minutes(self):
        """Total time needed including setup/teardown"""
        service_minutes = 0
        if self.duration_value:
            if self.duration_unit == 'hours':
                service_minutes = self.duration_value * 60
            elif self.duration_unit == 'days':
                service_minutes = self.duration_value * 24 * 60
        
        return service_minutes + self.setup_time + self.teardown_time
    
    def calculate_price(self, quantity=1, guest_count=None, custom_options=None):
        """Calculate price based on service type and parameters"""
        if self.service_type == 'flat_rate':
            return self.base_price
        
        elif self.service_type == 'time_based':
            return self.base_price + (self.price_per_unit * quantity)
        
        elif self.service_type == 'per_guest':
            if not guest_count:
                raise ValueError("Guest count required for per-guest pricing")
            return self.base_price + (self.price_per_unit * guest_count)
        
        elif self.service_type == 'tiered':
            # Implement tiered pricing logic based on quantity
            base = self.base_price
            if quantity > 10:
                base *= Decimal('0.9')  # 10% discount for large orders
            return base * quantity
        
        return self.base_price
    
    def is_available_on_date(self, date, start_time=None, duration_hours=None):
        """Check if service is available on a specific date/time"""
        # Check day of week
        if self.available_days_of_week and date.weekday() not in self.available_days_of_week:
            return False
        
        # Check blackout dates
        if date.strftime('%Y-%m-%d') in self.blackout_dates:
            return False
        
        # Check advance booking requirement
        from django.utils import timezone
        days_in_advance = (date - timezone.now().date()).days
        if days_in_advance < self.advance_booking_days:
            return False
        
        # TODO: Check existing bookings vs max_concurrent_bookings
        
        return True
    
    def clean(self):
        super().clean()
        if self.service_type in ['time_based', 'per_guest'] and not self.price_per_unit:
            raise ValidationError(f"{self.service_type} pricing requires price_per_unit")
        
        if self.maximum_order and self.maximum_order < self.minimum_order:
            raise ValidationError("Maximum order cannot be less than minimum order")


class Package(models.Model):
    """Bundles of services that vendors can offer together"""
    
    PACKAGE_TYPES = [
        ('bundle', 'Service Bundle'),
        ('wedding_package', 'Wedding Package'),
        ('seasonal', 'Seasonal Package'),
        ('promotional', 'Promotional Package'),
    ]
    
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage Off'),
        ('fixed_amount', 'Fixed Amount Off'),
        ('bundle_price', 'Bundle Price'),
    ]
    
    # Basic Info
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE, related_name='packages')
    name = models.CharField(max_length=200)
    description = models.TextField()
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES, default='bundle')
    
    # Services in Package
    services = models.ManyToManyField(Service, through='PackageService', related_name='packages')
    
    # Pricing
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Percentage or amount")
    minimum_spend = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bundle_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Availability
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    max_bookings = models.PositiveIntegerField(null=True, blank=True, help_text="Max times this package can be booked")
    current_bookings = models.PositiveIntegerField(default=0)
    
    # Requirements
    minimum_guest_count = models.PositiveIntegerField(null=True, blank=True)
    maximum_guest_count = models.PositiveIntegerField(null=True, blank=True)
    requires_all_services = models.BooleanField(default=True, help_text="Must book all services in package")
    
    # Media
    images = models.JSONField(default=list)
    featured_image = models.URLField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True, help_text="Visible to customers")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Package"
        verbose_name_plural = "Packages"
        ordering = ['-is_featured', 'name']
    
    def __str__(self):
        return f"{self.vendor.business_name} - {self.name}"
    
    @property
    def services_total_price(self):
        """Calculate total price of all services without discount"""
        total = Decimal('0')
        for package_service in self.package_services.all():
            service_price = package_service.service.base_price
            if package_service.quantity:
                service_price *= package_service.quantity
            total += service_price
        return total
    
    @property
    def discounted_price(self):
        """Calculate final package price with discount"""
        if self.discount_type == 'bundle_price' and self.bundle_price:
            return self.bundle_price
        
        total = self.services_total_price
        
        if self.discount_type == 'percentage':
            discount_amount = total * (self.discount_value / 100)
            return total - discount_amount
        
        elif self.discount_type == 'fixed_amount':
            return max(total - self.discount_value, Decimal('0'))
        
        return total
    
    @property
    def savings_amount(self):
        """How much customer saves with this package"""
        return self.services_total_price - self.discounted_price
    
    @property
    def savings_percentage(self):
        """Savings as percentage"""
        if self.services_total_price > 0:
            return (self.savings_amount / self.services_total_price) * 100
        return 0
    
    def is_available_for_date(self, date):
        """Check if package is available for booking on date"""
        if not self.is_active:
            return False
        
        if self.valid_from and date < self.valid_from:
            return False
        
        if self.valid_until and date > self.valid_until:
            return False
        
        if self.max_bookings and self.current_bookings >= self.max_bookings:
            return False
        
        # Check if all services are available
        for package_service in self.package_services.all():
            if not package_service.service.is_available_on_date(date):
                return False
        
        return True
    
    def clean(self):
        super().clean()
        if self.valid_from and self.valid_until and self.valid_from > self.valid_until:
            raise ValidationError("Valid from date cannot be after valid until date")


class PackageService(models.Model):
    """Through model for Package-Service relationship with specific quantities"""
    
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='package_services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='package_services')
    quantity = models.PositiveIntegerField(default=1, help_text="How many of this service in the package")
    is_optional = models.BooleanField(default=False, help_text="Service is optional in package")
    custom_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                      help_text="Override service price for this package")
    notes = models.TextField(blank=True, help_text="Special notes for this service in the package")
    
    class Meta:
        verbose_name = "Package Service"
        verbose_name_plural = "Package Services"
        unique_together = ['package', 'service']
    
    def __str__(self):
        return f"{self.package.name} - {self.service.name} (x{self.quantity})"
    
    @property
    def total_price(self):
        """Calculate total price for this service in the package"""
        if self.custom_price:
            return self.custom_price * self.quantity
        return self.service.base_price * self.quantity


class ServiceAvailability(models.Model):
    """Smart availability tracking for services"""
    
    AVAILABILITY_STATUS = [
        ('available', 'Available'),
        ('booked', 'Fully Booked'),
        ('partially_booked', 'Partially Booked'),
        ('blocked', 'Blocked by Vendor'),
        ('maintenance', 'Under Maintenance'),
    ]
    
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='availability_slots')
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    # Availability Details
    status = models.CharField(max_length=20, choices=AVAILABILITY_STATUS, default='available')
    capacity_total = models.PositiveIntegerField(default=1, help_text="Total capacity for this slot")
    capacity_booked = models.PositiveIntegerField(default=0, help_text="Currently booked capacity")
    
    # Pricing Overrides
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                        help_text="Override base price for this slot")
    surge_pricing = models.DecimalField(max_digits=5, decimal_places=2, default=1.0,
                                       help_text="Multiplier for surge pricing (1.0 = normal)")
    
    # Notes
    vendor_notes = models.TextField(blank=True, help_text="Internal vendor notes")
    customer_notes = models.TextField(blank=True, help_text="Notes visible to customers")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Service Availability"
        verbose_name_plural = "Service Availabilities"
        unique_together = ['service', 'date', 'start_time']
        ordering = ['date', 'start_time']
    
    def __str__(self):
        time_str = f" {self.start_time}-{self.end_time}" if self.start_time else ""
        return f"{self.service.name} - {self.date}{time_str} ({self.status})"
    
    @property
    def remaining_capacity(self):
        """How much capacity is still available"""
        return max(0, self.capacity_total - self.capacity_booked)
    
    @property
    def is_available(self):
        """Check if any capacity is available"""
        return self.status == 'available' and self.remaining_capacity > 0
    
    @property
    def effective_price(self):
        """Get effective price including overrides and surge pricing"""
        base_price = self.price_override or self.service.base_price
        return base_price * self.surge_pricing
    
    def book_capacity(self, quantity=1):
        """Book some capacity for this slot"""
        if quantity > self.remaining_capacity:
            raise ValidationError(f"Cannot book {quantity}, only {self.remaining_capacity} remaining")
        
        self.capacity_booked += quantity
        
        if self.capacity_booked >= self.capacity_total:
            self.status = 'booked'
        elif self.capacity_booked > 0:
            self.status = 'partially_booked'
        
        self.save()
    
    def release_capacity(self, quantity=1):
        """Release booked capacity"""
        self.capacity_booked = max(0, self.capacity_booked - quantity)
        
        if self.capacity_booked == 0:
            self.status = 'available'
        elif self.capacity_booked < self.capacity_total:
            self.status = 'partially_booked'
        
        self.save()