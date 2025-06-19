from rest_framework import serializers
from django.db import transaction
from .models import Sale, SaleItem, SaleReturn, SaleReturnItem
from inventory.models import Inventory, StockMovement


class SaleItemSerializer(serializers.ModelSerializer):
    """Serializer for sale items"""
    medicine_name = serializers.CharField(source='inventory.medicine.name', read_only=True)
    batch_number = serializers.CharField(source='inventory.batch_number', read_only=True)
    
    class Meta:
        model = SaleItem
        fields = [
            'id', 'inventory', 'medicine_name', 'batch_number',
            'quantity', 'unit_price', 'total_price'
        ]
        read_only_fields = ['id', 'total_price']


class SaleSerializer(serializers.ModelSerializer):
    """Serializer for sales"""
    items = SaleItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    pharmacy_name = serializers.CharField(source='pharmacy.name', read_only=True)
    
    class Meta:
        model = Sale
        fields = [
            'id', 'sale_number', 'pharmacy', 'pharmacy_name',
            'customer_name', 'customer_phone', 'payment_method',
            'subtotal', 'discount', 'tax', 'total_amount',
            'amount_paid', 'change_amount', 'notes',
            'created_by_name', 'created_at', 'updated_at', 'items'
        ]
        read_only_fields = [
            'id', 'sale_number', 'created_by', 'created_at', 'updated_at'
        ]


class SaleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating sales"""
    items = SaleItemSerializer(many=True, write_only=True)
    
    class Meta:
        model = Sale
        fields = [
            'pharmacy', 'customer_name', 'customer_phone',
            'payment_method', 'discount', 'tax', 'amount_paid',
            'notes', 'items'
        ]
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required")
        
        for item in value:
            inventory_id = item.get('inventory')
            quantity = item.get('quantity', 0)
            
            if not inventory_id:
                raise serializers.ValidationError("Inventory ID is required for each item")
            
            try:
                inventory = Inventory.objects.get(id=inventory_id.id if hasattr(inventory_id, 'id') else inventory_id)
                if inventory.quantity < quantity:
                    raise serializers.ValidationError(
                        f"Insufficient stock for {inventory.medicine.name}. "
                        f"Available: {inventory.quantity}, Requested: {quantity}"
                    )
            except Inventory.DoesNotExist:
                raise serializers.ValidationError(f"Invalid inventory ID: {inventory_id}")
        
        return value
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        with transaction.atomic():
            # Calculate totals
            subtotal = sum(
                item['quantity'] * item['unit_price'] 
                for item in items_data
            )
            
            discount = validated_data.get('discount', 0)
            tax = validated_data.get('tax', 0)
            total_amount = subtotal - discount + tax
            change_amount = validated_data['amount_paid'] - total_amount
            
            # Create sale
            sale = Sale.objects.create(
                subtotal=subtotal,
                total_amount=total_amount,
                change_amount=change_amount,
                created_by=self.context['request'].user,
                **validated_data
            )
            
            # Create sale items and update inventory
            for item_data in items_data:
                inventory = item_data['inventory']
                quantity = item_data['quantity']
                
                # Create sale item
                SaleItem.objects.create(
                    sale=sale,
                    **item_data
                )
                
                # Update inventory quantity
                inventory.quantity -= quantity
                inventory.save()
                
                # Create stock movement
                StockMovement.objects.create(
                    inventory=inventory,
                    movement_type='OUT',
                    quantity=-quantity,
                    reference_number=sale.sale_number,
                    notes=f"Sale to {sale.customer_name or 'Walk-in customer'}",
                    created_by=self.context['request'].user
                )
        
        return sale


class SaleReturnItemSerializer(serializers.ModelSerializer):
    """Serializer for sale return items"""
    medicine_name = serializers.CharField(source='sale_item.inventory.medicine.name', read_only=True)
    
    class Meta:
        model = SaleReturnItem
        fields = [
            'id', 'sale_item', 'medicine_name',
            'return_quantity', 'return_amount'
        ]
        read_only_fields = ['id']


class SaleReturnSerializer(serializers.ModelSerializer):
    """Serializer for sale returns"""
    items = SaleReturnItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    original_sale_number = serializers.CharField(source='original_sale.sale_number', read_only=True)
    
    class Meta:
        model = SaleReturn
        fields = [
            'id', 'return_number', 'original_sale', 'original_sale_number',
            'reason', 'return_amount', 'notes',
            'created_by_name', 'created_at', 'items'
        ]
        read_only_fields = [
            'id', 'return_number', 'created_by', 'created_at'
        ]


class SaleReturnCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating sale returns"""
    items = SaleReturnItemSerializer(many=True, write_only=True)
    
    class Meta:
        model = SaleReturn
        fields = [
            'original_sale', 'reason', 'notes', 'items'
        ]
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required")
        
        for item in value:
            sale_item_id = item.get('sale_item')
            return_quantity = item.get('return_quantity', 0)
            
            try:
                sale_item = SaleItem.objects.get(id=sale_item_id.id if hasattr(sale_item_id, 'id') else sale_item_id)
                
                # Check if return quantity is valid
                already_returned = SaleReturnItem.objects.filter(
                    sale_item=sale_item
                ).aggregate(
                    total_returned=models.Sum('return_quantity')
                )['total_returned'] or 0
                
                available_for_return = sale_item.quantity - already_returned
                
                if return_quantity > available_for_return:
                    raise serializers.ValidationError(
                        f"Cannot return {return_quantity} items. "
                        f"Available for return: {available_for_return}"
                    )
            except SaleItem.DoesNotExist:
                raise serializers.ValidationError(f"Invalid sale item ID: {sale_item_id}")
        
        return value
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        with transaction.atomic():
            # Calculate return amount
            return_amount = sum(
                item['return_quantity'] * item['sale_item'].unit_price
                for item in items_data
            )
            
            # Create sale return
            sale_return = SaleReturn.objects.create(
                return_amount=return_amount,
                created_by=self.context['request'].user,
                **validated_data
            )
            
            # Create return items and update inventory
            for item_data in items_data:
                sale_item = item_data['sale_item']
                return_quantity = item_data['return_quantity']
                return_amount = return_quantity * sale_item.unit_price
                
                # Create return item
                SaleReturnItem.objects.create(
                    sale_return=sale_return,
                    return_amount=return_amount,
                    **item_data
                )
                
                # Update inventory quantity (add back to stock)
                inventory = sale_item.inventory
                inventory.quantity += return_quantity
                inventory.save()
                
                # Create stock movement
                StockMovement.objects.create(
                    inventory=inventory,
                    movement_type='IN',
                    quantity=return_quantity,
                    reference_number=sale_return.return_number,
                    notes=f"Return from sale {sale_return.original_sale.sale_number}",
                    created_by=self.context['request'].user
                )
        
        return sale_return