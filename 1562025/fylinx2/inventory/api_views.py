from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone

from .models import Medicine, Inventory, StockMovement
from .serializers import (
    MedicineSerializer, InventorySerializer, StockMovementSerializer,
    InventoryCreateSerializer, StockAdjustmentSerializer
)
from pharmacies.models import Pharmacy


class MedicineListCreateAPIView(generics.ListCreateAPIView):
    """API endpoint for listing and creating medicines"""
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.request.method == 'POST':
            # Only admins and managers can create medicines
            if self.request.user.role in ['ADMIN', 'MANAGER'] or self.request.user.is_superuser:
                return [permissions.IsAuthenticated()]
            return [permissions.DenyAll()]
        return [permissions.IsAuthenticated()]


class InventoryListCreateAPIView(generics.ListCreateAPIView):
    """API endpoint for listing and creating inventory items"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return InventoryCreateSerializer
        return InventorySerializer
    
    def get_queryset(self):
        user = self.request.user
        pharmacy_id = self.request.query_params.get('pharmacy_id')
        
        if user.is_superuser or user.role == 'ADMIN':
            queryset = Inventory.objects.all()
        elif user.role == 'MANAGER':
            managed_pharmacy_ids = user.managed_pharmacies.values_list('id', flat=True)
            queryset = Inventory.objects.filter(pharmacy_id__in=managed_pharmacy_ids)
        elif user.role == 'STAFF':
            if user.assigned_pharmacy:
                queryset = Inventory.objects.filter(pharmacy=user.assigned_pharmacy)
            else:
                queryset = Inventory.objects.none()
        else:
            queryset = Inventory.objects.none()
        
        # Filter by pharmacy if specified
        if pharmacy_id:
            queryset = queryset.filter(pharmacy_id=pharmacy_id)
        
        return queryset.select_related('medicine', 'pharmacy')
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            inventory = serializer.save()
            
            # Create initial stock movement
            StockMovement.objects.create(
                inventory=inventory,
                movement_type='IN',
                quantity=inventory.quantity,
                reference_number=f"INITIAL-{inventory.id}",
                notes="Initial stock entry",
                created_by=request.user
            )
            
            return Response({
                'success': True,
                'message': 'Inventory item created successfully',
                'inventory': InventorySerializer(inventory).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class InventoryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for retrieving, updating, and deleting inventory items"""
    serializer_class = InventorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_superuser or user.role == 'ADMIN':
            return Inventory.objects.all()
        elif user.role == 'MANAGER':
            managed_pharmacy_ids = user.managed_pharmacies.values_list('id', flat=True)
            return Inventory.objects.filter(pharmacy_id__in=managed_pharmacy_ids)
        elif user.role == 'STAFF':
            if user.assigned_pharmacy:
                return Inventory.objects.filter(pharmacy=user.assigned_pharmacy)
        
        return Inventory.objects.none()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def adjust_stock(request):
    """Adjust inventory stock levels"""
    serializer = StockAdjustmentSerializer(data=request.data)
    
    if serializer.is_valid():
        inventory_id = serializer.validated_data['inventory_id']
        adjustment_quantity = serializer.validated_data['adjustment_quantity']
        movement_type = serializer.validated_data['movement_type']
        reference_number = serializer.validated_data.get('reference_number', '')
        notes = serializer.validated_data.get('notes', '')
        
        inventory = get_object_or_404(Inventory, id=inventory_id)
        
        # Check permissions
        user = request.user
        if not (user.is_superuser or 
                user.role == 'ADMIN' or
                (user.role == 'MANAGER' and inventory.pharmacy in user.managed_pharmacies.all()) or
                (user.role == 'STAFF' and inventory.pharmacy == user.assigned_pharmacy)):
            return Response({
                'success': False,
                'message': 'You do not have permission to adjust this inventory'
            }, status=status.HTTP_403_FORBIDDEN)
        
        with transaction.atomic():
            # Create stock movement record
            movement_quantity = adjustment_quantity
            if movement_type == 'OUT':
                movement_quantity = -adjustment_quantity
            
            StockMovement.objects.create(
                inventory=inventory,
                movement_type=movement_type,
                quantity=movement_quantity,
                reference_number=reference_number,
                notes=notes,
                created_by=request.user
            )
            
            # Update inventory quantity
            if movement_type == 'IN':
                inventory.quantity += adjustment_quantity
            elif movement_type == 'OUT':
                inventory.quantity -= adjustment_quantity
            elif movement_type == 'ADJUSTMENT':
                inventory.quantity = adjustment_quantity
            
            inventory.save()
        
        return Response({
            'success': True,
            'message': 'Stock adjusted successfully',
            'inventory': InventorySerializer(inventory).data
        })
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def low_stock_alerts(request):
    """Get low stock alerts for user's accessible pharmacies"""
    user = request.user
    
    if user.is_superuser or user.role == 'ADMIN':
        low_stock_items = Inventory.objects.filter(quantity__lte=models.F('minimum_stock_level'))
    elif user.role == 'MANAGER':
        managed_pharmacy_ids = user.managed_pharmacies.values_list('id', flat=True)
        low_stock_items = Inventory.objects.filter(
            pharmacy_id__in=managed_pharmacy_ids,
            quantity__lte=models.F('minimum_stock_level')
        )
    elif user.role == 'STAFF':
        if user.assigned_pharmacy:
            low_stock_items = Inventory.objects.filter(
                pharmacy=user.assigned_pharmacy,
                quantity__lte=models.F('minimum_stock_level')
            )
        else:
            low_stock_items = Inventory.objects.none()
    else:
        low_stock_items = Inventory.objects.none()
    
    serializer = InventorySerializer(low_stock_items, many=True)
    
    return Response({
        'success': True,
        'low_stock_items': serializer.data,
        'count': low_stock_items.count()
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def expired_items(request):
    """Get expired items for user's accessible pharmacies"""
    user = request.user
    today = timezone.now().date()
    
    if user.is_superuser or user.role == 'ADMIN':
        expired_items = Inventory.objects.filter(expiry_date__lt=today)
    elif user.role == 'MANAGER':
        managed_pharmacy_ids = user.managed_pharmacies.values_list('id', flat=True)
        expired_items = Inventory.objects.filter(
            pharmacy_id__in=managed_pharmacy_ids,
            expiry_date__lt=today
        )
    elif user.role == 'STAFF':
        if user.assigned_pharmacy:
            expired_items = Inventory.objects.filter(
                pharmacy=user.assigned_pharmacy,
                expiry_date__lt=today
            )
        else:
            expired_items = Inventory.objects.none()
    else:
        expired_items = Inventory.objects.none()
    
    serializer = InventorySerializer(expired_items, many=True)
    
    return Response({
        'success': True,
        'expired_items': serializer.data,
        'count': expired_items.count()
    })


class StockMovementListAPIView(generics.ListAPIView):
    """API endpoint for listing stock movements"""
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        inventory_id = self.request.query_params.get('inventory_id')
        
        if user.is_superuser or user.role == 'ADMIN':
            queryset = StockMovement.objects.all()
        elif user.role == 'MANAGER':
            managed_pharmacy_ids = user.managed_pharmacies.values_list('id', flat=True)
            queryset = StockMovement.objects.filter(inventory__pharmacy_id__in=managed_pharmacy_ids)
        elif user.role == 'STAFF':
            if user.assigned_pharmacy:
                queryset = StockMovement.objects.filter(inventory__pharmacy=user.assigned_pharmacy)
            else:
                queryset = StockMovement.objects.none()
        else:
            queryset = StockMovement.objects.none()
        
        # Filter by inventory if specified
        if inventory_id:
            queryset = queryset.filter(inventory_id=inventory_id)
        
        return queryset.select_related('inventory__medicine', 'inventory__pharmacy', 'created_by')