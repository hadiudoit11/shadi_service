from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from ..models import VendorCategory
from django.db.models import Count, Q


class VendorCategoriesAPIView(APIView):
    """Get all vendor categories with vendor counts"""
    permission_classes = [AllowAny]
    
    @extend_schema(
        operation_id='list_vendor_categories',
        summary="Get vendor categories",
        description="Get all active vendor categories with vendor counts and descriptions",
        responses={
            200: OpenApiResponse(description="Categories retrieved successfully"),
        },
        tags=['Vendors']
    )
    def get(self, request):
        """Get all vendor categories"""
        
        # Get categories with vendor counts
        categories = VendorCategory.objects.filter(is_active=True).annotate(
            vendor_count=Count('vendors', filter=Q(vendors__is_verified=True, vendors__is_active=True))
        ).order_by('name')
        
        categories_data = []
        for category in categories:
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'description': category.description,
                'icon': category.icon,
                'vendor_count': category.vendor_count,
                'is_active': category.is_active,
            })
        
        return Response({
            'success': True,
            'message': 'Categories retrieved successfully',
            'data': {
                'categories': categories_data,
                'total_categories': len(categories_data),
            }
        })


class VendorCategoryDetailAPIView(APIView):
    """Get specific vendor category with vendors"""
    permission_classes = [AllowAny]
    
    @extend_schema(
        operation_id='get_vendor_category',
        summary="Get vendor category details",
        description="Get specific vendor category with list of vendors in that category",
        responses={
            200: OpenApiResponse(description="Category retrieved successfully"),
            404: OpenApiResponse(description="Category not found"),
        },
        tags=['Vendors']
    )
    def get(self, request, category_slug):
        """Get category details with vendors"""
        try:
            category = VendorCategory.objects.get(slug=category_slug, is_active=True)
        except VendorCategory.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Category not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get vendors in this category
        vendors = category.vendors.filter(is_verified=True, is_active=True).order_by('business_name')
        
        vendors_data = []
        for vendor in vendors:
            vendors_data.append({
                'id': vendor.id,
                'business_name': vendor.business_name,
                'description': vendor.description[:200] + '...' if len(vendor.description) > 200 else vendor.description,
                'city': vendor.city,
                'state': vendor.state,
                'price_range_min': float(vendor.price_range_min) if vendor.price_range_min else None,
                'price_range_max': float(vendor.price_range_max) if vendor.price_range_max else None,
                'pricing_structure': vendor.pricing_structure,
                'website': vendor.website,
                'rating_average': vendor.rating_average,
                'review_count': vendor.review_count,
                'is_featured': vendor.is_featured,
            })
        
        return Response({
            'success': True,
            'message': 'Category retrieved successfully',
            'data': {
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'icon': category.icon,
                    'vendor_count': len(vendors_data),
                },
                'vendors': vendors_data,
                'total_vendors': len(vendors_data),
            }
        })