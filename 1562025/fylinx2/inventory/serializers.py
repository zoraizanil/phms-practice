from rest_framework import serializers
from .models import Medicine, Inventory, StockMovement
from pharmacies.models import Pharmacy


class MedicineSerializer(serializers.ModelSerializer):
    """Serializer for medicine information"""
    
    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'generic_name', 'manufacturer', 
            'description', 'dosage_form', 'strength',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InventorySerializer(serializers.ModelSerializer):
    """Serializer for inventory items"""
    medicine = MedicineSerializer(read_only=True)
    medicine_id = serializers.IntegerField(write_only=True)
    pharmacy_name = serializers.CharField(source='pharmacy.name', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Inventory
        fields = [
            'id', 'pharmacy', 'pharmacy_name', 'medicine', 'medicine_id',
            'batch_number', 'quantity', 'unit_price', 'selling_price',
            'expiry_date', 'manufacture_date', 'supplier',
            'minimum_stock_level', 'is_low_stock', 'is_expired',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        # Validate that expiry date is after manufacture date
        if attrs['expiry_date'] <= attrs['manufacture_date']:
            raise serializers.ValidationError("Expiry date must be after manufacture date")
        
        # Validate that selling price is greater than unit price
        if attrs['selling_price'] <= attrs['unit_price']:
            raise serializers.ValidationError("Selling price must be greater than unit price")
        
        return attrs
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class StockMovementSerializer(serializers.ModelSerializer):
    """Serializer for stock movements"""
    inventory_info = serializers.SerializerMethodField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = StockMovement
        fields = [
            'id', 'inventory', 'inventory_info', 'movement_type',
            'quantity', 'reference_number', 'notes',
            'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']
    
    def get_inventory_info(self, obj):
        return {
            'medicine_name': obj.inventory.medicine.name,
            'batch_number': obj.inventory.batch_number,
            'pharmacy_name': obj.inventory.pharmacy.name
        }
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class InventoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating inventory items"""
    
    class Meta:
        model = Inventory
        fields = [
            'pharmacy', 'medicine', 'batch_number', 'quantity',
            'unit_price', 'selling_price', 'expiry_date',
            'manufacture_date', 'supplier', 'minimum_stock_level'
        ]
    
    def validate(self, attrs):
        # Check if inventory item with same pharmacy, medicine, and batch already exists
        if Inventory.objects.filter(
            pharmacy=attrs['pharmacy'],
            medicine=attrs['medicine'],
            batch_number=attrs['batch_number']
        ).exists():
            raise serializers.ValidationError(
                "Inventory item with this pharmacy, medicine, and batch number already exists"
            )
        
        # Validate dates
        if attrs['expiry_date'] <= attrs['manufacture_date']:
            raise serializers.ValidationError("Expiry date must be after manufacture date")
        
        # Validate prices
        if attrs['selling_price'] <= attrs['unit_price']:
            raise serializers.ValidationError("Selling price must be greater than unit price")
        
        return attrs
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class StockAdjustmentSerializer(serializers.Serializer):
    """Serializer for stock adjustments"""
    inventory_id = serializers.IntegerField()
    adjustment_quantity = serializers.IntegerField()
    movement_type = serializers.ChoiceField(choices=StockMovement.MOVEMENT_TYPES)
    reference_number = serializers.CharField(max_length=100, required=False)
    notes = serializers.CharField(required=False)
    
    def validate_inventory_id(self, value):
        try:
            inventory = Inventory.objects.get(id=value)
            return value
        except Inventory.DoesNotExist:
            raise serializers.ValidationError("Invalid inventory ID")
    
    def validate(self, attrs):
        inventory = Inventory.objects.get(id=attrs['inventory_id'])
        adjustment_quantity = attrs['adjustment_quantity']
        
        # For OUT movements, check if sufficient stock is available
        if attrs['movement_type'] == 'OUT' and adjustment_quantity > 0:
            if inventory.quantity < adjustment_quantity:
                raise serializers.ValidationError(
                    f"Insufficient stock. Available: {inventory.quantity}, Requested: {adjustment_quantity}"
                )
        
        return attrs