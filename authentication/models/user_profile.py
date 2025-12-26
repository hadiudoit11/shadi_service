from django.contrib.auth.models import AbstractUser
from .base_manager import EventUserManager
from django.db import models
from django.core.exceptions import ValidationError



class EventUser(AbstractUser):
    # Event Role Choices (Note: Vendors are separate business entities, not user roles)
    BRIDE = 'bride'
    GROOM = 'groom'
    ORGANIZER = 'organizer'
    CO_ORGANIZER = 'co_organizer'
    WEDDING_PLANNER = 'wedding_planner'
    VENDOR_REPRESENTATIVE = 'vendor_rep'  # Person who represents a vendor business
    ATTENDEE = 'attendee'
    ADMIN = 'admin'
    
    EVENT_ROLE_CHOICES = [
        (BRIDE, 'Bride'),
        (GROOM, 'Groom'),
        (ORGANIZER, 'Event Organizer'),
        (CO_ORGANIZER, 'Co-Organizer'),
        (WEDDING_PLANNER, 'Wedding Planner'),
        (VENDOR_REPRESENTATIVE, 'Vendor Representative'),  # Person working for a vendor
        (ATTENDEE, 'Attendee'),
        (ADMIN, 'Admin'),
    ]
    

    
    # Auth0 Fields
    auth0_user_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    auth0_email = models.EmailField(null=True, blank=True)
    auth0_picture = models.URLField(blank=True, null=True)
    auth0_nickname = models.CharField(max_length=100, blank=True, null=True)

    # # Billing Fields
    # subscription_tier = models.CharField(max_length=20, choices=SUBSCRIPTION_CHOICES, default=FREE)
    # subscription_active = models.BooleanField(default=False)
    # stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    # trial_end_date = models.DateTimeField(null=True, blank=True)
    
    # Auth0 Authorization Fields (instead of hard-coded permissions)
    auth0_roles = models.JSONField(default=list, blank=True, help_text="Auth0 roles assigned to user")
    auth0_permissions = models.JSONField(default=list, blank=True, help_text="Auth0 permissions from roles")
    last_auth0_sync = models.DateTimeField(null=True, blank=True, help_text="Last time Auth0 data was synced")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = EventUserManager()
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @property
    def display_name(self):
        return self.auth0_nickname or self.get_full_name() or self.username
    
    def has_role(self, role):
        """Check if user has a specific role"""
        return role in (self.auth0_roles or [])
    
    def add_role(self, role):
        """Add a role to user's auth0_roles"""
        if not self.auth0_roles:
            self.auth0_roles = []
        if role not in self.auth0_roles:
            self.auth0_roles.append(role)
            self.save()
    
    def remove_role(self, role):
        """Remove a role from user's auth0_roles"""
        if self.auth0_roles and role in self.auth0_roles:
            self.auth0_roles.remove(role)
            self.save()
    
    @property
    def all_roles(self):
        """Get all auth0 roles"""
        return self.auth0_roles or []
    
    @property
    def is_bride_or_groom(self):
        return self.has_role(self.BRIDE) or self.has_role(self.GROOM)
    
    @property
    def is_wedding_couple(self):
        return self.is_bride_or_groom
    
    @property
    def is_event_organizer(self):
        return (self.has_role(self.ORGANIZER) or 
                self.has_role(self.CO_ORGANIZER) or 
                self.has_role(self.WEDDING_PLANNER))
    
    @property
    def has_wedding_planning_access(self):
        return (self.is_bride_or_groom or 
                self.has_role(self.WEDDING_PLANNER) or 
                self.has_role(self.ORGANIZER))
    
    @property
    def has_premium_access(self):
        return 'premium' in (self.auth0_roles or [])
    
    @property
    def can_create_unlimited_events(self):
        return self.has_premium_access or self.has_role(self.ORGANIZER)
    
    @property
    def max_events_allowed(self):
        if self.has_premium_access:
            return 999
        return 1
    
    def update_from_auth0(self, auth0_data):
        self.auth0_email = auth0_data.get('email', self.auth0_email)
        self.auth0_picture = auth0_data.get('picture', self.auth0_picture)
        self.auth0_nickname = auth0_data.get('nickname', self.auth0_nickname)
        self.email = auth0_data.get('email', self.email)
        self.first_name = auth0_data.get('given_name', self.first_name)
        self.last_name = auth0_data.get('family_name', self.last_name)
        self.save()
    
    def sync_auth0_permissions(self):
        """Sync user permissions from Auth0 - replaces hard-coded permission logic"""
        from ..services.auth0_permissions import Auth0UserSync
        
        sync_service = Auth0UserSync()
        return sync_service.sync_user_permissions(self)
    
    def needs_permission_sync(self) -> bool:
        """Check if user permissions need to be synced from Auth0"""
        from django.utils import timezone
        from datetime import timedelta
        
        if not self.last_auth0_sync:
            return True
        
        # Sync if it's been more than 1 hour since last sync
        return self.last_auth0_sync < timezone.now() - timedelta(hours=1)
    
    # Auth0 Role Helper Methods
    def has_auth0_permission(self, permission):
        """Check if user has specific Auth0 permission"""
        return permission in (self.auth0_permissions or [])
    
    def has_auth0_role(self, role):
        """Check if user has specific Auth0 role"""
        return role in (self.auth0_roles or [])
    
    # Wedding Service Specific Role Checks
    @property
    def is_bride_or_groom_auth0(self):
        """Check if user is bride or groom via Auth0 roles"""
        return self.has_auth0_role('bride_groom')
    
    @property
    def is_wedding_planner_auth0(self):
        """Check if user is wedding planner via Auth0 roles"""
        return self.has_auth0_role('wedding_planner')
    
    @property
    def is_vendor_owner_auth0(self):
        """Check if user is vendor owner via Auth0 roles"""
        return self.has_auth0_role('vendor_owner')
    
    @property
    def is_vendor_staff_auth0(self):
        """Check if user is vendor staff via Auth0 roles"""
        return self.has_auth0_role('vendor_staff')
    
    @property
    def is_super_admin_auth0(self):
        """Check if user is super admin via Auth0 roles"""
        return self.has_auth0_role('super_admin')

    @property
    def is_vendor_representative(self):
        """Check if user represents any vendors"""
        return (self.has_auth0_role('vendor_owner') or 
                self.has_auth0_role('vendor_staff') or 
                self.has_role(self.VENDOR_REPRESENTATIVE) or 
                self.managed_vendors.exists())
    
    @property
    def represented_vendors(self):
        """Get vendors this user represents"""
        return self.managed_vendors.filter(is_active=True)
    
    def can_manage_vendor(self, vendor):
        """Check if user can manage a specific vendor"""
        if not self.is_vendor_representative:
            return False
        
        try:
            vendor_user = self.managed_vendors.get(vendor=vendor, is_active=True)
            return vendor_user.can_edit_vendor_info
        except:
            return False
    
    def get_vendor_role(self, vendor):
        """Get user's role for a specific vendor"""
        try:
            vendor_user = self.managed_vendors.get(vendor=vendor, is_active=True)
            return vendor_user.role
        except:
            return None
    
    def get_wedding_partner(self):
        """Get the wedding partner if exists - simplified for now"""
        return None
    
    def link_wedding_partner(self, partner_user):
        """Link two users as wedding partners - simplified for now"""
        pass
    
    def get_shared_wedding_data(self):
        """Get wedding data shared between partners - simplified for now"""
        return {
            'user_id': self.id,
            'user_name': self.display_name,
            'user_email': self.email,
        }
    
    def clean(self):
        super().clean()
        # Simplified validation - remove references to missing fields
    
    class Meta:
        verbose_name = "Event User"
        verbose_name_plural = "Event Users"