import argparse
import asyncio
import atexit
import logging
import os
import sys
from pathlib import Path

import readline  # enables arrow keys, backspace, and command history for input()

logger = logging.getLogger(__name__)

# Persistent command history (up/down arrow to navigate)
_HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".realtyiq_history")
try:
    readline.read_history_file(_HISTORY_FILE)
except FileNotFoundError:
    pass
readline.set_history_length(1000)
atexit.register(readline.write_history_file, _HISTORY_FILE)

from dotenv import load_dotenv
load_dotenv(override=True)  # override=True so .env wins over stale shell vars

# Add agents directory to path
_AGENTS_DIR = Path(__file__).parent / "agents"
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

# Import multi-agent system
from agents.base import create_agent, AVAILABLE_MODELS, get_all_model_keys, DEFAULT_MODEL
from agents.registry import get_all_agent_ids, get_agent_config, get_default_agent_id

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="GRES Multi-Agent CLI")
    parser.add_argument(
        "--agent",
        choices=get_all_agent_ids(),
        default=get_default_agent_id(),
        help=f"Select agent to use (default: {get_default_agent_id()})"
    )
    parser.add_argument(
        "--model",
        choices=get_all_model_keys(),  # Import from agents/base.py - single source of truth
        default=DEFAULT_MODEL,
        help=f"Select Claude model (default: {DEFAULT_MODEL})"
    )
    return parser.parse_args()


async def main() -> None:
    from observability import trace_agent_run, is_enabled
    
    # Parse command line arguments
    args = parse_args()
    
    # Get agent configuration from registry
    agent_config = get_agent_config(args.agent)
    model_info = AVAILABLE_MODELS[args.model]
    model_id = model_info["id"]
    
    # Display agent and model info
    print("=" * 70)
    print(f"Agent: {agent_config.icon} {agent_config.name}")
    print(f"Model: {model_info['name']}")
    print(f"Description: {agent_config.description}")
    print("=" * 70)
    print()
    
    if is_enabled():
        print("✓ Langfuse observability enabled")
        print(f"  Dashboard: {os.getenv('OBSERVABILITY_DASHBOARD')}")
        print()
    
    # Create agent (with SKILLS.md automatically loaded)
    agent = create_agent(agent_config, model_id, agent_id=args.agent)
    
    # Store model name for logging
    llm_name = model_info["name"]

    session_id = f"cli_session_{int(asyncio.get_event_loop().time())}"
    
    # Set up tool tracking for Langfuse
    if is_enabled():
        from beeai_framework.emitter import EventMeta, Emitter
        
        tool_calls_logged = []
        
        def on_all_events(event, meta: EventMeta):
            """Capture all events and filter for tool-related ones"""
            # Tool events have paths like: "tool.custom.list_properties.start"
            # Only capture "tool.*" to avoid duplicates from "run.tool.*"
            
            path = meta.path
            
            # Only capture non-run tool events
            if not path.startswith('tool.'):
                return
            
            # Skip final_answer pseudo-tool
            if 'final_answer' in path:
                return
            
            # Extract tool name from path: "tool.custom.TOOLNAME.event"
            path_parts = path.split('.')
            try:
                if len(path_parts) >= 4 and path_parts[0] == 'tool' and path_parts[1] == 'custom':
                    tool_name = path_parts[2]
                else:
                    return
            except (ValueError, IndexError):
                return
            
            # Handle tool start event
            if meta.name == 'start':
                try:
                    tool_input = event.input if hasattr(event, 'input') else {}
                    print(f"  🔧 {tool_name}...")
                    tool_calls_logged.append({
                        'name': tool_name,
                        'input': tool_input,
                        'start_time': asyncio.get_event_loop().time()
                    })
                except Exception as e:
                    logger.debug("Failed to log tool start for %s: %s", tool_name, e)
            
            # Handle tool success event
            elif meta.name == 'success':
                try:
                    tool_output = event.output if hasattr(event, 'output') else None
                    
                    for call in tool_calls_logged:
                        if call['name'] == tool_name and 'output' not in call:
                            call['output'] = tool_output
                            call['end_time'] = asyncio.get_event_loop().time()
                            elapsed = int((call['end_time'] - call['start_time']) * 1000)
                            print(f"  ✓ {tool_name} ({elapsed}ms)")
                            break
                except Exception as e:
                    logger.debug("Failed to log tool success for %s: %s", tool_name, e)
        
        # Register global wildcard listener to capture all events
        root = Emitter.root()
        root.on("*.*", on_all_events)
    
    while True:
        prompt = input("\nRealtyIQ> ").strip()
        if prompt.lower() in {"exit", "quit"}:
            return
        
        # Clear tool calls for this run
        if is_enabled():
            tool_calls_logged.clear()
        
        # Trace the agent run with Langfuse
        with trace_agent_run(
            user_id="cli_user",
            session_id=session_id,
            metadata={"source": "cli"}
        ) as tracer:
            try:
                tracer.log_input(prompt, model=llm_name)
                result = await agent.run(prompt)
                response = result.last_message.text
                
                # Log tool calls to Langfuse
                if is_enabled():
                    for call in tool_calls_logged:
                        if 'output' in call:
                            tracer.log_tool_call(
                                tool_name=call['name'],
                                args=call.get('input', {}),
                                result=str(call['output'])[:500]
                            )
                    
                    tracer.log_output(response, metadata={
                        'tools_used': len(tool_calls_logged),
                        'tool_names': [call['name'] for call in tool_calls_logged]
                    })
                else:
                    tracer.log_output(response)
                
                print("\nRealtyIQ>", response)
                
                if is_enabled() and tool_calls_logged:
                    print(f"\n📊 Used {len(tool_calls_logged)} tool(s)")
                
            except Exception as e:
                tracer.log_error(e)
                logger.exception("CLI agent run failed")
                print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
