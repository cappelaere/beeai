#!/usr/bin/env python
"""
Run the Agent UI with uvicorn. Use this when your current directory is agent_ui/.
From repo root you can instead run: python run_agent_ui.py [--port 8002]
"""

import os
import sys
from pathlib import Path

# Repo root is parent of this file's directory
repo_root = Path(__file__).resolve().parent.parent
os.chdir(repo_root)
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

if __name__ == "__main__":
    import uvicorn

    agent_ui_dir = Path(__file__).resolve().parent  # repo_root/agent_ui
    log_config_path = agent_ui_dir / "uvicorn_log_config.yaml"

    uvicorn.run(
        "agent_ui.agent_ui.asgi:application",
        host=os.environ.get("UVICORN_HOST", "127.0.0.1"),
        port=int(os.environ.get("UVICORN_PORT", "8002")),
        reload=os.environ.get("UVICORN_RELOAD", "").lower() in ("1", "true", "yes"),
        log_config=str(log_config_path) if log_config_path.exists() else None,
    )
