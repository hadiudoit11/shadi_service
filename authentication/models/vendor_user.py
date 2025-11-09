from django.db import models
from .vendor_business import Vendor
from .user_profile import EventUser


class VendorUser(models.Model):
    """Simple many-to-many relationship between vendors and users"""

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='vendor_users')
    user = models.ForeignKey(EventUser, on_delete=models.CASCADE, related_name='managed_vendors')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    
    # Simple tracking
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vendor User"
        verbose_name_plural = "Vendor Users"
        unique_together = ['vendor', 'user']

    def __str__(self):
        return f"{self.user.display_name} - {self.vendor.business_name} ({self.role})"
