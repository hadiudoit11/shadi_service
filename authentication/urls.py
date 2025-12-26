from django.urls import path
from . import views
from .views import protected_views

app_name = 'auth'

urlpatterns = [
    # Authentication endpoints
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('callback/', views.CallbackView.as_view(), name='callback'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # User Management API
    path('api/profile/', views.UserProfileAPIView.as_view(), name='api_profile'),
    path('api/partner/', views.WeddingPartnerAPIView.as_view(), name='api_partner'),
    path('api/roles/', views.RoleManagementAPIView.as_view(), name='api_roles'),
    path('api/permissions/', views.PermissionsAPIView.as_view(), name='api_permissions'),
    path('api/wedding/', views.WeddingDataAPIView.as_view(), name='api_wedding'),
    
    # Event Management API (only include existing views)
    path('api/events/', views.EventCreationAPIView.as_view(), name='api_events'),
    path('api/guests/', views.GuestManagementAPIView.as_view(), name='api_guests'),
    path('api/schedule/', views.ScheduleManagementAPIView.as_view(), name='api_schedule'),
    path('api/analytics/', views.AnalyticsAPIView.as_view(), name='api_analytics'),
    
    # Vendor API
    path('api/vendors/', views.VendorListAPIView.as_view(), name='api_vendors'),
    path('api/vendors/<int:vendor_id>/', views.VendorDetailAPIView.as_view(), name='api_vendor_detail'),
    path('api/vendors/<int:vendor_id>/images/', views.VendorImagesAPIView.as_view(), name='api_vendor_images'),
    path('api/vendors/categories/', views.VendorCategoriesAPIView.as_view(), name='api_vendor_categories'),
    path('api/vendors/categories/<slug:category_slug>/', views.VendorCategoryDetailAPIView.as_view(), name='api_vendor_category_detail'),
    path('api/image-types/', views.VendorImageTypesAPIView.as_view(), name='api_image_types'),
    
    # Image Upload API
    path('api/upload-image/', views.ImageUploadAPIView.as_view(), name='api_upload_image'),
    
    # Protected API endpoints (Auth0 role/permission examples)
    path('api/protected/vendors/', protected_views.protected_vendors_list, name='api_protected_vendors'),
    path('api/protected/create-vendor/', protected_views.create_vendor, name='api_create_vendor'),
    path('api/protected/update-vendor/<int:vendor_id>/', protected_views.update_vendor, name='api_update_vendor'),
    path('api/protected/vendor-management/', protected_views.VendorManagementAPIView.as_view(), name='api_vendor_management'),
    path('api/protected/admin/', protected_views.AdminOnlyAPIView.as_view(), name='api_admin_only'),
    path('api/protected/wedding-planning/', protected_views.WeddingPlannerAPIView.as_view(), name='api_wedding_planning'),
    path('api/debug/permissions/', protected_views.UserPermissionsAPIView.as_view(), name='api_debug_permissions'),
]