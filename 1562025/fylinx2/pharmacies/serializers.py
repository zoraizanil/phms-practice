from rest_framework import serializers
from .models import Pharmacy
from accounts.models import CustomUser


class PharmacySerializer(serializers.ModelSerializer):
    """Basic serializer for pharmacy information"""
    created_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Pharmacy
        fields = ['id', 'name', 'location', 'created_by', 'is_superuser_created']
        read_only_fields = ['id', 'created_by', 'is_superuser_created']
    
    def create(self, validated_data):
        # Set the created_by field to the current user
        validated_data['created_by'] = self.context['request'].user
        validated_data['is_superuser_created'] = self.context['request'].user.is_superuser
        return super().create(validated_data)


class PharmacyDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for pharmacy with managers and staff"""
    created_by = serializers.SerializerMethodField()
    managers = serializers.SerializerMethodField()
    staff_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Pharmacy
        fields = [
            'id', 'name', 'location', 'created_by', 
            'is_superuser_created', 'managers', 'staff_count'
        ]
    
    def get_created_by(self, obj):
        return {
            'id': obj.created_by.id,
            'username': obj.created_by.username,
            'full_name': f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        }
    
    def get_managers(self, obj):
        return [
            {
                'id': manager.id,
                'username': manager.username,
                'full_name': f"{manager.first_name} {manager.last_name}".strip(),
                'email': manager.email
            }
            for manager in obj.managers.all()
        ]
    
    def get_staff_count(self, obj):
        return obj.staff_users.count()


class PharmacyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating pharmacies"""
    
    class Meta:
        model = Pharmacy
        fields = ['name', 'location']
    
    def validate_name(self, value):
        # Check if pharmacy name already exists
        if Pharmacy.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A pharmacy with this name already exists.")
        return value
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        validated_data['is_superuser_created'] = self.context['request'].user.is_superuser
        return super().create(validated_data)


class PharmacyUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating pharmacies"""
    
    class Meta:
        model = Pharmacy
        fields = ['name', 'location']
    
    def validate_name(self, value):
        # Check if pharmacy name already exists (excluding current instance)
        if (Pharmacy.objects.filter(name__iexact=value)
            .exclude(id=self.instance.id).exists()):
            raise serializers.ValidationError("A pharmacy with this name already exists.")
        return value


class AssignManagerSerializer(serializers.Serializer):
    """Serializer for assigning managers to pharmacy"""
    manager_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )
    
    def validate_manager_ids(self, value):
        if not value:
            raise serializers.ValidationError("At least one manager must be selected.")
        
        # Validate that all IDs are valid manager users
        managers = CustomUser.objects.filter(id__in=value, role='MANAGER')
        if len(managers) != len(value):
            raise serializers.ValidationError("One or more manager IDs are invalid.")
        
        return value