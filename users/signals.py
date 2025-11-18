from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import logging
from django.db.models import ObjectDoesNotExist
import hashlib

from .models import User

from wagtail_newsletter import campaign_backends
from wagtail_newsletter.models import NewsletterRecipients

logger = logging.getLogger(__name__)

# ⚠️ Define the NAME of the NewsletterRecipients object set up in the Wagtail Admin
MAIN_RECIPIENT_NAME = "General Updates"


@receiver(post_save, sender=User)
def synchronize_subscriber_status(sender, instance, created, update_fields=None, **kwargs):
    """
    Synchronizes the user's is_subscribed_to_updates status with the
    external Mailchimp list via the Mailchimp API client.
    """
    if update_fields is not None:
        # We don't want to make an API call unless there was an update to the is_subscribed_to_updates field
        if 'is_subscribed_to_updates' not in update_fields:
            return

    # 1. Basic checks to ensure API will pass
    if not instance.email:
        return

    # Ensure the user profile changes don't trigger unnecessary updates
    if not instance.pk:
        # User not fully saved yet
        return

    try:
        # Get the DB record that holds the external list ID (e.g., Mailchimp List ID)
        recipient = NewsletterRecipients.objects.get(name=MAIN_RECIPIENT_NAME)
        mailchimp_list_id = recipient.audience

    except NewsletterRecipients.DoesNotExist:
        logger.warning(f"NewsletterRecipients named '{MAIN_RECIPIENT_NAME}' not found. Synchronization skipped.")
        return
    except ObjectDoesNotExist:
        # Catch case where recipient.audience or model is missing
        logger.error(f"Error accessing NewsletterRecipients data.")
        return

    # 2. Get the Mailchimp Backend and Client
    try:
        backend = campaign_backends.get_backend()
        mailchimp_client = backend.client  # Accesses the @cached_property client from the backend
    except Exception as e:
        logger.error(f"Failed to initialize Mailchimp backend/client: {e}")
        return

    # 3a. Define basic member info
    member_data = {
        "email_address": instance.email,
        "status": "subscribed" if instance.is_subscribed_to_updates else "unsubscribed",
        "merge_fields": {
            # Map your User fields to Mailchimp's MERGE fields (e.g., FNAME, LNAME)
            "FNAME": instance.first_name or "",
            "LNAME": instance.last_name or "",
        },
        "tags": [settings.NEWSLETTER_SEGMENT_TAG]
    }

    # 3b. Generate the required Mailchimp subscriber hash (MD5 hash of the lowercase email)
    email_lower = instance.email.lower().encode()
    subscriber_hash = hashlib.md5(email_lower).hexdigest()

    # 4. Perform the synchronization action
    try:
        if instance.is_subscribed_to_updates:
            # Add or update the member (PUT/POST operation)
            mailchimp_client.lists.set_list_member(
                list_id=mailchimp_list_id,
                subscriber_hash=subscriber_hash,
                body=member_data
            )
            logger.info(f"User {instance.email} subscribed/updated on Mailchimp list {mailchimp_list_id}.")
        else:
            # Unsubscribe the member (POST operation to update status)
            mailchimp_client.lists.update_list_member(
                list_id=mailchimp_list_id,
                subscriber_hash=subscriber_hash,
                body=member_data
            )
            logger.info(f"User {instance.email} unsubscribed from Mailchimp list {mailchimp_list_id}.")

    except Exception as e:
        # Catch specific ApiClientErrors if needed, but a generic catch works for logging
        logger.error(f"Mailchimp API sync failed for {instance.email}: {e}")