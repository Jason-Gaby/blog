from django.core.exceptions import ValidationError
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

# Get the active User model (Django's default or a custom one)
User = get_user_model()

class UserRegisterForm(UserCreationForm):
    # Honeypot
    profile_check = forms.CharField(
        required=False,
        label='',  # Looks legitimate to bots
        widget=forms.TextInput(attrs={
            'style': 'position:absolute;left:-9999px;width:1px;height:1px',
            'tabindex': '-1',
            'autocomplete': 'off',
            'aria-hidden': 'true'
        })
    )

    # reCAPTCHA
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_subscribed_to_updates']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Password creation is done using an email reset later. The form does not need this fields.
        if 'password' in self.fields:
            del self.fields['password']
        if 'password1' in self.fields:
            del self.fields['password1']
        if 'password2' in self.fields:
            del self.fields['password2']

    def save(self, commit=True):
        # The parent save() tries to get password data, which causes the KeyError.
        # We replace it with standard ModelForm save() logic, which is cleaner
        # when working with passwordless creation.

        # 1. Get model field names
        model_fields = [field.name for field in self.Meta.model._meta.fields]

        # 2. Filter cleaned data to only include model fields
        data_for_creation = {
            key: value for key, value in self.cleaned_data.items()
            if key in model_fields
        }

        # 3. Create the user instance in memory
        user = self._meta.model(**data_for_creation)

        # 4. Set the password as unusable
        user.set_unusable_password()

        # 5. Commit to the database
        if commit:
            user.save()

        return user


class UserUpdateForm(forms.ModelForm):
    """
    Form to allow users to update their core profile information.
    """

    class Meta:
        model = User
        # Define the fields the user can update.
        # NEVER include 'password' here.
        fields = ('username', 'first_name', 'last_name', 'profile_picture', 'is_subscribed_to_updates')

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


class EmailChangeForm(forms.ModelForm):
    class Meta:
        model = User
        # Only expose the field that stores the requested new email
        fields = ('new_email',)
        labels = {
            'new_email': 'New Email Address',
        }

    def clean_new_email(self):
        new_email = self.cleaned_data['new_email'].lower()

        # 1. Check if the new email is already the current email
        if new_email == self.instance.email.lower():
            raise ValidationError("This is already your current email address.")

        # 2. Check if the new email is already in use by another user
        if User.objects.filter(email__iexact=new_email).exists():
            raise ValidationError("This email address is already in use by another user.")

        return new_email

class SubscribeForm(forms.Form):
    email = forms.EmailField(
        label="Email Address",
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'})
    )



