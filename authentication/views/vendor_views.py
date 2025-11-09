from django.http import JsonResponse
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from django.db.models import Q, Avg, Count
from ..models import Vendor, VendorCategory, VendorUser, VendorInquiry
from .auth_views import Auth0LoginRequiredMixin
from .api_views import APIResponseMixin
from .auth0_mixins import CanManageVendorsMixin
from ..auth0_permissions import can_manage_vendors
import json


@method_decorator(csrf_exempt, name='dispatch')
class VendorListAPIView(Auth0LoginRequiredMixin, APIResponseMixin, View):
    """Public vendor listing - couples can browse vendors"""
    
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
        
        return self.success_response({
            'vendors': vendor_data,
            'categories': categories,
            'total_count': vendors.count(),
        })


@method_decorator(csrf_exempt, name='dispatch')
class VendorDetailAPIView(Auth0LoginRequiredMixin, APIResponseMixin, View):
    """Detailed vendor information"""
    
    def get(self, request, vendor_id):
        """Get detailed vendor information"""
        try:
            vendor = Vendor.objects.select_related('category').get(
                id=vendor_id,
                is_active=True,
                is_verified=True
            )
        except Vendor.DoesNotExist:
            return self.error_response("Vendor not found", status=404)
        
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
        
        return self.success_response(data)


@method_decorator(csrf_exempt, name='dispatch')
class VendorInquiryAPIView(Auth0LoginRequiredMixin, APIResponseMixin, View):
    """Send inquiries to vendors"""
    
    def post(self, request, vendor_id):
        """Send inquiry to vendor"""
        try:
            vendor = Vendor.objects.get(id=vendor_id, is_active=True, is_verified=True)
        except Vendor.DoesNotExist:
            return self.error_response("Vendor not found", status=404)
        
        try:
            data = json.loads(request.body)
            user = request.user
            
            # Validate required fields
            required_fields = ['event_date', 'event_location', 'guest_count', 'message']
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return self.error_response(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Create inquiry
            inquiry = VendorInquiry.objects.create(
                vendor=vendor,
                couple_user=user,
                event_date=data['event_date'],
                event_location=data['event_location'],
                guest_count=data['guest_count'],
                budget_range=data.get('budget_range', ''),
                message=data['message'],
                services_requested=data.get('services_requested', []),
            )
            
            # TODO: Send notification to vendor
            
            return self.success_response(
                data={'inquiry_id': inquiry.id},
                message="Inquiry sent successfully"
            )
            
        except json.JSONDecodeError:
            return self.error_response("Invalid JSON data")
        except Exception as e:
            return self.error_response(f"Failed to send inquiry: {str(e)}")


@method_decorator(csrf_exempt, name='dispatch')
class VendorManagementAPIView(CanManageVendorsMixin, Auth0LoginRequiredMixin, APIResponseMixin, View):
    """Vendor management for couples/planners - requires manage:vendors permission"""
    
    def get(self, request):
        """Get vendor management capabilities and saved vendors"""
        user = request.user
        
        # Get vendors the couple has inquired about or booked
        inquiries = VendorInquiry.objects.filter(
            couple_user=user
        ).select_related('vendor', 'vendor__category')
        
        vendor_relationships = []
        for inquiry in inquiries:
            vendor_relationships.append({
                'vendor': {
                    'id': inquiry.vendor.id,
                    'business_name': inquiry.vendor.business_name,
                    'category': inquiry.vendor.category.name,
                    'location': inquiry.vendor.location_display,
                },
                'inquiry': {
                    'id': inquiry.id,
                    'status': inquiry.status,
                    'event_date': inquiry.event_date.isoformat(),
                    'message': inquiry.message[:100] + '...' if len(inquiry.message) > 100 else inquiry.message,
                    'created_at': inquiry.created_at.isoformat(),
                    'responded_at': inquiry.responded_at.isoformat() if inquiry.responded_at else None,
                }
            })
        
        data = {
            'can_manage_vendors': can_manage_vendors(user),
            'vendor_relationships': vendor_relationships,
            'inquiry_count': inquiries.count(),
            'pending_responses': inquiries.filter(status='pending').count(),
        }
        
        return self.success_response(data)


@method_decorator(csrf_exempt, name='dispatch')
class VendorBusinessAPIView(Auth0LoginRequiredMixin, APIResponseMixin, View):
    """For vendor representatives to manage their business"""
    
    def get(self, request):
        """Get vendor businesses user represents"""
        user = request.user
        
        if not user.is_vendor_representative:
            return self.error_response("You are not a vendor representative", status=403)
        
        vendors = []
        for vendor_user in user.managed_vendors.filter(is_active=True):
            vendor = vendor_user.vendor
            vendors.append({
                'id': vendor.id,
                'business_name': vendor.business_name,
                'category': vendor.category.name,
                'role': vendor_user.role,
                'permissions': {
                    'can_edit_vendor_info': vendor_user.can_edit_vendor_info,
                    'can_manage_bookings': vendor_user.can_manage_bookings,
                    'can_respond_to_inquiries': vendor_user.can_respond_to_inquiries,
                    'can_view_analytics': vendor_user.can_view_analytics,
                },
                'inquiries_count': vendor.inquiries.filter(status='pending').count(),
            })
        
        return self.success_response({
            'managed_vendors': vendors,
            'total_vendors': len(vendors),
        })
    
    def patch(self, request, vendor_id):
        """Update vendor business information"""
        try:
            vendor = Vendor.objects.get(id=vendor_id)
            user = request.user
            
            # Check if user can manage this vendor
            if not user.can_manage_vendor(vendor):
                return self.error_response("You don't have permission to edit this vendor", status=403)
            
            data = json.loads(request.body)
            
            # Update allowed fields
            updateable_fields = [
                'business_name', 'business_email', 'business_phone', 'website',
                'description', 'services_offered', 'address', 'city', 'state',
                'zip_code', 'service_radius_miles', 'price_range_min', 'price_range_max',
                'pricing_structure', 'booking_lead_time_days', 'max_events_per_day',
                'available_days', 'portfolio_images'
            ]
            
            for field in updateable_fields:
                if field in data:
                    setattr(vendor, field, data[field])
            
            vendor.full_clean()
            vendor.save()
            
            return self.success_response(message="Vendor information updated successfully")
            
        except Vendor.DoesNotExist:
            return self.error_response("Vendor not found", status=404)
        except json.JSONDecodeError:
            return self.error_response("Invalid JSON data")
        except ValidationError as e:
            return self.error_response("Validation error", errors=e.message_dict)
        except Exception as e:
            return self.error_response(f"Update failed: {str(e)}")


@method_decorator(csrf_exempt, name='dispatch')
class VendorInquiryResponseAPIView(Auth0LoginRequiredMixin, APIResponseMixin, View):
    """For vendors to respond to inquiries"""
    
    def patch(self, request, inquiry_id):
        """Respond to vendor inquiry"""
        try:
            inquiry = VendorInquiry.objects.get(id=inquiry_id)
            user = request.user
            
            # Check if user can respond for this vendor
            vendor_user = user.managed_vendors.filter(
                vendor=inquiry.vendor,
                is_active=True,
                can_respond_to_inquiries=True
            ).first()
            
            if not vendor_user:
                return self.error_response("You don't have permission to respond to this inquiry", status=403)
            
            data = json.loads(request.body)
            
            # Update inquiry
            inquiry.vendor_response = data.get('response', '')
            inquiry.vendor_quote = data.get('quote')
            inquiry.status = data.get('status', 'responded')
            inquiry.responded_at = timezone.now()
            inquiry.save()
            
            # TODO: Send notification to couple
            
            return self.success_response(message="Response sent successfully")
            
        except VendorInquiry.DoesNotExist:
            return self.error_response("Inquiry not found", status=404)
        except json.JSONDecodeError:
            return self.error_response("Invalid JSON data")
        except Exception as e:
            return self.error_response(f"Response failed: {str(e)}")