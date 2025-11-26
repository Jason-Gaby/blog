from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(
        _("email address"),
        unique=True,  # <--- THIS IS THE CRITICAL CHANGE
        blank=False,
        null=False,
    )

    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True
    )

    is_subscribed_to_updates = models.BooleanField(
        default=True,
        verbose_name="Subscribe to Email Updates",
        help_text="Check this box to receive periodic updates and newsletters."
    )

    new_email = models.EmailField(
        _("pending email address"),
        max_length=254,
        null=True,
        blank=True,
        # This email is NOT required to be unique until it replaces the primary email.
    )
    email_verification_token = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    email_token_created_at = models.DateTimeField(
        null=True,
        blank=True
    )