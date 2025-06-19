from django.urls import path
from . import api_views

urlpatterns = [
    # Sales endpoints
    path('sales/', api_views.SaleListCreateAPIView.as_view(), name='api_sale_list_create'),
    path('sales/<int:pk>/', api_views.SaleDetailAPIView.as_view(), name='api_sale_detail'),
    
    # Sale returns endpoints
    path('sale-returns/', api_views.SaleReturnListCreateAPIView.as_view(), name='api_sale_return_list_create'),
    
    # Analytics endpoints
    path('sales/analytics/', api_views.sales_analytics, name='api_sales_analytics'),
    path('sales/summary/', api_views.sales_summary, name='api_sales_summary'),
]