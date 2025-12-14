from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import FileExtensionValidator
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid
import os


class VendorImage(models.Model):
    """Model for managing vendor images with classifications"""
    
    IMAGE_TYPES = [
        # Business Identity
        ('logo', 'Logo'),
        ('logo_dark', 'Logo (Dark Mode)'),
        ('logo_light', 'Logo (Light Mode)'),
        ('favicon', 'Favicon/Small Icon'),
        
        # Profile & Team
        ('profile_primary', 'Primary Profile Picture'),
        ('profile_team', 'Team Member Photo'),
        ('profile_owner', 'Owner/Founder Photo'),
        ('profile_artist', 'Artist/Designer Profile'),
        
        # Storefront/Marketplace
        ('storefront_hero', 'Storefront Hero Banner'),
        ('storefront_cover', 'Storefront Cover Image'),
        ('storefront_featured', 'Storefront Featured Image'),
        ('storefront_thumbnail', 'Marketplace Thumbnail'),
        ('storefront_banner', 'Promotional Banner'),
        
        # Portfolio & Work Samples
        ('portfolio', 'Portfolio Image'),
        ('portfolio_featured', 'Featured Work'),
        ('portfolio_before', 'Before Photo'),
        ('portfolio_after', 'After Photo'),
        ('portfolio_360', '360° View'),
        
        # Venue Specific
        ('venue_exterior', 'Venue Exterior'),
        ('venue_interior', 'Venue Interior'),
        ('venue_aerial', 'Aerial/Drone Shot'),
        ('venue_night', 'Night View'),
        ('venue_ceremony', 'Ceremony Space'),
        ('venue_reception', 'Reception Space'),
        
        # Service Specific
        ('menu_food', 'Food Menu/Samples'),
        ('menu_drinks', 'Drinks/Bar Menu'),
        ('decor_sample', 'Decor Sample'),
        ('setup_diagram', 'Setup/Layout Diagram'),
        
        # Marketing & Social
        ('social_cover', 'Social Media Cover'),
        ('social_post', 'Social Media Post'),
        ('testimonial', 'Testimonial/Review Image'),
        ('certificate', 'Certificate/Award'),
        ('press', 'Press/Media Feature'),
        
        # Gallery
        ('gallery', 'General Gallery'),
        ('gallery_event', 'Event Photos'),
        ('gallery_behind', 'Behind the Scenes'),
        
        ('other', 'Other'),
    ]
    
    IMAGE_DISPLAY_LOCATIONS = [
        # Marketplace/Search Results
        ('marketplace_grid', 'Marketplace Grid View'),
        ('marketplace_list', 'Marketplace List View'),
        ('marketplace_map', 'Map Popup'),
        ('search_result', 'Search Result Card'),
        ('category_hero', 'Category Page Hero'),
        
        # Vendor Storefront Page
        ('storefront_header', 'Storefront Header'),
        ('storefront_about', 'About Section'),
        ('storefront_services', 'Services Section'),
        ('storefront_gallery', 'Storefront Gallery'),
        ('storefront_contact', 'Contact Section'),
        
        # Detail Pages
        ('detail_hero', 'Detail Page Hero'),
        ('detail_gallery', 'Detail Gallery'),
        ('detail_sidebar', 'Detail Sidebar'),
        ('detail_reviews', 'Reviews Section'),
        
        # Cards & Thumbnails
        ('card_small', 'Small Card (200x200)'),
        ('card_medium', 'Medium Card (400x300)'),
        ('card_large', 'Large Card (800x600)'),
        ('card_featured', 'Featured Vendor Card'),
        
        # Homepage
        ('homepage_hero', 'Homepage Hero Slider'),
        ('homepage_featured', 'Featured Vendors Section'),
        ('homepage_category', 'Category Showcase'),
        
        # Mobile Specific
        ('mobile_splash', 'Mobile App Splash'),
        ('mobile_card', 'Mobile Card View'),
        ('mobile_story', 'Mobile Story View'),
        
        # Social & Marketing
        ('social_share', 'Social Share Preview'),
        ('email_header', 'Email Header'),
        ('ad_banner', 'Advertisement Banner'),
        
        # Modals & Overlays
        ('modal_gallery', 'Gallery Modal'),
        ('modal_preview', 'Quick Preview Modal'),
        ('lightbox', 'Lightbox View'),
    ]
    
    IMAGE_CONTEXTS = [
        ('public', 'Public - Anyone can view'),
        ('authenticated', 'Authenticated Users Only'),
        ('premium', 'Premium Members Only'),
        ('vendor_only', 'Vendor Internal Use'),
        ('admin_only', 'Admin Only'),
    ]
    
    ASPECT_RATIOS = [
        ('1:1', 'Square (1:1)'),
        ('4:3', 'Standard (4:3)'),
        ('16:9', 'Widescreen (16:9)'),
        ('21:9', 'Ultrawide (21:9)'),
        ('9:16', 'Portrait/Story (9:16)'),
        ('2:3', 'Portrait (2:3)'),
        ('custom', 'Custom'),
    ]
    
    vendor = models.ForeignKey(
        'Vendor',
        on_delete=models.CASCADE,
        related_name='images'
    )
    
    image_type = models.CharField(
        max_length=20,
        choices=IMAGE_TYPES,
        default='portfolio',
        help_text='Classification of the image'
    )
    
    display_locations = ArrayField(
        models.CharField(max_length=20, choices=IMAGE_DISPLAY_LOCATIONS),
        default=list,
        blank=True,
        help_text='Where this image should appear in the UI'
    )
    
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text='Image title or caption'
    )
    
    description = models.TextField(
        blank=True,
        help_text='Detailed description of the image'
    )
    
    image_url = models.URLField(
        max_length=500,
        blank=True,
        help_text='S3 URL of the uploaded image'
    )
    
    image_file = models.ImageField(
        upload_to='vendor_images/',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
        blank=True,
        null=True,
        help_text='Upload image (will be uploaded to S3)'
    )
    
    alt_text = models.CharField(
        max_length=200,
        blank=True,
        help_text='Alt text for accessibility'
    )
    
    # New fields for better classification
    visibility_context = models.CharField(
        max_length=20,
        choices=IMAGE_CONTEXTS,
        default='public',
        help_text='Who can view this image'
    )
    
    aspect_ratio = models.CharField(
        max_length=10,
        choices=ASPECT_RATIOS,
        default='custom',
        help_text='Image aspect ratio'
    )
    
    width = models.IntegerField(
        null=True,
        blank=True,
        help_text='Image width in pixels'
    )
    
    height = models.IntegerField(
        null=True,
        blank=True,
        help_text='Image height in pixels'
    )
    
    file_size = models.IntegerField(
        null=True,
        blank=True,
        help_text='File size in bytes'
    )
    
    order = models.IntegerField(
        default=0,
        help_text='Display order (lower numbers appear first)'
    )
    
    is_primary = models.BooleanField(
        default=False,
        help_text='Is this the primary image for this type?'
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text='Is this image currently active?'
    )
    
    is_watermarked = models.BooleanField(
        default=False,
        help_text='Does this image have a watermark?'
    )
    
    season = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('spring', 'Spring'),
            ('summer', 'Summer'),
            ('fall', 'Fall'),
            ('winter', 'Winter'),
            ('all', 'All Seasons'),
        ],
        help_text='Season this image is relevant for'
    )
    
    tags = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text='Tags for filtering (e.g., "outdoor", "traditional", "modern")'
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional metadata (dimensions, file size, etc.)'
    )
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['vendor', 'image_type', 'order']
        indexes = [
            models.Index(fields=['vendor', 'image_type']),
            models.Index(fields=['is_active', 'is_primary']),
        ]
    
    def __str__(self):
        return f"{self.vendor.business_name} - {self.get_image_type_display()} - {self.title or 'Untitled'}"
    
    def save(self, *args, **kwargs):
        """Override save to handle S3 upload and ensure only one primary per type"""
        
        # If marked as primary, unset other primary images of same type for this vendor
        if self.is_primary:
            VendorImage.objects.filter(
                vendor=self.vendor,
                image_type=self.image_type,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        
        # If image_file is provided but no URL, upload to S3
        if self.image_file and not self.image_url:
            # Generate unique filename
            file_extension = os.path.splitext(self.image_file.name)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            folder = f"vendors/{self.vendor.id}/{self.image_type}"
            file_path = f"{folder}/{unique_filename}"
            
            # Save to S3 and get URL
            file_content = self.image_file.read()
            saved_path = default_storage.save(file_path, ContentFile(file_content))
            self.image_url = default_storage.url(saved_path)
            
            # Store metadata
            self.metadata.update({
                'original_filename': self.image_file.name,
                'file_size': len(file_content),
                's3_path': saved_path,
            })
        
        # Generate alt text if not provided
        if not self.alt_text and self.title:
            self.alt_text = self.title
        elif not self.alt_text:
            self.alt_text = f"{self.vendor.business_name} {self.get_image_type_display()}"
        
        super().save(*args, **kwargs)
    
    @property
    def display_url(self):
        """Return the URL to use for display"""
        return self.image_url or (self.image_file.url if self.image_file else '')
    
    @classmethod
    def get_vendor_images_by_location(cls, vendor, location):
        """Get all images for a vendor that should appear in a specific location"""
        return cls.objects.filter(
            vendor=vendor,
            display_locations__contains=[location],
            is_active=True
        ).order_by('order')
    
    @classmethod
    def get_vendor_primary_image(cls, vendor, image_type='logo'):
        """Get the primary image of a specific type for a vendor"""
        return cls.objects.filter(
            vendor=vendor,
            image_type=image_type,
            is_primary=True,
            is_active=True
        ).first()