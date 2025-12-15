from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
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
            OpenApiParameter(
                name='sort_by',
                description='Sort by field: rating, price, name, experience, featured',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='sort_order',
                description='Sort order: asc or desc (default: asc)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='page',
                description='Page number (default: 1)',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='limit',
                description='Number of results per page (default: 12, max: 50)',
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
        """Get list of vendors with filtering, sorting and pagination"""
        # Get query parameters
        category_slug = request.GET.get('category')
        city = request.GET.get('city')
        max_price = request.GET.get('max_price')
        service_radius = request.GET.get('radius', 25)
        sort_by = request.GET.get('sort_by', 'name')
        sort_order = request.GET.get('sort_order', 'asc')
        page = int(request.GET.get('page', 1))
        limit = min(int(request.GET.get('limit', 12)), 50)  # Max 50 per page
        
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
        
        # Apply sorting
        sort_field = 'business_name'  # default
        if sort_by == 'rating':
            # Use featured status as proxy for rating until rating system is implemented
            sort_field = 'is_featured'
        elif sort_by == 'price':
            sort_field = 'price_range_min'
        elif sort_by == 'name':
            sort_field = 'business_name'
        elif sort_by == 'experience':
            sort_field = 'years_in_business'
        elif sort_by == 'featured':
            sort_field = 'is_featured'
        
        # Apply sort order
        if sort_order == 'desc':
            sort_field = f'-{sort_field}'
        
        vendors = vendors.order_by(sort_field, 'business_name')
        
        # Get total count before pagination
        total_count = vendors.count()
        
        # Apply pagination
        paginator = Paginator(vendors, limit)
        page_obj = paginator.get_page(page)
        
        # Serialize vendor data
        vendor_data = []
        for vendor in page_obj.object_list:
            vendor_data.append({
                'id': vendor.id,
                'business_name': vendor.business_name,
                'category': {
                    'name': vendor.category.name,
                    'slug': vendor.category.slug,
                },
                'location': f"{vendor.city}, {vendor.state}",
                'city': vendor.city,
                'state': vendor.state,
                'price_range_min': float(vendor.price_range_min) if vendor.price_range_min else None,
                'price_range_max': float(vendor.price_range_max) if vendor.price_range_max else None,
                'price_range_display': f"${int(vendor.price_range_min) if vendor.price_range_min else 'N/A'} - ${int(vendor.price_range_max) if vendor.price_range_max else 'N/A'}",
                'description': vendor.description[:200] + '...' if len(vendor.description) > 200 else vendor.description,
                'services_offered': vendor.services_offered,
                'years_in_business': vendor.years_in_business,
                'is_featured': vendor.is_featured,
                'rating_average': 4.5 if vendor.is_featured else 4.0,  # Placeholder until rating system
                'review_count': 12 if vendor.is_featured else 8,  # Placeholder until review system
                'website': vendor.website,
                'business_phone': vendor.business_phone,
            })
        
        # Get categories for filtering
        categories = list(VendorCategory.objects.filter(
            is_active=True
        ).values('name', 'slug'))
        
        return Response({
            'success': True,
            'message': f'Found {total_count} vendors',
            'data': {
                'results': vendor_data,  # Use 'results' to match common pagination format
                'vendors': vendor_data,  # Keep for backward compatibility
                'categories': categories,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total_count': total_count,
                    'total_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                    'next_page': page + 1 if page_obj.has_next() else None,
                    'previous_page': page - 1 if page_obj.has_previous() else None,
                }
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

