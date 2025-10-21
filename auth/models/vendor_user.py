from django.db import models
from vendor_business import Vendor
from user_profile import UserProfile

class VendorUser(models.Model):
    """Relationship between vendors and users who can manage them - permissions via Auth0"""

    ROLE_CHOICES = [
        ('owner', 'Business Owner'),
        ('employee', 'Employee'),
        ('manager', 'Manager'),
        ('representative', 'Representative'),
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='vendor_users')
    user = models.ForeignKey('UserProfile', on_delete=models.CASCADE, related_name='managed_vendors')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='representative')

    # Auth0 metadata for this vendor relationship
    auth0_organization_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Auth0 Organization ID for this vendor business"
    )
    auth0_role_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Auth0 Role ID assigned to user for this vendor"
    )

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vendor User"
        verbose_name_plural = "Vendor Users"
        unique_together = ['vendor', 'user']

    def __str__(self):
        return f"{self.user.display_name} - {self.vendor.business_name} ({self.role})"

    def get_vendor_permissions(self):
        """Get Auth0 permissions for this user-vendor relationship"""
        # This would check Auth0 for vendor-specific permissions
        # For now, return based on role until Auth0 Organizations are set up
        base_permissions = [
            'read:vendor_info',
            'read:vendor_inquiries',
        ]

        if self.role in ['owner', 'manager']:
            base_permissions.extend([
                'edit:vendor_info',
                'manage:vendor_bookings',
                'respond:vendor_inquiries',
                'view:vendor_analytics',
                'manage:vendor_team',
            ])
        elif self.role == 'employee':
            base_permissions.extend([
                'manage:vendor_bookings',
                'respond:vendor_inquiries',
            ])
        elif self.role == 'representative':
            base_permissions.extend([
                'respond:vendor_inquiries',
            ])

        return base_permissions
