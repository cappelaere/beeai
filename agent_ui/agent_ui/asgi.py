import os
import sys
import warnings
from pathlib import Path

# Suppress Django ASGI warning when serving static files (filterwarnings can miss it)
_original_showwarning = warnings.showwarning


def _showwarning(message, category, filename, lineno, file=None, line=None):
    msg = str(message) if message else ""
    if "StreamingHttpResponse" in msg and "synchronous iterators" in msg:
        return
    _original_showwarning(message, category, filename, lineno, file, line)


warnings.showwarning = _showwarning

# When run from repo root, ensure outer agent_ui is on path so Django finds agent_app
_outer_agent_ui = Path(__file__).resolve().parent.parent
if str(_outer_agent_ui) not in sys.path:
    sys.path.insert(0, str(_outer_agent_ui))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_ui.settings")

# Initialize Django before importing Channels
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

# Import Channels routing after Django is initialized
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from agent_app.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
