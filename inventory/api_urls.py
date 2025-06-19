from django.urls import path
from . import api_views

urlpatterns = [
    # Medicine endpoints
    path('medicines/', api_views.MedicineListCreateAPIView.as_view(), name='api_medicine_list_create'),
    
    # Inventory endpoints
    path('inventory/', api_views.InventoryListCreateAPIView.as_view(), name='api_inventory_list_create'),
    path('inventory/<int:pk>/', api_views.InventoryDetailAPIView.as_view(), name='api_inventory_detail'),
    
    # Stock management endpoints
    path('inventory/adjust-stock/', api_views.adjust_stock, name='api_adjust_stock'),
    path('inventory/low-stock/', api_views.low_stock_alerts, name='api_low_stock'),
    path('inventory/expired/', api_views.expired_items, name='api_expired_items'),
    
    # Stock movement endpoints
    path('stock-movements/', api_views.StockMovementListAPIView.as_view(), name='api_stock_movements'),
]