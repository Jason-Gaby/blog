from django import template
from users.forms import SubscribeForm

register = template.Library()

@register.inclusion_tag('home/tags/subscribe_form.html', takes_context=True)
def subscribe_form(context):
    """
    Renders the SubscribeForm and makes it available in the context
    for the included template.
    """
    # The form is always unbound for display purposes
    return {
        'form': SubscribeForm(),
        'request': context['request'],
        # Pass any existing messages from the request context (useful for error feedback)
        'messages': context['messages'] if 'messages' in context else None,
    }