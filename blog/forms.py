from django.core.exceptions import ValidationError
from django_comments_xtd.forms import XtdCommentForm
from blog.badwords.blacklist import badwords, domains

import re

class FilteredCommentForm(XtdCommentForm):
    def clean_comment(self):
        comment = self.cleaned_data.get('comment')
        content_lower = comment.lower()

        # 1. Crude Language Filtering
        for badword in badwords:
            pattern = re.compile(r'\b' + re.escape(badword.lower()) + r'\b')
            # Search the entire lower-cased comment content
            if pattern.search(content_lower):
                # Raise the error if a whole word match is found
                raise ValidationError(
                    f"Unable to post comment. Your comment uses the unallowed word: {badword}."
                )

        # 2. Email ban list
        if self.data['email'] in domains:
            raise ValidationError("User with this email cannot post comments.")

        return comment