from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from ..models import Vendor
from ..permissions import IsVendorOwnerOrStaff, CanManageOwnVendor, IsVendorReadOnly


class MyVendorsAPIView(APIView):
    """List only vendors that the current user manages"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get vendors that user owns or works for"""
        user = request.user
        
        # Get vendors where user is admin
        owned_vendors = Vendor.objects.filter(admin=user, is_active=True)
        
        # Get vendors where user is staff
        staff_vendors = Vendor.objects.filter(
            vendor_users__user=user,
            vendor_users__is_active=True,
            is_active=True
        ).distinct()
        
        # Combine and remove duplicates
        all_vendors = (owned_vendors | staff_vendors).distinct()
        
        vendor_data = []
        for vendor in all_vendors:
            vendor_data.append({
                'id': vendor.id,
                'business_name': vendor.business_name,
                'role': 'owner' if vendor.admin == user else 'staff',
                'can_edit': vendor.admin == user or vendor.vendor_users.filter(
                    user=user, can_edit_vendor_info=True
                ).exists()
            })
        
        return Response({
            'success': True,
            'vendors': vendor_data,
            'count': len(vendor_data)
        })


class VendorManagementDetailAPIView(APIView):
    """Manage a specific vendor - only if you own/work for it"""
    permission_classes = [IsAuthenticated, IsVendorOwnerOrStaff]
    
    def get_object(self, vendor_id):
        vendor = get_object_or_404(Vendor, id=vendor_id)
        # Check object-level permissions
        self.check_object_permissions(self.request, vendor)
        return vendor
    
    def get(self, request, vendor_id):
        """Get vendor details - only if you manage it"""
        vendor = self.get_object(vendor_id)
        
        return Response({
            'success': True,
            'vendor': {
                'id': vendor.id,
                'business_name': vendor.business_name,
                'description': vendor.description,
                'is_owner': vendor.admin == request.user,
                'your_role': self.get_user_role(request.user, vendor)
            }
        })
    
    def put(self, request, vendor_id):
        """Update vendor - only if you own/manage it"""
        vendor = self.get_object(vendor_id)
        
        # Additional check: staff might have read but not write
        if not self.can_user_edit(request.user, vendor):
            return Response({
                'error': 'You do not have permission to edit this vendor'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Update vendor fields
        data = request.data
        if 'business_name' in data:
            vendor.business_name = data['business_name']
        if 'description' in data:
            vendor.description = data['description']
        # ... other fields
        
        vendor.save()
        
        return Response({
            'success': True,
            'message': 'Vendor updated successfully'
        })
    
    def delete(self, request, vendor_id):
        """Delete vendor - only owners can delete"""
        vendor = self.get_object(vendor_id)
        
        # Only the actual owner can delete
        if vendor.admin != request.user and not request.user.has_auth0_role('super_admin'):
            return Response({
                'error': 'Only the vendor owner can delete this vendor'
            }, status=status.HTTP_403_FORBIDDEN)
        
        vendor.is_active = False  # Soft delete
        vendor.save()
        
        return Response({
            'success': True,
            'message': 'Vendor deleted successfully'
        })
    
    def get_user_role(self, user, vendor):
        """Helper to get user's role for this vendor"""
        if vendor.admin == user:
            return 'owner'
        
        vendor_user = vendor.vendor_users.filter(user=user, is_active=True).first()
        if vendor_user:
            return vendor_user.role
        
        return None
    
    def can_user_edit(self, user, vendor):
        """Helper to check if user can edit this vendor"""
        if vendor.admin == user:
            return True
        
        return vendor.vendor_users.filter(
            user=user,
            is_active=True,
            can_edit_vendor_info=True
        ).exists()


class PublicVendorAPIView(APIView):
    """Public vendor view with read-only access"""
    permission_classes = [IsVendorReadOnly]
    
    def get(self, request, vendor_id):
        """Anyone with read:vendors can view"""
        vendor = get_object_or_404(Vendor, id=vendor_id, is_active=True, is_verified=True)
        
        return Response({
            'success': True,
            'vendor': {
                'id': vendor.id,
                'business_name': vendor.business_name,
                'description': vendor.description,
                'services_offered': vendor.services_offered,
                # Public information only
            }
        })
    
    def put(self, request, vendor_id):
        """Only vendor owner can update through this endpoint"""
        vendor = get_object_or_404(Vendor, id=vendor_id)
        
        # The IsVendorReadOnly permission will check ownership
        self.check_object_permissions(request, vendor)
        
        # Update logic here
        return Response({'success': True})


class VendorStaffAPIView(APIView):
    """Manage vendor staff members"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, vendor_id):
        """Add staff to vendor - only owner can do this"""
        vendor = get_object_or_404(Vendor, id=vendor_id)
        
        # Only vendor owner can add staff
        if vendor.admin != request.user:
            return Response({
                'error': 'Only vendor owner can add staff'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Add staff logic
        staff_email = request.data.get('staff_email')
        role = request.data.get('role', 'staff')
        can_edit = request.data.get('can_edit', False)
        
        # ... implementation
        
        return Response({
            'success': True,
            'message': f'Staff member {staff_email} added'
        })