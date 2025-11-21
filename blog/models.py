

from blog.badwords.blacklist import badwords

from django import forms
from django.conf import settings
from django.shortcuts import reverse
from django.utils import timezone
from django.db import models
from django.contrib.contenttypes.models import ContentType

from django_comments_xtd.moderation import moderator, SpamModerator
from django_comments_xtd.models import Comment


from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField
from wagtail.search import index
from wagtail.snippets.models import register_snippet

class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'BlogPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

class BlogTagIndexPage(Page):
    def get_context(self, request, *args, **kwargs):
        # Filter by tag
        tag = request.GET.get('tag')
        blogpages = BlogPage.objects.filter(tags__name=tag)

        # Update template context
        context = super().get_context(request, *args, **kwargs)
        context['blogpages'] = blogpages

        return context




class BlogIndexPage(Page):
    intro = models.CharField(max_length=255)
    # add the get_context method:
    def get_context(self, request):
        # Update context to include only published posts, ordered by reverse-chron
        context = super().get_context(request)
        blogpages = self.get_children().live().order_by('-first_published_at')
        context['blogpages'] = blogpages
        return context

    content_panels = Page.content_panels + ["intro"]


class BlogPage(Page):
    date = models.DateField("Post Date", default=timezone.now)
    intro = models.CharField(max_length=255)
    body = RichTextField(blank=True)
    authors = ParentalManyToManyField('blog.Author', blank=True)
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    allow_comments = models.BooleanField("allow comments", default=True)

    def main_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.image
        else:
            return None

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("allow_comments", widget=forms.CheckboxInput),
            "date",
            FieldPanel("authors", widget=forms.CheckboxSelectMultiple),
            "tags",
        ], heading="Blog information"),
        "intro", "body", "gallery_images"
    ]

    def get_absolute_url(self):
        return self.url

    def get_context(self, request, *args, **kwargs):
        # Update template context
        context = super().get_context(request, *args, **kwargs)

        # Info for handling persistent comment data
        context['comment_data_from_session'] = request.session.get('comment_form_data')
        if 'comment_form_data' in request.session:
            del request.session['comment_form_data']

        context['comment_list_custom'] = self.get_comment_list()

        return context

    def get_comment_list(self):
        # Retrieve the content type for the object (e.g., your BlogPage)
        ctype = ContentType.objects.get_for_model(BlogPage)

        comment_list = Comment.objects.filter(
            content_type_id=ctype.pk,
            object_pk=self.pk,
        ).select_related('user')  # <-- This fetches the User data efficiently

        return comment_list

class BlogPageGalleryImage(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = ["image", "caption"]


@register_snippet
class Author(models.Model):
    name = models.CharField(max_length=255)
    author_image = models.ForeignKey(
        'wagtailimages.Image', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )

    panels = ["name", "author_image"]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Authors'



class PostCommentModerator(SpamModerator):
    email_notification = True
    removal_suggestion_notification = True

    def moderate(self, comment, content_object, request):
        return super(PostCommentModerator, self).moderate(
            comment, content_object, request
        )

moderator.register(BlogPage, PostCommentModerator)