from django.urls import path
from . import api_views

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', api_views.login_api, name='api_login'),
    path('auth/logout/', api_views.logout_api, name='api_logout'),
    path('auth/profile/', api_views.user_profile, name='api_user_profile'),
    
    # User creation endpoints
    path('users/create-admin/', api_views.AdminCreateAPIView.as_view(), name='api_create_admin'),
    path('users/create-manager/', api_views.ManagerCreateAPIView.as_view(), name='api_create_manager'),
    path('users/create-staff/', api_views.StaffCreateAPIView.as_view(), name='api_create_staff'),
    
    # User management endpoints
    path('users/', api_views.UserListAPIView.as_view(), name='api_user_list'),
    
    # Dashboard endpoint
    path('dashboard/', api_views.dashboard_data, name='api_dashboard'),
]