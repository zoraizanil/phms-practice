from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import CustomUser
from .serializers import (
    LoginSerializer, UserSerializer, AdminCreateSerializer,
    ManagerCreateSerializer, StaffCreateSerializer, UserDetailSerializer
)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_api(request):
    """API endpoint for user login"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        
        # Create or get token for the user
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_api(request):
    """API endpoint for user logout"""
    try:
        # Delete the user's token
        request.user.auth_token.delete()
    except:
        pass
    
    logout(request)
    return Response({
        'success': True,
        'message': 'Logout successful'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request):
    """Get current user profile"""
    serializer = UserDetailSerializer(request.user)
    return Response({
        'success': True,
        'user': serializer.data
    }, status=status.HTTP_200_OK)


class AdminCreateAPIView(generics.CreateAPIView):
    """API endpoint for creating admin users"""
    serializer_class = AdminCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        # Only superusers and admins can create other admins
        if self.request.user.is_superuser or self.request.user.role == 'ADMIN':
            return [permissions.IsAuthenticated()]
        return [permissions.DenyAll()]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'success': True,
                'message': 'Admin created successfully',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ManagerCreateAPIView(generics.CreateAPIView):
    """API endpoint for creating manager users"""
    serializer_class = ManagerCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        # Only superusers and admins can create managers
        if self.request.user.is_superuser or self.request.user.role == 'ADMIN':
            return [permissions.IsAuthenticated()]
        return [permissions.DenyAll()]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'success': True,
                'message': 'Manager created successfully',
                'user': UserDetailSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class StaffCreateAPIView(generics.CreateAPIView):
    """API endpoint for creating staff users"""
    serializer_class = StaffCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        # Superusers, admins, and managers can create staff
        if (self.request.user.is_superuser or 
            self.request.user.role in ['ADMIN', 'MANAGER']):
            return [permissions.IsAuthenticated()]
        return [permissions.DenyAll()]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'success': True,
                'message': 'Staff created successfully',
                'user': UserDetailSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserListAPIView(generics.ListAPIView):
    """API endpoint for listing users"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_superuser or user.role == 'ADMIN':
            # Admins can see all users
            return CustomUser.objects.all()
        elif user.role == 'MANAGER':
            # Managers can see staff in their pharmacies
            managed_pharmacy_ids = user.managed_pharmacies.values_list('id', flat=True)
            return CustomUser.objects.filter(
                assigned_pharmacy_id__in=managed_pharmacy_ids
            )
        else:
            # Staff can only see themselves
            return CustomUser.objects.filter(id=user.id)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_data(request):
    """Get dashboard data based on user role"""
    user = request.user
    
    if user.is_superuser or user.role == 'ADMIN':
        # Admin dashboard data
        total_pharmacies = user.created_pharmacies.count() if not user.is_superuser else None
        total_managers = CustomUser.objects.filter(role='MANAGER').count()
        total_staff = CustomUser.objects.filter(role='STAFF').count()
        
        return Response({
            'success': True,
            'role': 'ADMIN',
            'data': {
                'total_pharmacies': total_pharmacies,
                'total_managers': total_managers,
                'total_staff': total_staff,
                'permissions': ['create_pharmacy', 'create_manager', 'create_staff']
            }
        })
    
    elif user.role == 'MANAGER':
        # Manager dashboard data
        managed_pharmacies = user.managed_pharmacies.all()
        total_staff = CustomUser.objects.filter(
            assigned_pharmacy__in=managed_pharmacies
        ).count()
        
        return Response({
            'success': True,
            'role': 'MANAGER',
            'data': {
                'managed_pharmacies': [
                    {
                        'id': p.id,
                        'name': p.name,
                        'location': p.location
                    } for p in managed_pharmacies
                ],
                'total_staff': total_staff,
                'permissions': ['create_staff', 'view_pharmacy_data']
            }
        })
    
    elif user.role == 'STAFF':
        # Staff dashboard data
        assigned_pharmacy = user.assigned_pharmacy
        
        return Response({
            'success': True,
            'role': 'STAFF',
            'data': {
                'assigned_pharmacy': {
                    'id': assigned_pharmacy.id,
                    'name': assigned_pharmacy.name,
                    'location': assigned_pharmacy.location
                } if assigned_pharmacy else None,
                'permissions': ['view_sales', 'manage_inventory']
            }
        })
    
    return Response({
        'success': False,
        'message': 'Invalid user role'
    }, status=status.HTTP_400_BAD_REQUEST)