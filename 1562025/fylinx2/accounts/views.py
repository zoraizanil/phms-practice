from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import LoginForm
from pharmacies.models import Pharmacy

# def login_view(request):
#     form = LoginForm(request.POST or None)
#     error = None

#     if request.method == 'POST':
#         if form.is_valid():
#             username = form.cleaned_data['username']
#             password = form.cleaned_data['password']
#             print(f'Username entered: {username}')
#             print(f'Password entered: {password}')
#             user = authenticate(request, username=username, password=password)

#             if user is not None:
#                 login(request, user)
#                 print(f'{username} has logged in successfully.')  
#                 return redirect('dashboard')
#             else:
#                 error = "Invalid username or password"
#                 print('Authentication failed.')  

#     return render(request, 'index.html', {'form': form, 'error': error})

# from django.contrib.auth import authenticate, login
# from django.shortcuts import render, redirect
# from django.utils.http import url_has_allowed_host_and_scheme
# from django.conf import settings

# def login_view(request):
#     form = LoginForm(request.POST or None)
#     error = None

#     if request.method == 'POST':
#         if form.is_valid():
#             username = form.cleaned_data['username']
#             password = form.cleaned_data['password']
#             print(f'Username entered: {username}')
#             print(f'Password entered: {password}')
#             user = authenticate(request, username=username, password=password)

#             if user is not None:
#                 login(request, user)
#                 print(f'{username} has logged in successfully.')  
#                 next_url = request.GET.get('next')
#                 if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
#                     return redirect(next_url)
#                 return redirect('dashboard')
#             else:
#                 error = "Invalid username or password"
#                 print('Authentication failed.')

#     return render(request, 'index.html', {'form': form, 'error': error})
from django.contrib.auth.decorators import login_required
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

# accounts/views.py
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import LoginForm

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

def login_view(request):
    error = None

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_superuser or user.role == 'ADMIN':
                    return redirect('dashboard')
                elif user.role == 'ADMIN':
                    return redirect('admin_dashboard')
                elif user.role == 'MANAGER':
                    return redirect('manager_dashboard')
                elif user.role == 'STAFF':
                    return redirect('sale_dashboard')
                else:
                    return redirect('dashboard')  # fallback
            else:
                error = "Invalid username or password"
        else:
            error = "Both fields are required"

    return render(request, 'index.html', {'error': error})


from django.contrib.auth.decorators import login_required
from django.shortcuts import render



from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages

def custom_logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login') 

from django.shortcuts import render

def home(request):
    return render(request, 'home.html')


# accounts/views.py (continued)

from .forms import AdminCreationForm, ManagerCreationForm, StaffCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from pharmacies.models import Pharmacy

User = get_user_model()

@login_required
def create_admin_view(request):
    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        print("Raw form data received:", request.POST)
        
        if form.is_valid():
            print("Cleaned form data:", form.cleaned_data)
            saved_instance = form.save()
            print("Saved instance:", saved_instance)
            print("Saved Admin Name:", getattr(saved_instance, 'name', 'N/A'))
            print("Saved Admin Email:", getattr(saved_instance, 'email', 'N/A'))
            return redirect('dashboard')
        else:
            print("Form errors:", form.errors)
    else:
        form = AdminCreationForm()
    
    return render(request, 'accounts/create_admin.html', {
        'form': form,
        'post_data': request.POST if request.method == 'POST' else None
    })



@login_required
def create_manager_view(request):
    if request.method == 'POST':
        form = ManagerCreationForm(request.POST)
        
        print("Raw form data received:", request.POST)
        
        if form.is_valid():
            print("Cleaned form data:", form.cleaned_data)
            
            saved_instance = form.save()  # Save and get saved model instance
            
            # Print saved instance data - customize fields accordingly
            print("Saved instance:", saved_instance)
            # Example: print specific fields if your Manager model has 'name' and 'email'
            print("Saved Manager Name:", getattr(saved_instance, 'name', 'N/A'))
            print("Saved Manager Email:", getattr(saved_instance, 'email', 'N/A'))
            
            return redirect('dashboard')
        else:
            print("Form errors:", form.errors)
            # Get selected pharmacies from POST data for form re-rendering
            selected_pharmacies = request.POST.getlist('pharmacies')
    else:
        form = ManagerCreationForm()
        selected_pharmacies = []
    
    pharmacies = Pharmacy.objects.all()
    return render(request, 'accounts/create_manager.html', {
        'form': form,
        'pharmacies': pharmacies,
        'selected_pharmacies': [int(pid) for pid in selected_pharmacies] if selected_pharmacies else []
    })

# @login_required
# def create_manager_view(request):
#     if request.method == 'POST':
#         form = ManagerCreationForm(request.POST)

#         print("Form data received:", request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('dashboard')
#     else:
#         form = ManagerCreationForm()
#     return render(request, 'accounts/create_manager.html', {'form': form})


@login_required
def create_staff_view(request):
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        print("Raw form data received:", request.POST)
        
        if form.is_valid():
            print("Cleaned form data:", form.cleaned_data)
            saved_instance = form.save()
            print("Saved instance:", saved_instance)
            print("Saved Staff Name:", getattr(saved_instance, 'name', 'N/A'))
            print("Saved Staff Email:", getattr(saved_instance, 'email', 'N/A'))
            return redirect('dashboard')
        else:
            print("Form errors:", form.errors)
            selected_pharmacy = request.POST.get('assigned_pharmacy')
    else:
        form = StaffCreationForm()
        selected_pharmacy = None
    
    # Get pharmacies based on user role
    if request.user.is_superuser or request.user.role == 'ADMIN':
        pharmacies = Pharmacy.objects.all()
    else:  # For managers, only show their managed pharmacies
        pharmacies = request.user.managed_pharmacies.all()
    
    return render(request, 'accounts/create_staff.html', {
        'form': form,
        'pharmacies': pharmacies,
        'selected_pharmacy': selected_pharmacy,
        'post_data': request.POST if request.method == 'POST' else None
    })



@login_required
def admin_dashboard(request):
    return render(request, 'accounts/admin_dashboard.html')

@login_required
def manager_dashboard(request):
    return render(request, 'accounts/manager_dashboard.html')

@login_required
def sale_dashboard(request):
    return render(request, 'accounts/sale_dashboard.html')
