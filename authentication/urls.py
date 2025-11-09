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
    path('api/vendor-relationships/', views.VendorManagementAPIView.as_view(), name='api_vendor_management'),
]