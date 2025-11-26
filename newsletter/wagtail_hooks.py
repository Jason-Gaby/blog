from wagtail import hooks
from wagtail.admin.menu import MenuItem
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist

from newsletter.models import NewsletterIndexPage


@hooks.register('register_admin_menu_item')
def register_newsletter_page_menu_item():
    """
    Registers the custom menu item. Safely returns an empty list if the parent
    page is not found or if a database error occurs.
    """

    # We will assume failure until success
    menu_items = []

    try:
        # 1. Attempt to find the parent page
        parent_page = NewsletterIndexPage.objects.live().first()

        # 2. If a page is found, create the MenuItem and add it to the list
        if parent_page is not None:
            add_url = reverse(
                'wagtailadmin_pages:add',
                args=['newsletter', 'newsletterpage', parent_page.pk]
            )

            menu_items.append(
                MenuItem(
                    'New Newsletter',
                    add_url,
                    icon_name='mail',
                    order=200,
                )
            )

    # 3. Handle specific errors (like the model not being available)
    except (ObjectDoesNotExist, Exception):
        # If anything goes wrong during page fetching, we catch the exception,
        # and the function proceeds to return the empty list defined above.
        pass

    # 4. Return the list of menu items (either empty or containing the MenuItem)
    return menu_items