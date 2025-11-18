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