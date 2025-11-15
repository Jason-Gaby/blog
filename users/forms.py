from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

# Get the active User model (Django's default or a custom one)
User = get_user_model()

class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

class UserUpdateForm(forms.ModelForm):
    """
    Form to allow users to update their core profile information.
    """

    class Meta:
        model = User
        # Define the fields the user can update.
        # NEVER include 'password' here.
        fields = ('first_name', 'last_name', 'email', 'profile_picture')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Optional: Add Tailwind/DaisyUI classes to form fields for styling
        for field in self.fields.values():
            field.widget.attrs.update({
                'placeholder': field.label
            })

def profile_update_view(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'users/profile.html', {'form': form})