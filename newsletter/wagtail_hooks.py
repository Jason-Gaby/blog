from wagtail import hooks
from wagtail.admin.menu import MenuItem
from django.urls import reverse
from django.db.models import ObjectDoesNotExist

from newsletter.models import NewsletterIndexPage

class NewsletterMenuItem(MenuItem):
    def is_shown(self, request):
        # Custom code to not show the menu item if a NewsLetterIndexPage does not exist yet.
        parent_page = NewsletterIndexPage.objects.live().first()
        if parent_page:
            return True
        return False

@hooks.register('register_admin_menu_item')
def register_newsletter_page_menu_item():
    # 1. Find the parent page type you want to create the new newsletter page under.
    #    We assume the NewsletterPage is created under the site's root/Home Page (Page ID 1 or 2).
    #    A safer approach is to find the *first allowed parent* page, e.g., the Home Page.

    # --- FIND THE PARENT PAGE (The location where 'Add NewsletterPage' should start) ---
    # Get the root Page (often ID 2 in a fresh Wagtail install)
    index = 1
    parent_page = NewsletterIndexPage.objects.live().first()
    if parent_page is not None:
        index = parent_page.pk

    # 2. Construct the URL to the 'Add Child Page' view
    #    The URL format is typically: /admin/pages/add/<app_name>/<model_name>/<parent_page_id>/

    # Replace 'newsletter' and 'newsletterpage' with your actual app name and model name
    add_url = reverse('wagtailadmin_pages:add', args=['newsletter', 'newsletterpage', index])

    # 3. Create the MenuItem
    return NewsletterMenuItem(
        'New Newsletter',  # Displayed text in the menu
        add_url,  # The URL calculated above
        icon_name='mail',  # A relevant icon (e.g., mail, news)
        order=200,  # Determines placement (adjust this number)
    )