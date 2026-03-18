import os
import sys
from pathlib import Path

# When run from repo root, ensure outer agent_ui is on path so Django finds agent_app
_outer_agent_ui = Path(__file__).resolve().parent.parent
if str(_outer_agent_ui) not in sys.path:
    sys.path.insert(0, str(_outer_agent_ui))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_ui.agent_ui.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
