"""
Pytest bootstrap for agent_ui: path and Django setup so agent_app tests run from repo root.
Run: pytest agent_ui/agent_app/tests/ (from repo root) or pytest agent_app/tests/ (from agent_ui).
"""

import os
import sys
from pathlib import Path

_agent_ui = str(Path(__file__).resolve().parent)
_repo_root = str(Path(_agent_ui).parent)
# So "agent_ui" is the outer package (agent_ui/agent_app, agent_ui/agent_ui/...) and test collection finds agent_ui.agent_app
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)
if _agent_ui not in sys.path:
    sys.path.insert(0, _agent_ui)

# Inner config package has settings; outer agent_ui has no settings.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_ui.agent_ui.settings")

import django

django.setup()
