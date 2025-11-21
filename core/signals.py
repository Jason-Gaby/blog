# core/signals.py (or a similar location)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.sites.models import Site as DjangoSite
from wagtail.models import Site as WagtailSite  # Use the Wagtail site model


@receiver(post_save, sender=WagtailSite)
def sync_wagtail_site_to_django_site(sender, instance, **kwargs):
    """
    Ensures that the corresponding django_site record reflects the
    hostname and port from the wagtailcore_site record.

    This is required because sites are managed on Wagtail, but some plug-ins only use the Django Site model,
    so we need to automatically make sure these tables are synced. It should only go one way, from Wagtail to Django.
    """

    # 1. Construct the full domain string
    if instance.port and instance.port not in (80, 443):
        # Include port if it's not the default HTTP/HTTPS port
        full_domain = f"{instance.hostname}:{instance.port}"
    else:
        full_domain = instance.hostname

    # 2. Get the matching Django Site object
    # WagtailSite has a foreign key relationship to the DjangoSite model.
    django_site, created = DjangoSite.objects.update_or_create(
        pk=instance.id,
        defaults={
            'domain': full_domain,
            'name': instance.site_name or full_domain
        }
    )