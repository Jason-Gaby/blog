import os
import importlib
import json
import plotly.utils
from django.conf import settings
from wagtail import blocks

def get_plotly_figures():
    """Scans the 'graphs' directory for python files."""
    graph_dir = os.path.join(settings.GRAPH_DIR)
    choices = []

    if not os.path.exists(graph_dir):
        return choices

    # os.walk looks through all subdirectories
    for root, dirs, files in os.walk(graph_dir):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                # Get the relative path (e.g., '2023_10_01_sales\chart')
                rel_path = os.path.relpath(os.path.join(root, file), graph_dir)

                # Convert file path to python module path (folder.file)
                module_path = rel_path.replace(os.sep, '.')[:-3]

                # Human-friendly label (Folder > File)
                label = module_path.replace('.', ' > ').replace('_', ' ').title()

                choices.append((module_path, label))

    return sorted(choices)


class PlotlyBlock(blocks.StructBlock):
    # The dropdown choices are refreshed whenever the server restarts or the code is evaluated
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