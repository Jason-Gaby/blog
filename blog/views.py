# blog/views.py (Simplified Concept)
from django.apps import apps
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.utils.html import escape


from django_comments import signals
from django_comments.views.comments import CommentPostBadRequest
from django_comments_xtd.models import XtdComment

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
    form = FilteredCommentForm(comment.content_object, comment=comment)



    # 3. Render your existing form template.
    return render(request, 'comments/includes/comment_form.html', {
        'form': form,
        'request': request,
        'post_submit_redirect': redirect_url,
    })




@require_POST
def post_reply_ajax(request):
    data = request.POST.copy()

    if request.user.is_authenticated:
        if not data.get('name', ''):
            data["name"] = request.user.get_full_name() or request.user.get_username()
        if not data.get('email', ''):
            data["email"] = request.user.email

    ctype_str = data.get("content_type")
    object_pk = data.get("object_pk")
    parent_id = data.get("parent")  # The parent ID is crucial for rendering the reply form later

    try:
        model = apps.get_model(*ctype_str.split(".", 1))
        target = model._default_manager.using(None).get(pk=object_pk)
    except:
        return JsonResponse({'status': 'error', 'message': 'Invalid target object.'}, status=400)

    form = FilteredCommentForm(target, data=data)

    if form.security_errors():
        return CommentPostBadRequest(
            "The comment form failed security verification: %s" % escape(str(form.security_errors())))

    if form.is_valid():
        # 1. Success: Save the comment (or let the default view handle it and redirect)
        # For simplicity, we assume you want the standard comment success handling.
        # This view should probably just perform the validation and return JSON.
        # In a production app, you might process the comment here and return the rendered comment HTML.

        # For now, return success and let the client-side redirect handle things.

        # Otherwise create the comment
        comment = form.get_comment_object(site_id=get_current_site(request).id)
        comment.ip_address = request.META.get("REMOTE_ADDR", None) or None
        if request.user.is_authenticated:
            comment.user = request.user

        # Signal that the comment is about to be saved
        responses = signals.comment_will_be_posted.send(
            sender=comment.__class__,
            comment=comment,
            request=request
        )

        for (receiver, response) in responses:
            if response is False:
                return CommentPostBadRequest(
                    "comment_will_be_posted receiver %r killed the comment" % receiver.__name__)

        # Save the comment and signal that it was saved
        comment.save()
        signals.comment_was_posted.send(
            sender=comment.__class__,
            comment=comment,
            request=request
        )

        return JsonResponse({'status': 'success', 'redirect_to': form.data.get('next', '/')})

    else:
        # 2. Failure (Profanity, etc.):
        # Render the form template with the error context directly.

        # Get the errors for the 'comment' field (where profanity check usually happens)
        comment_errors = form.errors.get('comment', [])

        # Re-render the comment form snippet with errors and original data
        rendered_form_html = render_to_string('comments/includes/comment_form.html', {
            'form': form,
            'page': target,  # Pass the target object for {% get_comment_form %}
            'request': request,
            'messages': True,  # Signal the template to display errors
            'comment_data_from_session': {'comment': form.data.get('comment', '')}  # Pass faulty data back
        }, request=request)

        # Return the errors and the re-rendered form HTML
        return JsonResponse({
            'status': 'error',
            'error_message': comment_errors[0] if comment_errors else "Form validation failed.",
            'rendered_form_html': rendered_form_html
        })