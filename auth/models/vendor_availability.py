from django.db import models
from .vendor_business import Vendor

class VendorAvailability(models.Model):
    """Track vendor availability for specific dates"""

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='availability')
    date = models.DateField()
    is_available = models.BooleanField(default=True)
    slots_available = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Vendor Availability"
        verbose_name_plural = "Vendor Availabilities"
        unique_together = ['vendor', 'date']
        ordering = ['date']

    def __str__(self):
        status = "Available" if self.is_available else "Unavailable"
        return f"{self.vendor.business_name} - {self.date} ({status})"