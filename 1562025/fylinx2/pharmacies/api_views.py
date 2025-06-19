from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Pharmacy
from .serializers import (
    PharmacySerializer, PharmacyDetailSerializer, 
    PharmacyCreateSerializer, PharmacyUpdateSerializer,
    AssignManagerSerializer
)
from accounts.models import CustomUser


class PharmacyListCreateAPIView(generics.ListCreateAPIView):
    """API endpoint for listing and creating pharmacies"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PharmacyCreateSerializer
        return PharmacySerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_superuser or user.role == 'ADMIN':
            # Admins can see all pharmacies
            return Pharmacy.objects.all()
        elif user.role == 'MANAGER':
            # Managers can see their assigned pharmacies
            return user.managed_pharmacies.all()
        elif user.role == 'STAFF':
            # Staff can see only their assigned pharmacy
            if user.assigned_pharmacy:
                return Pharmacy.objects.filter(id=user.assigned_pharmacy.id)
            return Pharmacy.objects.none()
        
        return Pharmacy.objects.none()
    
    def get_permissions(self):
        if self.request.method == 'POST':
            # Only admins and superusers can create pharmacies
            if (self.request.user.is_superuser or 
                self.request.user.role == 'ADMIN'):
                return [permissions.IsAuthenticated()]
            return [permissions.DenyAll()]
        return [permissions.IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            pharmacy = serializer.save()
            return Response({
                'success': True,
                'message': 'Pharmacy created successfully',
                'pharmacy': PharmacySerializer(pharmacy).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PharmacyDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for retrieving, updating, and deleting a specific pharmacy"""
    serializer_class = PharmacyDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_superuser or user.role == 'ADMIN':
            return Pharmacy.objects.all()
        elif user.role == 'MANAGER':
            return user.managed_pharmacies.all()
        elif user.role == 'STAFF':
            if user.assigned_pharmacy:
                return Pharmacy.objects.filter(id=user.assigned_pharmacy.id)
        
        return Pharmacy.objects.none()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PharmacyUpdateSerializer
        return PharmacyDetailSerializer
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            # Only creators, admins, and superusers can modify/delete
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]
    
    def update(self, request, *args, **kwargs):
        pharmacy = self.get_object()
        
        # Check permissions for update
        if not (request.user.is_superuser or 
                request.user.role == 'ADMIN' or 
                pharmacy.created_by == request.user):
            return Response({
                'success': False,
                'message': 'You do not have permission to update this pharmacy'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(pharmacy, data=request.data, partial=True)
        if serializer.is_valid():
            pharmacy = serializer.save()
            return Response({
                'success': True,
                'message': 'Pharmacy updated successfully',
                'pharmacy': PharmacyDetailSerializer(pharmacy).data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        pharmacy = self.get_object()
        
        # Check permissions for delete
        if not (request.user.is_superuser or 
                request.user.role == 'ADMIN' or 
                pharmacy.created_by == request.user):
            return Response({
                'success': False,
                'message': 'You do not have permission to delete this pharmacy'
            }, status=status.HTTP_403_FORBIDDEN)
        
        pharmacy_name = pharmacy.name
        pharmacy.delete()
        
        return Response({
            'success': True,
            'message': f'Pharmacy "{pharmacy_name}" deleted successfully'
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def assign_managers(request, pharmacy_id):
    """Assign managers to a pharmacy"""
    pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
    
    # Check permissions
    if not (request.user.is_superuser or 
            request.user.role == 'ADMIN' or 
            pharmacy.created_by == request.user):
        return Response({
            'success': False,
            'message': 'You do not have permission to assign managers to this pharmacy'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = AssignManagerSerializer(data=request.data)
    if serializer.is_valid():
        manager_ids = serializer.validated_data['manager_ids']
        managers = CustomUser.objects.filter(id__in=manager_ids, role='MANAGER')
        
        # Clear existing managers and assign new ones
        pharmacy.managers.clear()
        pharmacy.managers.add(*managers)
        
        return Response({
            'success': True,
            'message': 'Managers assigned successfully',
            'pharmacy': PharmacyDetailSerializer(pharmacy).data
        })
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def pharmacy_managers(request, pharmacy_id):
    """Get available managers for assignment"""
    pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
    
    # Check permissions
    if not (request.user.is_superuser or 
            request.user.role == 'ADMIN' or 
            pharmacy.created_by == request.user):
        return Response({
            'success': False,
            'message': 'You do not have permission to view this data'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get all managers
    managers = CustomUser.objects.filter(role='MANAGER')
    manager_data = [
        {
            'id': manager.id,
            'username': manager.username,
            'full_name': f"{manager.first_name} {manager.last_name}".strip(),
            'email': manager.email,
            'is_assigned': pharmacy.managers.filter(id=manager.id).exists()
        }
        for manager in managers
    ]
    
    return Response({
        'success': True,
        'managers': manager_data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def pharmacy_stats(request, pharmacy_id):
    """Get pharmacy statistics"""
    pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
    
    # Check permissions
    user = request.user
    if not (user.is_superuser or 
            user.role == 'ADMIN' or 
            pharmacy.created_by == user or
            pharmacy.managers.filter(id=user.id).exists() or
            (user.role == 'STAFF' and user.assigned_pharmacy == pharmacy)):
        return Response({
            'success': False,
            'message': 'You do not have permission to view this data'
        }, status=status.HTTP_403_FORBIDDEN)
    
    stats = {
        'total_managers': pharmacy.managers.count(),
        'total_staff': pharmacy.staff_users.count(),
        'pharmacy_info': {
            'id': pharmacy.id,
            'name': pharmacy.name,
            'location': pharmacy.location,
            'created_by': pharmacy.created_by.username
        }
    }
    
    return Response({
        'success': True,
        'stats': stats
    })