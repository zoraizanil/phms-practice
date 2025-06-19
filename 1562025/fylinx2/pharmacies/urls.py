from django.urls import path
from .views import add_pharmacy_view, pharmacy_list_view, delete_pharmacy_view,get_pharmacies

urlpatterns = [
    path('add/', add_pharmacy_view, name='add_pharmacy'),
    path('list/', pharmacy_list_view, name='pharmacy_list'),
    path('delete/', delete_pharmacy_view, name='delete_pharmacy'),
    path('api/pharmacies/', get_pharmacies, name='get_pharmacies'),
]
