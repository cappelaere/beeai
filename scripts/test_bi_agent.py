#!/usr/bin/env python3
"""
Non-interactive test for the BI agent: load config, create agent, run one prompt.
Usage (from repo root, with .env or API_URL/AUTH_TOKEN set):
  python scripts/test_bi_agent.py
  python scripts/test_bi_agent.py "Show top 5 properties by views in the last 7 days"
"""
import asyncio
import os
import sys
from pathlib import Path

# Repo root
_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# Load env before importing tools that need API_URL/AUTH_TOKEN
from dotenv import load_dotenv
load_dotenv(_REPO / ".env", override=True)


async def main() -> None:
    from agents.base import create_agent, DEFAULT_MODEL, AVAILABLE_MODELS
    from agents.registry import get_agent_config

    agent_id = "bi"
    prompt = sys.argv[1] if len(sys.argv) > 1 else "What can you help me with? List your main capabilities in one short paragraph."

    print("Loading BI agent...")
    config = get_agent_config(agent_id)
    model_id = AVAILABLE_MODELS.get(DEFAULT_MODEL, AVAILABLE_MODELS["gpt-4o"])["id"]
    agent = create_agent(config, model_id, agent_id=agent_id)
    print(f"  Agent: {config.icon} {config.name}")
    print(f"  Model: {model_id}")
    print()

    print(f"Prompt: {prompt}")
    print("-" * 60)
    try:
        result = await agent.run(prompt)
        text = result.last_message.text if result and result.last_message else str(result)
        print(text)
        print("-" * 60)
        print("OK")
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
