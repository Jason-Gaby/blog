from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

#from django import forms
from wagtail.forms import forms
from django.db import models
from modelcluster.fields import ParentalKey

from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    MultiFieldPanel,
    PublishingPanel,
)
from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    register_setting,
)
from wagtail.fields import RichTextField
from wagtail.models import (
    DraftStateMixin,
    PreviewableMixin,
    RevisionMixin,
    TranslatableMixin
)



from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.contrib.forms.panels import FormSubmissionsPanel
from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    register_setting,
)

from wagtail.snippets.models import register_snippet

@register_setting
class NavigationSettings(BaseGenericSetting):
    linkedin_url = models.URLField(verbose_name="LinkedIn URL", blank=True)
    github_url = models.URLField(verbose_name="GitHub URL", blank=True)
    mastodon_url = models.URLField(verbose_name="Mastodon URL", blank=True)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("linkedin_url"),
                FieldPanel("github_url"),
                FieldPanel("mastodon_url"),
            ],
            "Social settings",
        )
    ]


class FormField(AbstractFormField):
    page = ParentalKey('FormPage', on_delete=models.CASCADE, related_name='form_fields')


class FormPage(AbstractEmailForm):
    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    content_panels = AbstractEmailForm.content_panels + [
        FormSubmissionsPanel(),
        FieldPanel('intro'),
        InlinePanel('form_fields'),
        FieldPanel('thank_you_text'),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address'),
                FieldPanel('to_address'),
            ]),
            FieldPanel('subject'),
        ], "Email"),
    ]

    def get_form_class(self):
        form_class = super().get_form_class()

        # Honeypot
        form_class.base_fields['email_check'] = forms.CharField(
            required=False,
            label='',  # Looks legitimate to bots
            widget=forms.TextInput(attrs={
                'style': 'position:absolute;left:-9999px;width:1px;height:1px',
                'tabindex': '-1',
                'autocomplete': 'off',
                'aria-hidden': 'true'
            })
        )

        # reCAPTCHA
        form_class.base_fields['captcha'] = ReCaptchaField(
            widget=ReCaptchaV2Checkbox(),
        )

        return form_class

    def get_data_for_submission(self, form):
        """
        Returns the submission data as a dictionary, explicitly excluding
        the anti-spam fields (captcha and honeypot) from the email and log.
        """
        super().get_data_fields()
        data = super().get_data_for_submission(form)

        # Define fields to exclude from email/log
        fields_to_exclude = ['email_check', 'captcha']

        # Filter out the unwanted fields
        filtered_data = {
            name: value
            for name, value in data.items()
            if name not in fields_to_exclude
        }

        return filtered_data

    def process_form_submission(self, form):
        # Check honeypot - if filled, it's a bot (silent rejection)
        if form.cleaned_data.get('email_check'):
            # Don't save submission, don't send email, don't show error
            return None

        # If honeypot is empty and reCAPTCHA passed, process normally
        return super().process_form_submission(form)

    def send_mail(self, form):
        """
        Overrides the base send_mail method to temporarily filter fields
        and use the parent class's email generation logic.
        """
        # Define fields to exclude from the email body
        fields_to_exclude = ['email_check', 'captcha']

        # 1. Store the original form fields
        original_fields = form.fields

        # 2. Filter the fields dictionary
        filtered_fields = {
            name: field
            for name, field in original_fields.items()
            if name not in fields_to_exclude
        }

        # 3. Temporarily replace the form's fields with the filtered list
        # This is what AbstractEmailForm will iterate over to build the email body
        form.fields = filtered_fields

        try:
            # 4. Call the original AbstractEmailForm.send_mail method
            super().send_mail(form)
        finally:
            # 5. Restore the original form fields, regardless of success or failure
            # This ensures the form object remains intact for other uses.
            form.fields = original_fields


@register_snippet
class FooterText(
    DraftStateMixin,
    RevisionMixin,
    PreviewableMixin,
    TranslatableMixin,
    models.Model
):
    body = RichTextField()

    panels = [
        FieldPanel("body"),
        PublishingPanel(),
    ]

    def __str__(self):
        return "Footer text"

    def get_preview_template(self, request, mode_name):
        return "base.html"

    def get_preview_context(self, request, mode_name):
        return {"footer_text": self.body}

    class Meta(TranslatableMixin.Meta):
        verbose_name_plural = "Footer Text"