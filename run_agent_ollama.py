#!/usr/bin/env python3
"""
Run the agent using a LOCAL Ollama LLM (no outbound API calls).
Use this when OpenAI/Anthropic are blocked by a corporate proxy (405 errors).

Prerequisites:
  1. Install Ollama: https://ollama.ai
  2. Run: ollama pull llama3.1
  3. Ensure Ollama is running (ollama serve, or the Ollama app)
"""
import asyncio
import atexit
import os

import readline  # enables arrow keys, backspace, and command history for input()

from beeai_framework.agents.requirement import RequirementAgent

# Persistent command history (up/down arrow to navigate)
_HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".realtyiq_history")
try:
    readline.read_history_file(_HISTORY_FILE)
except FileNotFoundError:
    pass
readline.set_history_length(1000)
atexit.register(readline.write_history_file, _HISTORY_FILE)
from beeai_framework.backend import ChatModel
from beeai_framework.tools.think import ThinkTool

from tools import (
    list_properties,
    list_agents_summary,
    get_property_detail,
    list_property_types,
    list_asset_types,
    get_auction_types,
    get_site_detail,
    property_count_summary,
    auction_dashboard,
    auction_bidders,
    auction_total_bids,
    bid_history,
    auction_watchers,
    admin_dashboard,
    property_registration_graph,
    list_available_tools,
)
from dotenv import load_dotenv

load_dotenv(override=True)

# Local Ollama - no outbound API, avoids proxy 405
# BeeAI format: ollama:model_name (OLLAMA_API_BASE defaults to http://localhost:11434)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "ollama:llama3.1")
os.environ.setdefault("OLLAMA_API_BASE", "http://localhost:11434")

ALL_TOOLS = [
    ThinkTool(),
    list_available_tools,
    list_properties,
    list_agents_summary,
    get_property_detail,
    list_property_types,
    list_asset_types,
    get_auction_types,
    get_site_detail,
    property_count_summary,
    auction_dashboard,
    auction_bidders,
    auction_total_bids,
    bid_history,
    auction_watchers,
    admin_dashboard,
    property_registration_graph,
]


async def main() -> None:
    llm = ChatModel.from_name(OLLAMA_MODEL)
    print(f"Using local LLM: {OLLAMA_MODEL} at {os.environ.get('OLLAMA_API_BASE', 'http://localhost:11434')}")
    print("(No outbound API calls - runs entirely on localhost)\n")

    agent = RequirementAgent(
        llm=llm,
        tools=ALL_TOOLS,
        instructions=(
            "You are RealtyIQ, a read-only assistant for GSA Real Estate Sales Auctions. "
            "Use tools to fetch data. Do not request or output PII unless explicitly asked."
        ),
    )

    while True:
        prompt = input("\nRealtyIQ> ").strip()
        if prompt.lower() in {"exit", "quit"}:
            return
        result = await agent.run(prompt)
        print("\nRealtyIQ>", result.last_message.text)


if __name__ == "__main__":
    asyncio.run(main())
