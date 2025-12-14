from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from ..models import Vendor, VendorImage


class VendorImagesAPIView(APIView):
    """Get vendor images organized by type and location"""
    permission_classes = [AllowAny]
    
    @extend_schema(
        operation_id='get_vendor_images',
        summary="Get vendor images",
        description="Get all images for a vendor, optionally filtered by type or display location",
        parameters=[
            OpenApiParameter(
                name='type',
                description='Filter by image type (logo, cover, portfolio, etc.)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='location',
                description='Filter by display location (card, hero, gallery, etc.)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='primary_only',
                description='Only return primary images',
                required=False,
                type=bool
            ),
        ],
        responses={
            200: OpenApiResponse(description="Images retrieved successfully"),
            404: OpenApiResponse(description="Vendor not found"),
        },
        tags=['Vendors']
    )
    def get(self, request, vendor_id):
        """Get vendor images"""
        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Vendor not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Base queryset
        images = VendorImage.objects.filter(vendor=vendor, is_active=True)
        
        # Apply filters
        image_type = request.GET.get('type')
        if image_type:
            images = images.filter(image_type=image_type)
        
        location = request.GET.get('location')
        if location:
            images = images.filter(display_locations__contains=[location])
        
        primary_only = request.GET.get('primary_only') == 'true'
        if primary_only:
            images = images.filter(is_primary=True)
        
        # Order by type and order field
        images = images.order_by('image_type', 'order')
        
        # Group images by type
        images_by_type = {}
        for image in images:
            if image.image_type not in images_by_type:
                images_by_type[image.image_type] = []
            
            images_by_type[image.image_type].append({
                'id': image.id,
                'url': image.display_url,
                'title': image.title,
                'description': image.description,
                'alt_text': image.alt_text,
                'is_primary': image.is_primary,
                'display_locations': image.display_locations,
                'tags': image.tags,
                'order': image.order,
            })
        
        # Get specific image sets organized for different UI contexts
        ui_images = {
            # Business Identity
            'logo': None,
            'logo_dark': None,
            'logo_light': None,
            'favicon': None,
            
            # Profile Pictures
            'profile_primary': None,
            'profile_owner': None,
            'profile_team': [],
            
            # Marketplace & Search
            'marketplace_thumbnail': None,
            'marketplace_cover': None,
            'search_card_image': None,
            
            # Storefront Page
            'storefront_hero': None,
            'storefront_cover': None,
            'storefront_featured': [],
            'storefront_gallery': [],
            
            # Portfolio & Work
            'portfolio_featured': [],
            'portfolio_all': [],
            'before_after': [],
            
            # Venue Specific (for venue vendors)
            'venue_exterior': [],
            'venue_interior': [],
            'venue_ceremony': None,
            'venue_reception': None,
            
            # Social Media & Marketing
            'social_cover': None,
            'social_posts': [],
            
            # Mobile Optimized
            'mobile_card': None,
            'mobile_story': [],
        }
        
        # Helper function to get images by type and location
        def get_images_by_criteria(image_type=None, location=None, limit=None):
            query = VendorImage.objects.filter(vendor=vendor, is_active=True)
            if image_type:
                query = query.filter(image_type=image_type)
            if location:
                query = query.filter(display_locations__contains=[location])
            query = query.order_by('order', '-is_primary')
            return query[:limit] if limit else query
        
        # Business Identity
        logo = get_images_by_criteria('logo').first()
        if logo:
            ui_images['logo'] = logo.display_url
            
        logo_dark = get_images_by_criteria('logo_dark').first()
        if logo_dark:
            ui_images['logo_dark'] = logo_dark.display_url
            
        logo_light = get_images_by_criteria('logo_light').first()
        if logo_light:
            ui_images['logo_light'] = logo_light.display_url
        
        # Profile Pictures
        profile_primary = get_images_by_criteria('profile_primary').first()
        if profile_primary:
            ui_images['profile_primary'] = profile_primary.display_url
            
        profile_owner = get_images_by_criteria('profile_owner').first()
        if profile_owner:
            ui_images['profile_owner'] = profile_owner.display_url
            
        team_photos = get_images_by_criteria('profile_team', limit=10)
        ui_images['profile_team'] = [img.display_url for img in team_photos]
        
        # Marketplace Images
        marketplace_thumb = get_images_by_criteria('storefront_thumbnail').first() or \
                           get_images_by_criteria(location='marketplace_grid').first()
        if marketplace_thumb:
            ui_images['marketplace_thumbnail'] = marketplace_thumb.display_url
            
        storefront_cover = get_images_by_criteria('storefront_cover').first()
        if storefront_cover:
            ui_images['storefront_cover'] = storefront_cover.display_url
        
        # Search result card image (priority order)
        search_card = get_images_by_criteria(location='search_result').first() or \
                     get_images_by_criteria(location='card_medium').first() or \
                     marketplace_thumb
        if search_card:
            ui_images['search_card_image'] = search_card.display_url
        
        # Storefront Page
        storefront_hero = get_images_by_criteria('storefront_hero').first() or \
                         get_images_by_criteria(location='storefront_header').first()
        if storefront_hero:
            ui_images['storefront_hero'] = storefront_hero.display_url
            
        storefront_featured = get_images_by_criteria('storefront_featured', limit=6)
        ui_images['storefront_featured'] = [img.display_url for img in storefront_featured]
        
        storefront_gallery = get_images_by_criteria(location='storefront_gallery', limit=20)
        ui_images['storefront_gallery'] = [img.display_url for img in storefront_gallery]
        
        # Portfolio Images
        portfolio_featured = get_images_by_criteria('portfolio_featured', limit=8)
        ui_images['portfolio_featured'] = [img.display_url for img in portfolio_featured]
        
        portfolio_all = get_images_by_criteria('portfolio', limit=50)
        ui_images['portfolio_all'] = [img.display_url for img in portfolio_all]
        
        # Before/After combinations
        before_images = get_images_by_criteria('portfolio_before')
        after_images = get_images_by_criteria('portfolio_after')
        before_after = []
        for i in range(min(len(before_images), len(after_images))):
            before_after.append({
                'before': before_images[i].display_url,
                'after': after_images[i].display_url
            })
        ui_images['before_after'] = before_after
        
        # Venue Specific
        ui_images['venue_exterior'] = [img.display_url for img in get_images_by_criteria('venue_exterior', limit=10)]
        ui_images['venue_interior'] = [img.display_url for img in get_images_by_criteria('venue_interior', limit=10)]
        
        venue_ceremony = get_images_by_criteria('venue_ceremony').first()
        if venue_ceremony:
            ui_images['venue_ceremony'] = venue_ceremony.display_url
            
        venue_reception = get_images_by_criteria('venue_reception').first()
        if venue_reception:
            ui_images['venue_reception'] = venue_reception.display_url
        
        # Social Media
        social_cover = get_images_by_criteria('social_cover').first()
        if social_cover:
            ui_images['social_cover'] = social_cover.display_url
            
        social_posts = get_images_by_criteria('social_post', limit=12)
        ui_images['social_posts'] = [img.display_url for img in social_posts]
        
        # Mobile Optimized
        mobile_card = get_images_by_criteria(location='mobile_card').first() or \
                     ui_images['marketplace_thumbnail']
        if mobile_card:
            ui_images['mobile_card'] = mobile_card
            
        mobile_story = get_images_by_criteria(location='mobile_story', limit=10)
        ui_images['mobile_story'] = [img.display_url for img in mobile_story]
        
        return Response({
            'success': True,
            'message': 'Images retrieved successfully',
            'data': {
                'vendor_id': vendor_id,
                'vendor_name': vendor.business_name,
                'images_by_type': images_by_type,
                'ui_images': ui_images,
                'total_images': images.count(),
            }
        })


class VendorImageTypesAPIView(APIView):
    """Get available image types and display locations"""
    permission_classes = [AllowAny]
    
    @extend_schema(
        operation_id='get_image_types',
        summary="Get image types and locations",
        description="Get all available image types and display locations for reference",
        responses={
            200: OpenApiResponse(description="Types retrieved successfully"),
        },
        tags=['Vendors']
    )
    def get(self, request):
        """Get image classification options"""
        return Response({
            'success': True,
            'data': {
                'image_types': [
                    {'value': choice[0], 'label': choice[1]} 
                    for choice in VendorImage.IMAGE_TYPES
                ],
                'display_locations': [
                    {'value': choice[0], 'label': choice[1]} 
                    for choice in VendorImage.IMAGE_DISPLAY_LOCATIONS
                ],
                'usage_guide': {
                    # Business Identity
                    'logo': 'Main business logo (transparent background preferred)',
                    'logo_dark': 'Logo for dark backgrounds/dark mode',
                    'logo_light': 'Logo for light backgrounds',
                    'favicon': 'Small icon for browser tabs (16x16, 32x32)',
                    
                    # Profile & Team
                    'profile_primary': 'Main profile picture for the business',
                    'profile_team': 'Individual team member photos',
                    'profile_owner': 'Owner/founder profile picture',
                    'profile_artist': 'Artist/designer profile for creative vendors',
                    
                    # Storefront/Marketplace
                    'storefront_hero': 'Large banner for storefront header (1920x600)',
                    'storefront_cover': 'Cover image for storefront (1200x400)',
                    'storefront_featured': 'Featured work for storefront showcase',
                    'storefront_thumbnail': 'Main thumbnail for marketplace listings (400x300)',
                    'storefront_banner': 'Promotional banner for marketing',
                    
                    # Portfolio
                    'portfolio': 'General portfolio images',
                    'portfolio_featured': 'Best work samples (featured portfolio)',
                    'portfolio_before': 'Before photos for transformations',
                    'portfolio_after': 'After photos for transformations',
                    'portfolio_360': '360-degree view images',
                    
                    # Venue Specific
                    'venue_exterior': 'Outside venue shots',
                    'venue_interior': 'Inside venue shots',
                    'venue_aerial': 'Drone/aerial photography',
                    'venue_night': 'Evening/night venue shots',
                    'venue_ceremony': 'Ceremony space setup',
                    'venue_reception': 'Reception space setup',
                    
                    # Display Locations
                    'marketplace_grid': 'Grid view in marketplace (300x300)',
                    'marketplace_list': 'List view in marketplace (200x150)',
                    'search_result': 'Search result cards (250x200)',
                    'card_small': 'Small cards (200x200)',
                    'card_medium': 'Medium cards (400x300)',
                    'card_large': 'Large cards (800x600)',
                    'storefront_header': 'Storefront page header (1200x400)',
                    'storefront_gallery': 'Storefront gallery grid',
                    'detail_hero': 'Detail page hero section (1200x500)',
                    'homepage_hero': 'Homepage hero slider (1920x800)',
                    'mobile_card': 'Mobile card view (300x200)',
                    'social_share': 'Social media sharing preview (1200x630)',
                },
                'image_contexts': [
                    {'value': choice[0], 'label': choice[1]} 
                    for choice in VendorImage.IMAGE_CONTEXTS
                ],
                'aspect_ratios': [
                    {'value': choice[0], 'label': choice[1]} 
                    for choice in VendorImage.ASPECT_RATIOS
                ],
                'recommended_sizes': {
                    'logo': '500x500 (square, transparent background)',
                    'storefront_hero': '1920x600 (16:5 ratio)',
                    'storefront_thumbnail': '400x300 (4:3 ratio)',
                    'marketplace_grid': '300x300 (square)',
                    'portfolio': '800x600 (4:3 ratio) or 1200x800',
                    'venue_exterior': '1200x800 (3:2 ratio)',
                    'social_cover': '1200x630 (1.91:1 ratio)',
                    'mobile_card': '400x250 (16:10 ratio)',
                }
            }
        })