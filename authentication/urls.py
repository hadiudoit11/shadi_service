from django.urls import path
from . import views

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
]