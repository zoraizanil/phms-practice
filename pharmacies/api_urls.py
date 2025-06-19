from django.urls import path
from . import api_views

urlpatterns = [
    # Pharmacy CRUD endpoints
    path('pharmacies/', api_views.PharmacyListCreateAPIView.as_view(), name='api_pharmacy_list_create'),
    path('pharmacies/<int:pk>/', api_views.PharmacyDetailAPIView.as_view(), name='api_pharmacy_detail'),
    
    # Pharmacy management endpoints
    path('pharmacies/<int:pharmacy_id>/assign-managers/', api_views.assign_managers, name='api_assign_managers'),
    path('pharmacies/<int:pharmacy_id>/managers/', api_views.pharmacy_managers, name='api_pharmacy_managers'),
    path('pharmacies/<int:pharmacy_id>/stats/', api_views.pharmacy_stats, name='api_pharmacy_stats'),
]