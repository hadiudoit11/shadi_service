from django.db import models

from .user_profile import EventUser
from .vendor_business import Vendor


class VendorInquiry(models.Model):
    """Track inquiries sent to vendors from couples"""

    STATUS_CHOICES = [
        ('pending', 'Pending Response'),
        ('in-review', 'In Review'),
        ('responded', 'Vendor Responded'),
        ('waiting on customer', 'Waiting on Customer'),
        ('booked', 'Booking Confirmed'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='inquiries')
    submitted_by = models.ForeignKey(EventUser, on_delete=models.CASCADE, related_name='inquiries_submitted')
    # Event Details
    event_date = models.DateField()
    event_location = models.CharField(max_length=200)
    guest_count = models.PositiveIntegerField()
    budget_range_high = models.PositiveIntegerField(blank=True, null=True)
    budget_range_low = models.PositiveIntegerField(blank=True, null=True)

    # Inquiry Details
    message = models.TextField()
    package_requested = models.JSONField(default=list)

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