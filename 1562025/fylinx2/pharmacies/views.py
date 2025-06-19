from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import PharmacyForm
from .models import Pharmacy
from django.shortcuts import render, get_object_or_404, redirect
from django.shortcuts import render, redirect
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.shortcuts import redirect

@login_required
def add_pharmacy_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        location = request.POST.get('location')

        if name and location:
            try:
                pharmacy = Pharmacy.objects.create(
                    name=name,
                    location=location,
                    created_by=request.user,
                    is_superuser_created=request.user.is_superuser
                )
                messages.success(request, f"Pharmacy '{name}' added successfully!")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f"Pharmacy '{name}' added successfully!",
                        'pharmacy': {
                            'id': pharmacy.id,
                            'name': pharmacy.name,
                            'location': pharmacy.location,
                            'created_by': pharmacy.created_by.username
                        }
                    })
                return redirect('add_pharmacy')
            except Exception as e:
                messages.error(request, f"Error adding pharmacy: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': str(e)})
                return redirect('add_pharmacy')
        else:
            messages.error(request, "Both name and location are required.")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': "Both name and location are required."})
            return redirect('add_pharmacy')

    pharmacies = Pharmacy.objects.all()  # Get all pharmacies for the table
    return render(request, 'pharmacies/add_pharmacy.html', {'pharmacies': pharmacies})

@csrf_exempt
def get_pharmacies(request):
    print("I'm called")
    pharmacies = Pharmacy.objects.all()
    print("here is the pharmacies", pharmacies)
    data = [{"id": p.id, "name": p.name} for p in pharmacies]
    print("here is the data", data)
    return JsonResponse(data, safe=False)







@login_required
def pharmacy_list_view(request):
    # Superuser can see all, others only their created ones
    if request.user.is_superuser or request.user.role == 'ADMIN':
        pharmacies = Pharmacy.objects.all()
    else:
        pharmacies = Pharmacy.objects.filter(created_by=request.user)

    return render(request, 'pharmacies/pharmacy_list.html', {'pharmacies': pharmacies})



from django.shortcuts import get_object_or_404


# @login_required
# def delete_pharmacy_view(request, pk):
#     pharmacy = get_object_or_404(Pharmacy, pk=pk)

#     # Only creator or superuser can delete
#     if pharmacy.created_by != request.user and not request.user.is_superuser:
#         return redirect('pharmacy_list')

#     if request.method == 'POST':
#         pharmacy.delete()
#         return redirect('pharmacy_list')

#     return render(request, 'pharmacies/delete_pharmacy_confirm.html', {'pharmacy': pharmacy})

from django.shortcuts import redirect

@login_required
def delete_pharmacy_view(request):
    if request.method == 'POST':
        pk = request.POST.get("pharmacy_id")
        try:
            pharmacy = get_object_or_404(Pharmacy, pk=pk)

            # Only allow creator or superuser to delete
            if pharmacy.created_by == request.user or request.user.is_superuser:
                pharmacy_name = pharmacy.name  # Store name before deleting
                pharmacy.delete()
                messages.success(request, f"Pharmacy '{pharmacy_name}' has been deleted successfully!")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': f"Pharmacy '{pharmacy_name}' has been deleted successfully!"})
                return redirect('pharmacy_list')  # Redirect to list view instead of delete view
            else:
                messages.error(request, "You do not have permission to delete this pharmacy.")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'You do not have permission to delete this pharmacy.'})
                return redirect('pharmacy_list')
        except Exception as e:
            messages.error(request, f"Error deleting pharmacy: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            return redirect('pharmacy_list')

    # GET request – show all pharmacies
    pharmacies = Pharmacy.objects.all()
    return render(request, 'pharmacies/pharmacy_list.html', {'pharmacies': pharmacies})  # Changed template to list view


# from django.views.decorators.csrf import csrf_exempt

# # views.py
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from .models import Pharmacy

# @csrf_exempt
# def delete_pharmacy_by_id(request, pk):
#     if request.method == "POST":
#         try:
#             pharmacy = Pharmacy.objects.get(pk=pk)
#             pharmacy.delete()
#             return JsonResponse({"message": "Pharmacy deleted successfully."})
#         except Pharmacy.DoesNotExist:
#             return JsonResponse({"error": "Pharmacy not found."}, status=404)
#     return JsonResponse({"error": "Invalid request method."}, status=405)
