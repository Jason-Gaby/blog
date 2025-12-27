import blog.blocks
import wagtail.fields
from django.db import migrations
import json


def fix_streamfield_json(apps, schema_editor):
    BlogPage = apps.get_model('blog', 'BlogPage')

    for page in BlogPage.objects.all():
        # Access the raw value from the database
        raw_value = page.body

        if not raw_value:
            page.body = "[]"  # Valid JSON empty list string
        elif isinstance(raw_value, str):
            try:
                json.loads(raw_value)
                # If it loads, it's already valid JSON
            except ValueError:
                # If it's old Wagtail format (which isn't strict JSON), 
                # you might need to convert it. However, usually, 
                # simply setting it to an empty list is the safest 
                # way to clear the IntegrityError if data isn't critical.
                page.body = "[]"

        page.save()


class Migration(migrations.Migration):
    dependencies = [
        ('blog', '0002_blogpage_allow_comments'),
    ]

    operations = [
        # STEP 1: Fix the data while the field is still technically a "string" type
        migrations.RunPython(fix_streamfield_json),

        # STEP 2: Now apply the schema change. 
        # SQLite will now validate the "body" and find valid JSON strings (like "[]").
        migrations.AlterField(
            model_name='blogpage',
            name='body',
            field=wagtail.fields.StreamField(
                [('text', 0), ('chart', 2)],
                block_lookup={
                    0: ('wagtail.blocks.RichTextBlock', (), {'blank': True}),
                    1: ('wagtail.blocks.ChoiceBlock', [], {'choices': blog.blocks.get_plotly_figures}),
                    2: ('wagtail.blocks.StructBlock', [[('script_selection', 1)]], {})
                },
                use_json_field=True  # Ensure this is explicitly here if not in the default
            ),
        ),
    ]