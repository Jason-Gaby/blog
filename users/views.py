from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordResetView, \
    PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.views.generic.edit import FormView
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.conf import settings
from django.db import IntegrityError
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.urls.exceptions import NoReverseMatch
from django.views.generic import UpdateView

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.core.mail import send_mail

import uuid

from .forms import UserUpdateForm, UserRegisterForm, SubscribeForm, EmailChangeForm

User = get_user_model()

class CustomLoginView(LoginView):
    template_name = "registrations/login.html"

    next_page = settings.LOGIN_REDIRECT_URL

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
    template_name = "registrations/password_change.html"
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
    template_name = "registrations/password_reset_form.html"
    email_template_name = 'registrations/password_reset_email.html'
    html_email_template_name = 'registrations/password_reset_email.html'

    success_url = reverse_lazy('password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "registrations/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "registrations/password_reset_confirm.html"
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "registrations/password_reset_complete.html"

class CustomUserRegisterView(FormView, SuccessMessageMixin):
    template_name = "registrations/register.html"
    form_class = UserRegisterForm
    success_url = reverse_lazy('login')
    success_message = "Account created! Please check your email for a link to set your password and log in."

    # Method called when the submitted form data is valid
    def form_valid(self, form):
        # 1. Save the new user object
        user = form.save()
        send_account_creation_email(self.request, user)
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


def subscribe_view(request):
    url = None
    if settings.HOME_URL == "site_root":
        from wagtail.models import Site
        site = Site.find_for_request(request)
        if site:
            url = site.root_page.url
    else:
        url = settings.HOME_URL

    if request.method == 'POST':
        form = SubscribeForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            # 1. Attempt to find the user if they already exist
            try:
                user = User.objects.get(email=email)
                messages.warning(request, "A user already exists with this email. Log in to your account to update your subscription settings.")
                return redirect(url)

            except User.DoesNotExist:
                # 2. User does not exist, create a new account
                try:
                    # 💡 Auto-generate a unique username since it's required by AbstractUser.
                    # We use a UUID to ensure global uniqueness.
                    username_base = email.split('@')[0].lower()[:20]
                    unique_id = uuid.uuid4().hex[:6]
                    username = f"{username_base}_{unique_id}"

                    # Note: We don't set a password here, making the account unusable for login.
                    # The user will need to use a "Forgot Password" link to set one if they want to log in later.
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        is_subscribed_to_updates=True
                    )

                    send_account_creation_email(request, user)

                    messages.success(request, "Subscription successful! Check your email for confirmation.")
                    return redirect(url)

                except IntegrityError as e:
                    # Should only catch if the generated username was somehow not unique, though highly unlikely.
                    messages.error(request, "Error: A user already exists with that information. Please try again.")
                    return redirect(url)
                except Exception as e:
                    messages.error(request, f"An error occurred during signup: {e}")
                    return redirect(url)

        else:
            messages.error(request, "Error: The email address provided is invalid or CAPTCHA failed. Please try again.")
            return redirect(url)

    # Handle GET Requests
    else:
        form = SubscribeForm()
        return render(request, 'includes/footer.html', {'form': form})


def send_account_creation_email(request, user):
    """
    Sends an email to the new user containing a unique token for setting their password.
    """
    # 1. Generate secure reset tokens (uid and token)
    context = {
        'email': user.email,
        'domain': request.get_host(),  # Gets the domain (e.g., example.com)
        'site_name': getattr(settings, 'WAGTAIL_SITE_NAME'),
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'user': user,
        'token': default_token_generator.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http',
    }

    # 2. Render the email content (HTML or plain text)
    subject = f"Welcome to {context['site_name']}! Set up your account access."
    email_html_content = render_to_string('registrations/account_creation_email.html', context)
    email_plain_content = strip_tags(email_html_content)

    # 3. Send the email
    try:
        send_mail(
            subject,
            email_plain_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=email_html_content,
        )
    except Exception as e:
        # Log the failure but allow the user subscription process to complete
        print(f"Failed to send account creation email to {user.email}: {e}")


@login_required
def request_email_change(request):
    if request.method == 'POST':
        form = EmailChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            new_email = form.cleaned_data['new_email']
            send_email_change_confirmation_email(request.user, new_email, request)

            messages.info(
                request,
                f"A confirmation email has been sent to {new_email}. Please check your inbox to confirm the change."
            )
            return redirect('profile')  # Redirect to profile page
    else:
        form = EmailChangeForm(instance=request.user)

    return render(request, 'registrations/request_email_change.html', {'form': form})


def send_email_change_confirmation_email(user, new_email, request):
    user.email_token_created_at = timezone.now()
    user.email_verification_token = default_token_generator.make_token(user)
    user.new_email = new_email.lower()
    user.save()

    # Email content
    context = {
        'user': user,
        'domain': request.get_host(),
        'protocol': 'https' if request.is_secure() else 'http',
        'new_email': user.new_email,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': user.email_verification_token,

        'site_name': getattr(settings, 'WAGTAIL_SITE_NAME'),
    }

    email_subject = "Confirm Your Email Change"
    email_body = render_to_string('registrations/email_change_confirmation.html', context)
    email_plain_content = strip_tags(email_body)

    send_mail(
        email_subject,
        email_plain_content,
        settings.DEFAULT_FROM_EMAIL,
        [new_email],
        fail_silently=False,
        html_message=email_body,
    )


def confirm_email_change(request, pk, token, uidb64):
    # 1. Fetch the user
    user = get_object_or_404(User, pk=pk)

    # 2. Check for token match and expiration
    token_valid = default_token_generator.check_token(user, token)
    is_expired = (timezone.now() - user.email_token_created_at).days > 1

    if user.new_email and user.email_verification_token == token and token_valid and not is_expired:

        # 3. Success: Update the primary email address
        old_email = user.email
        user.email = user.new_email.lower()

        # 4. Clear temporary fields
        user.new_email = None
        user.email_verification_token = None
        user.email_token_created_at = None
        user.save()

        messages.success(
            request,
            f"Your email address has been successfully changed from {old_email} to {user.email}."
        )
        # Log the user back in if they weren't already, although typically they are.
        # login(request, user) # Optional: if you want to ensure they are logged in.

        return redirect('profile')  # Redirect to profile page
    else:
        # Failure: Token is invalid, expired, or data is missing
        messages.error(
            request,
            "The email confirmation link is invalid or has expired. Please try changing your email again."
        )
        return redirect('request_email_change')