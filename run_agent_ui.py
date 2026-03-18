#!/usr/bin/env python
"""
Run the Agent UI (Django) with uvicorn from repo root.
Usage: python run_agent_ui.py [--port 8002] [--reload]
"""
import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
os.chdir(REPO_ROOT)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
# So uvicorn --reload subprocess finds agent_ui when cwd may differ
os.environ["PYTHONPATH"] = os.pathsep.join([str(REPO_ROOT), os.environ.get("PYTHONPATH", "")])


def main():
    parser = argparse.ArgumentParser(description="Run Agent UI with uvicorn")
    parser.add_argument("--port", type=int, default=8002, help="Port (default: 8002)")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    import uvicorn
    uvicorn.run(
        "agent_ui.agent_ui.asgi:application",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
