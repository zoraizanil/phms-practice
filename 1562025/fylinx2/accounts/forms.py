from django import forms

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from pharmacies.models import Pharmacy

class AdminCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'ADMIN'
        if commit:
            user.save()
        return user


from pharmacies.models import Pharmacy

# accounts/forms.py

class ManagerCreationForm(UserCreationForm):
    pharmacies = forms.ModelMultipleChoiceField(
        queryset=Pharmacy.objects.all(),
        required=True,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'pharmacies']

    def clean(self):
        cleaned_data = super().clean()
        print("\n=== ManagerCreationForm Clean Method ===")
        print("Cleaned data:", cleaned_data)
        
        # Validate that at least one pharmacy is selected
        pharmacies = cleaned_data.get('pharmacies')
        if not pharmacies:
            print("No pharmacies selected")
            raise forms.ValidationError("Please select at least one pharmacy")
        print("Selected pharmacies:", [p.name for p in pharmacies])
        return cleaned_data

    def save(self, commit=True):
        print("\n=== ManagerCreationForm Save Method ===")
        user = super().save(commit=False)
        user.role = 'MANAGER'
        print("Creating manager with role:", user.role)
        
        if commit:
            try:
                user.save()
                print("User saved successfully")
                pharmacies = self.cleaned_data['pharmacies']
                print("Assigning pharmacies:", [p.name for p in pharmacies])
                for pharmacy in pharmacies:
                    pharmacy.managers.add(user)
                    print(f"Added manager to pharmacy: {pharmacy.name}")
            except Exception as e:
                print("Error in save method:", str(e))
                raise
        return user


class StaffCreationForm(UserCreationForm):
    assigned_pharmacy = forms.ModelChoiceField(queryset=Pharmacy.objects.all(), required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'assigned_pharmacy']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'STAFF'
        user.assigned_pharmacy = self.cleaned_data.get('assigned_pharmacy')
        if commit:
            user.save()
        return user
