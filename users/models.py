from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
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