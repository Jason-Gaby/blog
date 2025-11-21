# blog/views.py (Simplified Concept)
from django.apps import apps
from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from blog.forms import FilteredCommentForm


@csrf_protect
@require_POST
def post_comment_redirect(request, next=None, using=None):
    # Assume the form is processed and you get the form object back
    data = request.POST.copy()

    ctype = data.get("content_type")
    object_pk = data.get("object_pk")
    model = apps.get_model(*ctype.split(".", 1))
    target = model._default_manager.using(None).get(pk=object_pk)
    form = FilteredCommentForm(target, data=data)

    if not form.is_valid():
        # Store form data and errors in the messages framework
        messages.error(request, form.errors['comment'][0])

        # Store the cleaned form data (the profane comment text) in the session
        request.session['comment_form_data'] = form.data
    else:
        if 'comment_form_data' in request.session:
            del request.session['comment_form_data']

    # Redirect back to the originating page immediately
    return redirect(form.data.get('next', '/'))
