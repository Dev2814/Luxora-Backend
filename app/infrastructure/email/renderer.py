"""
Email Template Renderer

Handles rendering HTML email templates using Jinja2.
"""

import os
from typing import Dict, Any

from jinja2 import (
    Environment,
    FileSystemLoader,
    select_autoescape,
    TemplateNotFound,
    StrictUndefined
)

# ==========================================================
# TEMPLATE DIRECTORY
# ==========================================================

TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__),
    "templates"
)

# ==========================================================
# JINJA ENVIRONMENT
# ==========================================================

env = Environment(
    loader=FileSystemLoader(TEMPLATE_PATH),
    autoescape=select_autoescape(["html", "xml"]),
    cache_size=100,
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True
)

# ==========================================================
# TEMPLATE RENDER
# ==========================================================

def render_template(template_name: str, context: Dict[str, Any]) -> str:
    """
    Render HTML email template safely.
    """

    try:

        if not isinstance(context, dict):
            context = {}

        template = env.get_template(template_name)

        return template.render(**context)

    except TemplateNotFound:

        return "<h3>Email template missing</h3>"

    except Exception as e:
        print(f"Template render error: {e}")
        return "<h3>Email rendering error</h3>"