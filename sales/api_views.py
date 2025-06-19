from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Sale, SaleReturn
from .serializers import (
    SaleSerializer, SaleCreateSerializer,
    SaleReturnSerializer, SaleReturnCreateSerializer
)


class SaleListCreateAPIView(generics.ListCreateAPIView):
    """API endpoint for listing and creating sales"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SaleCreateSerializer
        return SaleSerializer
    
    def get_queryset(self):
        user = self.request.user
        pharmacy_id = self.request.query_params.get('pharmacy_id')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if user.is_superuser or user.role == 'ADMIN':
            queryset = Sale.objects.all()
        elif user.role == 'MANAGER':
            managed_pharmacy_ids = user.managed_pharmacies.values_list('id', flat=True)
            queryset = Sale.objects.filter(pharmacy_id__in=managed_pharmacy_ids)
        elif user.role == 'STAFF':
            if user.assigned_pharmacy:
                queryset = Sale.objects.filter(pharmacy=user.assigned_pharmacy)
            else:
                queryset = Sale.objects.none()
        else:
            queryset = Sale.objects.none()
        
        # Filter by pharmacy if specified
        if pharmacy_id:
            queryset = queryset.filter(pharmacy_id=pharmacy_id)
        
        # Filter by date range
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=end_date)
            except ValueError:
                pass
        
        return queryset.select_related('pharmacy', 'created_by').prefetch_related('items__inventory__medicine')
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            sale = serializer.save()
            return Response({
                'success': True,
                'message': 'Sale created successfully',
                'sale': SaleSerializer(sale).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class SaleDetailAPIView(generics.RetrieveAPIView):
    """API endpoint for retrieving sale details"""
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_superuser or user.role == 'ADMIN':
            return Sale.objects.all()
        elif user.role == 'MANAGER':
            managed_pharmacy_ids = user.managed_pharmacies.values_list('id', flat=True)
            return Sale.objects.filter(pharmacy_id__in=managed_pharmacy_ids)
        elif user.role == 'STAFF':
            if user.assigned_pharmacy:
                return Sale.objects.filter(pharmacy=user.assigned_pharmacy)
        
        return Sale.objects.none()


class SaleReturnListCreateAPIView(generics.ListCreateAPIView):
    """API endpoint for listing and creating sale returns"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SaleReturnCreateSerializer
        return SaleReturnSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_superuser or user.role == 'ADMIN':
            queryset = SaleReturn.objects.all()
        elif user.role == 'MANAGER':
            managed_pharmacy_ids = user.managed_pharmacies.values_list('id', flat=True)
            queryset = SaleReturn.objects.filter(original_sale__pharmacy_id__in=managed_pharmacy_ids)
        elif user.role == 'STAFF':
            if user.assigned_pharmacy:
                queryset = SaleReturn.objects.filter(original_sale__pharmacy=user.assigned_pharmacy)
            else:
                queryset = SaleReturn.objects.none()
        else:
            queryset = SaleReturn.objects.none()
        
        return queryset.select_related('original_sale', 'created_by')
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            sale_return = serializer.save()
            return Response({
                'success': True,
                'message': 'Sale return created successfully',
                'sale_return': SaleReturnSerializer(sale_return).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def sales_analytics(request):
    """Get sales analytics for user's accessible pharmacies"""
    user = request.user
    pharmacy_id = request.query_params.get('pharmacy_id')
    period = request.query_params.get('period', 'month')  # day, week, month, year
    
    # Get base queryset based on user permissions
    if user.is_superuser or user.role == 'ADMIN':
        sales_queryset = Sale.objects.all()
    elif user.role == 'MANAGER':
        managed_pharmacy_ids = user.managed_pharmacies.values_list('id', flat=True)
        sales_queryset = Sale.objects.filter(pharmacy_id__in=managed_pharmacy_ids)
    elif user.role == 'STAFF':
        if user.assigned_pharmacy:
            sales_queryset = Sale.objects.filter(pharmacy=user.assigned_pharmacy)
        else:
            sales_queryset = Sale.objects.none()
    else:
        sales_queryset = Sale.objects.none()
    
    # Filter by pharmacy if specified
    if pharmacy_id:
        sales_queryset = sales_queryset.filter(pharmacy_id=pharmacy_id)
    
    # Calculate date range based on period
    today = timezone.now().date()
    if period == 'day':
        start_date = today
    elif period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today - timedelta(days=30)
    elif period == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = today - timedelta(days=30)
    
    # Filter sales by date range
    period_sales = sales_queryset.filter(created_at__date__gte=start_date)
    
    # Calculate analytics
    analytics = {
        'total_sales': period_sales.count(),
        'total_revenue': period_sales.aggregate(
            total=Sum('total_amount')
        )['total'] or 0,
        'average_sale_amount': period_sales.aggregate(
            avg=Sum('total_amount')
        )['avg'] or 0,
        'payment_method_breakdown': {},
        'top_selling_medicines': [],
        'daily_sales': []
    }
    
    # Calculate average
    if analytics['total_sales'] > 0:
        analytics['average_sale_amount'] = analytics['total_revenue'] / analytics['total_sales']
    
    # Payment method breakdown
    payment_methods = period_sales.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    )
    for method in payment_methods:
        analytics['payment_method_breakdown'][method['payment_method']] = {
            'count': method['count'],
            'total': method['total']
        }
    
    # Top selling medicines (by quantity)
    from django.db.models import F
    top_medicines = period_sales.values(
        'items__inventory__medicine__name'
    ).annotate(
        total_quantity=Sum('items__quantity'),
        total_revenue=Sum(F('items__quantity') * F('items__unit_price'))
    ).order_by('-total_quantity')[:10]
    
    analytics['top_selling_medicines'] = list(top_medicines)
    
    # Daily sales for the period
    daily_sales = period_sales.extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    ).order_by('day')
    
    analytics['daily_sales'] = list(daily_sales)
    
    return Response({
        'success': True,
        'period': period,
        'start_date': start_date,
        'end_date': today,
        'analytics': analytics
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def sales_summary(request):
    """Get sales summary for dashboard"""
    user = request.user
    
    # Get base queryset based on user permissions
    if user.is_superuser or user.role == 'ADMIN':
        sales_queryset = Sale.objects.all()
    elif user.role == 'MANAGER':
        managed_pharmacy_ids = user.managed_pharmacies.values_list('id', flat=True)
        sales_queryset = Sale.objects.filter(pharmacy_id__in=managed_pharmacy_ids)
    elif user.role == 'STAFF':
        if user.assigned_pharmacy:
            sales_queryset = Sale.objects.filter(pharmacy=user.assigned_pharmacy)
        else:
            sales_queryset = Sale.objects.none()
    else:
        sales_queryset = Sale.objects.none()
    
    today = timezone.now().date()
    
    summary = {
        'today_sales': sales_queryset.filter(created_at__date=today).count(),
        'today_revenue': sales_queryset.filter(created_at__date=today).aggregate(
            total=Sum('total_amount')
        )['total'] or 0,
        'month_sales': sales_queryset.filter(
            created_at__date__gte=today.replace(day=1)
        ).count(),
        'month_revenue': sales_queryset.filter(
            created_at__date__gte=today.replace(day=1)
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or 0,
        'total_sales': sales_queryset.count(),
        'total_revenue': sales_queryset.aggregate(
            total=Sum('total_amount')
        )['total'] or 0,
    }
    
    return Response({
        'success': True,
        'summary': summary
    })