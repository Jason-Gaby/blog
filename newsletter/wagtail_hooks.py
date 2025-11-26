from wagtail import hooks
from wagtail.admin.menu import MenuItem
from django.urls import reverse

from newsletter.models import NewsletterIndexPage


@hooks.register('register_admin_menu_item')
def register_newsletter_page_menu_item():
    """
    Registers a custom menu item to add a new NewsletterPage under the first available
    NewsletterIndexPage.
    """

    # --- FIND THE PARENT PAGE (The location where 'Add NewsletterPage' should start) ---

    # 1. Attempt to find the first live NewsletterIndexPage to act as the parent.
    #    The .first() method returns None if no object is found, which is what we check for.
    parent_page = NewsletterIndexPage.objects.live().first()

    # 2. CRITICAL CHECK: If no parent page exists in the database, stop and return None.
    #    This prevents the Attribute Error and allows the admin to load so you can create the
    #    parent page first.
    if parent_page is None:
        return None
        # By returning nothing (None), no menu item is created, and the hook is safely ignored.

    # 3. Construct the URL to the 'Add Child Page' view
    #    The URL format is typically: /admin/pages/add/<app_name>/<model_name>/<parent_page_id>/

    # Now we know parent_page is a valid object, so accessing its pk is safe.
    add_url = reverse(
        'wagtailadmin_pages:add',
        args=['newsletter', 'newsletterpage', parent_page.pk]
    )

    # 4. Create the MenuItem
    yield MenuItem(
        'New Newsletter',  # Displayed text in the menu
        add_url,
        icon_name='mail',
        order=200,
    )