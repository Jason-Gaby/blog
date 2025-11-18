from django.contrib.auth.models import Group
from django.shortcuts import render
from django.http import Http404
from django.db import models
from django.utils import timezone

from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail_newsletter.models import NewsletterPageMixin


class NewsletterIndexPage(Page):
    # Set max_count to 1 if you only ever want one of these pages on the site
    max_count = 1

    intro = models.CharField(max_length=255)

    # Define a custom body field for the Wagtail admin
    content_panels = Page.content_panels + ["intro"]

    def get_context(self, request, *args, **kwargs):
        # Update context to include only published posts, ordered by reverse-chron
        context = super().get_context(request, *args, **kwargs)
        newsletterpages = self.get_children().live()#.order_by('-first_published_at')
        context['newsletterpages'] = newsletterpages
        return context

    # --- THE CRITICAL STEP: Override the serve method for access control ---
    def serve(self, request, *args, **kwargs):

        # 1. Check if the user is authenticated (logged in)
        if not request.user.is_authenticated:
            # If not logged in, redirect to login or raise 404/403
            raise Http404("Page not found.")

        # 2. Check if the user is staff (admin, moderator, editor)
        #    Wagtail users with access to the admin area usually have is_staff=True.
        if not request.user.is_staff:
            # Since it's an admin archive, checking is_staff is usually enough
            raise Http404("Page not found.")  # Raise 404 to obscure its existence

        # 3. If access is granted, gather the data and render the template
        context = self.get_context(request, *args, **kwargs)

        # Render the template
        return render(request, "newsletter/newsletter_index_page.html", context)


class NewsletterPage(NewsletterPageMixin, Page):
    body = RichTextField()
    date = models.DateField("Create Date", default=timezone.now)

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]

    newsletter_template = "newsletter/newsletter.html"