import os
import importlib
import json
import plotly.utils
from django.conf import settings
from wagtail import blocks

def get_plotly_figures():
    """Scans the 'graphs' directory for python files."""
    graph_dir = settings.GRAPH_DIR
    module_root = settings.CONTENT_ROOT_DIR
    choices = []

    if not os.path.exists(graph_dir):
        return choices

    # os.walk looks through all subdirectories
    for root, dirs, files in os.walk(graph_dir):
        for file in files:
            if file.endswith(".py") and os.path.basename(root) == settings.GRAPH_DIR_NAME and file != "__init__.py":
                # Get the relative path (e.g., '2023_10_01_sales\chart')
                rel_path = os.path.relpath(os.path.join(root, file), module_root)

                # Convert file path to python module path (folder.file)
                module_path = rel_path.replace(os.sep, '.').replace(".py", "")

                # Human-friendly label (Folder > File)
                label = ""
                module_list = module_path.split(".")
                for i, module in enumerate(module_list):
                    if module.startswith("date_"):
                        label = module.replace("date_", "").replace('_', '-').title()
                    if i == len(module_list) - 1:
                        label = label + " > " + module.replace('_', ' ').title()

                choices.append((module_path, label))

    return sorted(choices)


class PlotlyBlock(blocks.StructBlock):
    # The dropdown choices are refreshed whenever the server restarts or the code is evaluated
    get_plotly_figures()
    script_selection = blocks.ChoiceBlock(choices=get_plotly_figures)

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)

        context['block_id'] = value.id if hasattr(value, 'id') else id(value)
        script_name = value['script_selection']

        try:
            # Dynamically import the selected script
            module = importlib.import_module(script_name)
            if settings.DEBUG:
                importlib.reload(module)

            # Run the standardized function
            fig = module.generate_fig()

            context['chart_json'] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            context['error'] = None
        except Exception as e:
            context['chart_json'] = None
            context['error'] = str(e)

        return context

    class Meta:
        template = "blocks/plotly_chart.html"
        icon = "code"


class DashBlock(blocks.StructBlock):
    url_suffix = blocks.CharBlock(
        help_text=f"Enter the app suffix only (e.g., 'app1/'). Base URL {settings.DASH_APP_BASE_URL} is added automatically.",
        label="App Path"
    )
    title = blocks.CharBlock(required=False, help_text="For accessibility/screen readers")
    height = blocks.IntegerBlock(default=600, help_text="Height in pixels")

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        # Add the setting to the context so it's available in the template
        context['url_prefix'] = settings.DASH_APP_BASE_URL
        return context

    class Meta:
        template = "blocks/dash_app.html"
        icon = "code"
        label = "Dash Dashboard"