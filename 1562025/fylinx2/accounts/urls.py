# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('logout/', views.custom_logout_view, name='log_out'),
    # path('home', views.home, name='home'),
    path('home-page/', views.home, name='home'),
    # User creation
    path('create-admin/', views.create_admin_view, name='create_admin'),
    path('create-manager/', views.create_manager_view, name='create_manager'),
    path('create-staff/', views.create_staff_view, name='create_staff'),

    # Role Dashboards
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('sale-dashboard/', views.sale_dashboard, name='sale_dashboard'),
]
