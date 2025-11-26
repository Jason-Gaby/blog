from wagtail import hooks
from wagtail.admin.menu import MenuItem
from django.urls import reverse
from django.db.models import ObjectDoesNotExist

from newsletter.models import NewsletterIndexPage


@hooks.register('register_admin_menu_item')
def register_newsletter_page_menu_item():
    # 1. Find the parent page type you want to create the new newsletter page under.
    #    We assume the NewsletterPage is created under the site's root/Home Page (Page ID 1 or 2).
    #    A safer approach is to find the *first allowed parent* page, e.g., the Home Page.

    # --- FIND THE PARENT PAGE (The location where 'Add NewsletterPage' should start) ---
    try:
        # Get the root Page (often ID 2 in a fresh Wagtail install)
        parent_page = NewsletterIndexPage.objects.live().first()
    except ObjectDoesNotExist:
        # Fallback to the Page listing if the root isn't found
        return MenuItem(
            'New Newsletter',  # Displayed text in the menu
            reverse('wagtailadmin_pages:add', args=['newsletter', 'newsletterpage', 2]),
            icon_name='mail',  # A relevant icon (e.g., mail, news)
            order=200,  # Determines placement (adjust this number)
        )

    # 2. Construct the URL to the 'Add Child Page' view
    #    The URL format is typically: /admin/pages/add/<app_name>/<model_name>/<parent_page_id>/

    # Replace 'newsletter' and 'newsletterpage' with your actual app name and model name
    add_url = reverse('wagtailadmin_pages:add', args=['newsletter', 'newsletterpage', parent_page.pk])

    # 3. Create the MenuItem
    return MenuItem(
        'New Newsletter',  # Displayed text in the menu
        add_url,  # The URL calculated above
        icon_name='mail',  # A relevant icon (e.g., mail, news)
        order=200,  # Determines placement (adjust this number)
    )