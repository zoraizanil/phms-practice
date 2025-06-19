from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser
from pharmacies.models import Pharmacy


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile information"""
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include username and password')


class AdminCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating admin users"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(
            role='ADMIN',
            **validated_data
        )
        user.set_password(password)
        user.save()
        return user


class ManagerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating manager users"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    pharmacy_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'pharmacy_ids']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate pharmacy IDs exist
        pharmacy_ids = attrs.get('pharmacy_ids', [])
        if not pharmacy_ids:
            raise serializers.ValidationError("At least one pharmacy must be selected")
        
        existing_pharmacies = Pharmacy.objects.filter(id__in=pharmacy_ids)
        if len(existing_pharmacies) != len(pharmacy_ids):
            raise serializers.ValidationError("One or more pharmacy IDs are invalid")
        
        return attrs
    
    def create(self, validated_data):
        pharmacy_ids = validated_data.pop('pharmacy_ids')
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = CustomUser.objects.create_user(
            role='MANAGER',
            **validated_data
        )
        user.set_password(password)
        user.save()
        
        # Assign pharmacies to manager
        pharmacies = Pharmacy.objects.filter(id__in=pharmacy_ids)
        for pharmacy in pharmacies:
            pharmacy.managers.add(user)
        
        return user


class StaffCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating staff users"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    assigned_pharmacy_id = serializers.IntegerField(write_only=True, required=True)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'assigned_pharmacy_id']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate pharmacy exists
        pharmacy_id = attrs.get('assigned_pharmacy_id')
        if not Pharmacy.objects.filter(id=pharmacy_id).exists():
            raise serializers.ValidationError("Invalid pharmacy ID")
        
        return attrs
    
    def create(self, validated_data):
        pharmacy_id = validated_data.pop('assigned_pharmacy_id')
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        pharmacy = Pharmacy.objects.get(id=pharmacy_id)
        
        user = CustomUser.objects.create_user(
            role='STAFF',
            assigned_pharmacy=pharmacy,
            **validated_data
        )
        user.set_password(password)
        user.save()
        
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for user information including relationships"""
    assigned_pharmacy = serializers.SerializerMethodField()
    managed_pharmacies = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'date_joined', 'assigned_pharmacy', 'managed_pharmacies'
        ]
    
    def get_assigned_pharmacy(self, obj):
        if obj.assigned_pharmacy:
            return {
                'id': obj.assigned_pharmacy.id,
                'name': obj.assigned_pharmacy.name,
                'location': obj.assigned_pharmacy.location
            }
        return None
    
    def get_managed_pharmacies(self, obj):
        if obj.role == 'MANAGER':
            pharmacies = obj.managed_pharmacies.all()
            return [
                {
                    'id': pharmacy.id,
                    'name': pharmacy.name,
                    'location': pharmacy.location
                }
                for pharmacy in pharmacies
            ]
        return []