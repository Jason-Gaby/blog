from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordResetView, PasswordResetDoneView
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic.edit import FormView
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.conf import settings
from django.urls import reverse_lazy, reverse
from django.urls.exceptions import NoReverseMatch

from django.views.generic import UpdateView
from .forms import UserUpdateForm, UserRegisterForm

User = get_user_model()

class CustomLoginView(LoginView):
    template_name = "users/login.html"

    def dispatch(self, request, *args, **kwargs):
        # Custom code to get the site_root url if it exists.

        if self.next_page == "site_root":
            from wagtail.models import Site
            site = Site.find_for_request(request)
            if site:
                self.next_page = site.root_page.url
        return super().dispatch(request, *args, **kwargs)


    def form_valid(self, form):
        """
        Handles setting the session expiration based on the 'remember_me' checkbox.
        """
        # --- 1. Perform standard login ---
        # Calls the parent LoginView logic, which logs in the user and redirects.
        response = super().form_valid(form)

        # --- 2. Check the checkbox ---
        # The form data is in self.request.POST
        if self.request.POST.get('remember_me'):
            # If "Remember Me" is checked, set the session to persist
            # for the duration defined in settings (e.g., 2 weeks).
            self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        else:
            # If not checked, set the session to expire when the browser closes.
            self.request.session.set_expiry(0)

        return response


class CustomLogoutView(LogoutView):
    next_page = settings.SAFE_LOGOUT_REDIRECT

    def dispatch(self, request, *args, **kwargs):
        # Custom code to get the site_root url if it exists.

        if self.next_page == "site_root":
            from wagtail.models import Site
            site = Site.find_for_request(request)
            if site:
                self.next_page = site.root_page.url
        return super().dispatch(request, *args, **kwargs)


    def get_redirect_url(self):
        # 1. Get the path the user requested to redirect to (via hidden input 'next' or query param)
        # Note: The parent class handles fetching the redirect_field_name (default: 'next')
        next_path = self.request.GET.get(
            self.redirect_field_name,
            self.request.POST.get(self.redirect_field_name)
        )

        # If no 'next' parameter is provided at all, use the default safe page
        if not next_path:
            return self._get_next_page()

        # 2. Check the path against the protected list defined in settings.py
        for protected_path in settings.PROTECTED_URL_PATHS:
            if next_path.startswith(protected_path):
                # 3. If the path is protected, discard it and return the safe default URL
                return self._get_next_page()

                # 4. If the path is not protected, allow the redirect
        return next_path

    def _get_next_page(self):
        try:
            return reverse(self.next_page)
        except NoReverseMatch:
            return self.next_page


class CustomProfileView(LoginRequiredMixin, UpdateView):
    template_name = "users/profile.html"

    # Use the User model and the form we defined
    model = User
    form_class = UserUpdateForm

    # 🌟 KEY: Define where to redirect after a successful update 🌟
    # We redirect back to the profile page itself (or a success page)
    success_url = reverse_lazy('profile')

    def get_object(self):
        """
        Ensures the view only fetches and updates the currently logged-in user's object.
        """
        # The LoginRequiredMixin ensures self.request.user is authenticated
        return self.request.user

class CustomPasswordChangeView(PasswordChangeView):
    template_name = "users/password_change.html"
    success_url = reverse_lazy('profile')

    # Override form_valid to add a message before redirecting
    def form_valid(self, form):
        # 1. Call the parent method to change the password
        response = super().form_valid(form)

        # 2. Add the success message to be displayed on the next page (profile view)
        messages.success(self.request, "Password successfully changed!")

        # 3. Return the response (redirect to success_url/profile)
        return response

class CustomPasswordResetView(PasswordResetView):
    template_name = "users/password_reset_form.html"
    success_url = reverse_lazy('password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "users/password_reset_done.html"

class CustomUserRegisterView(FormView, SuccessMessageMixin):
    template_name = "users/register.html"
    form_class = UserRegisterForm
    success_url = reverse_lazy('login')

    # Method called when the submitted form data is valid
    def form_valid(self, form):
        # 1. Save the new user object
        form.save()

        return super().form_valid(form)


