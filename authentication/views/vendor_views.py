from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from django.db.models import Q
from ..models import Vendor, VendorCategory
from ..schemas import VendorSchema


class VendorListAPIView(APIView):
    """Public vendor listing - couples can browse vendors"""
    permission_classes = [AllowAny]
    
    @extend_schema(
        operation_id='list_vendors',
        summary="List vendors",
        description="Get a list of all active vendors with optional filtering",
        parameters=[
            OpenApiParameter(
                name='category',
                description='Filter by vendor category slug',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='city',
                description='Filter by city',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='max_price',
                description='Maximum price filter',
                required=False,
                type=float
            ),
            OpenApiParameter(
                name='radius',
                description='Service radius in miles (default: 25)',
                required=False,
                type=int
            ),
        ],
        responses={
            200: VendorSchema,
            401: OpenApiResponse(description="Authentication required"),
        },
        tags=['Vendors']
    )
    def get(self, request):
        """Get list of vendors with filtering"""
        # Get query parameters
        category_slug = request.GET.get('category')
        city = request.GET.get('city')
        max_price = request.GET.get('max_price')
        service_radius = request.GET.get('radius', 25)
        
        # Base queryset - only active, verified vendors
        vendors = Vendor.objects.filter(
            is_active=True,
            is_verified=True
        ).select_related('category')
        
        # Apply filters
        if category_slug:
            vendors = vendors.filter(category__slug=category_slug)
        
        if city:
            vendors = vendors.filter(city__icontains=city)
        
        if max_price:
            try:
                max_price = float(max_price)
                vendors = vendors.filter(
                    Q(price_range_max__lte=max_price) | Q(price_range_max__isnull=True)
                )
            except ValueError:
                pass
        
        # Limit by service radius if location provided
        user_location = request.GET.get('location')
        if user_location:
            # This would need geocoding - for now just filter by radius setting
            try:
                radius = int(service_radius)
                vendors = vendors.filter(service_radius_miles__gte=radius)
            except ValueError:
                pass
        
        # Serialize vendor data
        vendor_data = []
        for vendor in vendors[:50]:  # Limit results
            vendor_data.append({
                'id': vendor.id,
                'business_name': vendor.business_name,
                'category': {
                    'name': vendor.category.name,
                    'slug': vendor.category.slug,
                },
                'location': vendor.location_display,
                'price_range': vendor.price_range_display,
                'description': vendor.description[:200] + '...' if len(vendor.description) > 200 else vendor.description,
                'services_offered': vendor.services_offered,
                'years_in_business': vendor.years_in_business,
                'is_featured': vendor.is_featured,
                'portfolio_images': vendor.portfolio_images[:3],  # First 3 images
            })
        
        # Get categories for filtering
        categories = list(VendorCategory.objects.filter(
            is_active=True
        ).values('name', 'slug'))
        
        return Response({
            'success': True,
            'message': f'Found {len(vendor_data)} vendors',
            'data': {
                'vendors': vendor_data,
                'categories': categories,
                'total_count': vendors.count(),
            }
        })


class VendorDetailAPIView(APIView):
    """Detailed vendor information"""
    permission_classes = [AllowAny]
    
    @extend_schema(
        operation_id='get_vendor_details',
        summary="Get vendor details",
        description="Get detailed information about a specific vendor",
        responses={
            200: VendorSchema,
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Vendor not found"),
        },
        tags=['Vendors']
    )
    def get(self, request, vendor_id):
        """Get detailed vendor information"""
        try:
            vendor = Vendor.objects.select_related('category').get(
                id=vendor_id,
                is_active=True,
                is_verified=True
            )
        except Vendor.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Vendor not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        data = {
            'id': vendor.id,
            'business_name': vendor.business_name,
            'business_email': vendor.business_email,
            'business_phone': vendor.business_phone,
            'website': vendor.website,
            'category': {
                'name': vendor.category.name,
                'slug': vendor.category.slug,
            },
            'services_offered': vendor.services_offered,
            'address': vendor.address,
            'city': vendor.city,
            'state': vendor.state,
            'service_radius_miles': vendor.service_radius_miles,
            'description': vendor.description,
            'years_in_business': vendor.years_in_business,
            'insurance_verified': vendor.insurance_verified,
            'price_range_display': vendor.price_range_display,
            'pricing_structure': vendor.pricing_structure,
            'booking_lead_time_days': vendor.booking_lead_time_days,
            'max_events_per_day': vendor.max_events_per_day,
            'available_days': vendor.available_days,
            'portfolio_images': vendor.portfolio_images,
            'testimonials': vendor.testimonials,
            'is_featured': vendor.is_featured,
        }
        
        return Response({
            'success': True,
            'message': 'Vendor details retrieved successfully',
            'data': data
        })

