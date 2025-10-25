from django.db import models
from .vendor_business import Vendor


class VendorInquiry(models.Model):
    """Track inquiries sent to vendors from couples"""

    STATUS_CHOICES = [
        ('pending', 'Pending Response'),
        ('responded', 'Vendor Responded'),
        ('booked', 'Booking Confirmed'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='inquiries')
    couple_user = models.ForeignKey('user_profile.EventUser', on_delete=models.CASCADE, related_name='vendor_inquiries')

    # Event Details
    event_date = models.DateField()
    event_location = models.CharField(max_length=200)
    guest_count = models.PositiveIntegerField()
    budget_range = models.CharField(max_length=100, blank=True)

    # Inquiry Details
    message = models.TextField()
    services_requested = models.JSONField(default=list)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    vendor_response = models.TextField(blank=True)
    vendor_quote = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Vendor Inquiry"
        verbose_name_plural = "Vendor Inquiries"
        ordering = ['-created_at']

    def __str__(self):
        return f"Inquiry to {self.vendor.business_name} for {self.event_date}"