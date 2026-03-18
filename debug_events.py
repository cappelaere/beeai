#!/usr/bin/env python3
"""
Debug script to see what events BeeAI framework emits during agent execution.
Run this to understand what event patterns to use for tool tracking.
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.backend import ChatModel
from beeai_framework.emitter import Emitter, EventMeta

from tools import list_properties

async def main():
    print("🔍 BeeAI Event Debugger")
    print("=" * 50)
    print("This script captures ALL events emitted during agent execution")
    print()
    
    # Track all events
    all_events = []
    tool_events = []
    
    def log_all_events(event, meta: EventMeta):
        """Log every single event"""
        event_info = {
            'path': meta.path,
            'name': meta.name,
            'creator': type(meta.creator).__name__ if meta.creator else 'Unknown',
            'event_type': type(event).__name__
        }
        all_events.append(event_info)
        
        # Check if this is tool-related
        if 'tool' in meta.path.lower() or hasattr(event, 'tool'):
            tool_info = f"🔧 TOOL EVENT: {meta.path} | {type(event).__name__}"
            if hasattr(event, 'tool'):
                tool_name = event.tool.name if hasattr(event.tool, 'name') else type(event.tool).__name__
                tool_info += f" | tool: {tool_name}"
            print(tool_info)
            tool_events.append(event_info)
    
    # Register global listener
    root = Emitter.root()
    root.on("*.*", log_all_events)
    
    print("Creating agent with tools...")
    llm = ChatModel.from_name(os.getenv("LLM_CHAT_MODEL_NAME", "anthropic:claude-3-5-sonnet-20240620"))
    agent = RequirementAgent(
        llm=llm,
        tools=[list_properties],
        instructions="You are a helpful assistant. Use tools when needed."
    )
    
    print("Running agent with a query that requires tools...")
    print()
    
    try:
        result = await agent.run("List some properties")
        print()
        print("✅ Agent completed successfully")
        print(f"Response: {result.last_message.text[:100]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    print("=" * 50)
    print(f"📊 Event Summary:")
    print(f"   Total events captured: {len(all_events)}")
    print(f"   Tool-related events: {len(tool_events)}")
    print()
    
    if tool_events:
        print("🔧 Tool Events Detected:")
        for event in tool_events:
            print(f"   - {event['path']} ({event['event_type']})")
    else:
        print("⚠️  No tool events detected!")
        print()
        print("💡 All event paths captured:")
        # Show unique event paths
        unique_paths = sorted(set(e['path'] for e in all_events))
        for path in unique_paths:
            print(f"   - {path}")
    
    print()
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
