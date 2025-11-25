# blog/views.py (Simplified Concept)
from django.apps import apps
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render, reverse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from django_comments_xtd.models import XtdComment
from django_comments_xtd.forms import XtdCommentForm
from django_comments_xtd import get_form

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


def get_reply_form_snippet(request, parent_comment_id):
    """
    Renders the comment form template, passing the context necessary
    for the {% get_comment_form... %} tag to correctly handle threading.
    """
    comment = get_object_or_404(XtdComment, pk=parent_comment_id)
    redirect_url = comment.get_absolute_url()


    # 1. If not logged in, render the login prompt template.
    if not request.user.is_authenticated:
        # 1. If not authenticated, render the login prompt template
        return render(request, 'comments/includes/login_prompt.html', {
            'request': request,
            'next_url': redirect_url,
            'post_submit_redirect': redirect_url,
        })


    # 2. Get the parent comment object and initialize the form object.
    form = XtdCommentForm(comment.content_object, comment=comment)



    # 3. Render your existing form template.
    return render(request, 'comments/includes/comment_form.html', {
        'form': form,
        'request': request,
        'post_submit_redirect': redirect_url,
    })
