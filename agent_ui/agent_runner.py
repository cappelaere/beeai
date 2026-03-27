"""
Multi-Agent Runner for Django chat API.
Supports GRES, SAM.gov, and future agents with model selection.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Repo root = parent of agent_ui (this file lives in agent_ui/agent_runner.py)
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Also add agent_ui directory for local imports (cache.py)
_AGENT_UI_DIR = Path(__file__).resolve().parent
if str(_AGENT_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_UI_DIR))

# Load .env from repo root (same as run_agent.py)
from dotenv import load_dotenv

load_dotenv(_REPO_ROOT / ".env", override=True)

# Import multi-agent system
from agents.base import AVAILABLE_MODELS, DEFAULT_MODEL, create_agent, get_model_display_name
from agents.registry import get_agent_config, get_default_agent_id, load_agents_registry


def _build_available_agents():
    """Build AVAILABLE_AGENTS dict from registry for backward compatibility."""
    agents_dict = {}
    registry = load_agents_registry()
    for agent_id in registry:
        try:
            config = get_agent_config(agent_id)
            agents_dict[agent_id] = config
        except Exception as e:
            logger.warning(f"Could not load agent config for {agent_id}: {e}")
    return agents_dict


# Build AVAILABLE_AGENTS for backward compatibility with command handlers
AVAILABLE_AGENTS = _build_available_agents()


def get_agent(agent_type: str = None, model_id: str = None):
    """Get agent instance by type and model"""
    if not agent_type:
        agent_type = get_default_agent_id()

    if not model_id:
        model_id = AVAILABLE_MODELS[DEFAULT_MODEL]["id"]

    # Load agent config from registry
    try:
        config = get_agent_config(agent_type)
    except KeyError:
        logger.warning(f"Agent '{agent_type}' not found, using default")
        agent_type = get_default_agent_id()
        config = get_agent_config(agent_type)

    logger.info(f"Creating agent: {config.name} with model: {model_id}")
    return create_agent(config, model_id, agent_id=agent_type)


def _get_agent():
    """Legacy function for backwards compatibility"""
    return get_agent(get_default_agent_id())


# Max characters of bindings to include in context (BPMN diagram is no longer truncated)
_MAX_BINDINGS_CONTEXT_CHARS = 4_000


def _format_context_data(context_data: dict | None) -> str:
    """Serialize editor/workflow context into a compact prompt block. BPMN XML is included in full; bindings may be truncated."""
    if not context_data:
        return ""

    summary = {}
    for key, value in context_data.items():
        if key in {"bpmn_xml", "bindings_yaml", "bindings_json"}:
            continue
        summary[key] = value

    parts = ["[Workflow editor context]"]
    if summary:
        parts.append(json.dumps(summary, indent=2, ensure_ascii=False))

    bpmn_xml = (context_data.get("bpmn_xml") or "").strip()
    if bpmn_xml:
        parts.append("Current BPMN XML:")
        parts.append(bpmn_xml)

    bindings_yaml = (context_data.get("bindings_yaml") or "").strip()
    if not bindings_yaml and context_data.get("bindings_json"):
        import yaml

        try:
            bindings_yaml = yaml.safe_dump(
                context_data["bindings_json"], default_flow_style=False, allow_unicode=True
            )
        except Exception:
            bindings_yaml = json.dumps(context_data["bindings_json"], indent=2)
    if bindings_yaml:
        if len(bindings_yaml) > _MAX_BINDINGS_CONTEXT_CHARS:
            bindings_yaml = bindings_yaml[:_MAX_BINDINGS_CONTEXT_CHARS] + "\n\n[... truncated.]"
        parts.append("Current BPMN bindings YAML:")
        parts.append(bindings_yaml)

    return "\n\n".join(parts)


def _check_cache(cache, prompt: str, context_data: dict | None = None):
    """Check cache for existing response."""
    if context_data:
        return None
    if not cache:
        return None

    cached_result = cache.get(prompt, session_id=None)
    if cached_result:
        response_text, metadata = cached_result
        logger.info(f"✅ Returning cached response for prompt: {prompt[:50]}...")
        return response_text, metadata
    return None


def _build_messages(
    prompt: str, conversation_history: list = None, context_data: dict | None = None
):
    """Build messages list with conversation history."""
    from beeai_framework.backend import AssistantMessage, UserMessage

    messages = []

    if conversation_history:
        logger.info(f"📚 Including {len(conversation_history)} previous messages for context")
        for msg in conversation_history:
            if msg.get("role") == "user":
                messages.append(UserMessage(msg.get("content", "")))
            elif msg.get("role") == "assistant":
                messages.append(AssistantMessage(msg.get("content", "")))

    context_text = _format_context_data(context_data)
    if context_text:
        messages.append(UserMessage(context_text))

    messages.append(UserMessage(prompt))
    return messages


def _parse_tool_from_path(path: str):
    """Extract tool name from event path."""
    if not path.startswith("tool."):
        return None

    if "final_answer" in path:
        return None

    path_parts = path.split(".")
    try:
        if len(path_parts) >= 4 and path_parts[0] == "tool" and path_parts[1] == "custom":
            return path_parts[2]
    except (ValueError, IndexError):
        pass

    return None


def _handle_tool_start(event, tool_name: str, meta, tool_calls_logged: list):
    """Handle tool start event."""
    try:
        tool_input = event.input if hasattr(event, "input") else {}
        logger.info(f"🔧 Tool starting: {tool_name}")
        tool_calls_logged.append(
            {
                "name": tool_name,
                "input": tool_input,
                "start_time": time.time(),
                "trace_path": meta.path,
            }
        )
    except Exception as e:
        logger.warning(f"Failed to log tool start: {e}")


def _handle_tool_success(event, tool_name: str, tool_calls_logged: list, tracer):
    """Handle tool success event."""
    try:
        tool_output = event.output if hasattr(event, "output") else None
        logger.info(
            f"🔍 Tool output ({tool_name}): {str(tool_output)[:200] if tool_output else 'None'}..."
        )

        for call in tool_calls_logged:
            if call["name"] == tool_name and "output" not in call:
                call["output"] = tool_output
                call["end_time"] = time.time()
                elapsed = int((call["end_time"] - call["start_time"]) * 1000)

                tracer.log_tool_call(
                    tool_name=tool_name, args=call.get("input", {}), result=str(tool_output)[:500]
                )
                logger.info(f"✓ Tool completed: {tool_name} ({elapsed}ms)")
                break
    except Exception as e:
        logger.warning(f"Failed to log tool success: {e}")


def _handle_tool_error(event, tool_name: str):
    """Handle tool error event."""
    try:
        error_details = event.error if hasattr(event, "error") else event
        error_message = str(error_details)
        logger.error(f"✗ Tool error: {tool_name}")
        logger.error(f"   Error type: {type(error_details).__name__}")
        logger.error(f"   Error message: {error_message}")

        if hasattr(error_details, "__traceback__"):
            import traceback as tb

            tb_lines = tb.format_exception(
                type(error_details), error_details, error_details.__traceback__
            )
            logger.error(f"   Traceback:\n{''.join(tb_lines)}")
    except Exception as e:
        logger.error(f"✗ Tool error: {tool_name} (failed to get error details: {e})")


def _create_event_handler(tool_calls_logged: list, tracer):
    """Create event handler for tool tracking."""

    def on_all_events(event, meta):
        """Capture all events and filter for tool-related ones"""
        tool_name = _parse_tool_from_path(meta.path)
        if not tool_name:
            return

        if meta.name == "start":
            _handle_tool_start(event, tool_name, meta, tool_calls_logged)
        elif meta.name == "success":
            _handle_tool_success(event, tool_name, tool_calls_logged, tracer)
        elif meta.name == "error":
            _handle_tool_error(event, tool_name)

    return on_all_events


async def _execute_agent(agent, messages):
    """Execute agent and handle errors."""
    try:
        result = await agent.run(messages)
        return (result.last_message.text or "").strip()
    except (RuntimeError, Exception) as error:
        import traceback as tb

        error_msg = str(error)
        error_type = type(error).__name__
        tb_str = tb.format_exc()

        logger.error(f"❌ Agent run failed: {error_type}: {error_msg}")
        logger.error(f"Full traceback:\n{tb_str}")

        original_error = error
        while hasattr(original_error, "__cause__") and original_error.__cause__:
            original_error = original_error.__cause__

        if original_error is not error:
            logger.error(f"Original cause: {type(original_error).__name__}: {original_error}")
            raise original_error from error

        raise


def _cache_result(
    cache, prompt: str, response_text: str, metadata: dict, context_data: dict | None = None
):
    """Cache the response for future use."""
    if context_data:
        return
    if cache:
        cache.set(prompt, response_text, metadata, session_id=None)
        logger.info("💾 Response cached for future use")


async def _run_with_observability(
    prompt: str,
    agent_type: str,
    model_id: str,
    session_id: str,
    user_id: str,
    conversation_history: list,
    cache,
    metadata: dict,
    context_data: dict | None = None,
) -> tuple[str, dict]:
    """Run agent with Langfuse observability tracing."""
    from beeai_framework.emitter import Emitter

    from observability import trace_agent_run

    with trace_agent_run(
        user_id=user_id,
        session_id=session_id,
        metadata={"source": "web_ui", "agent_type": agent_type},
    ) as tracer:
        try:
            tracer.log_input(
                prompt,
                model=model_id or get_model_display_name(AVAILABLE_MODELS[DEFAULT_MODEL]["id"]),
            )

            agent = get_agent(agent_type, model_id)
            messages = _build_messages(prompt, conversation_history, context_data=context_data)

            tool_calls_logged = []
            event_handler = _create_event_handler(tool_calls_logged, tracer)

            root = Emitter.root()
            root.on("*.*", event_handler)

            response_text = await _execute_agent(agent, messages)

            tracer.log_output(
                response_text,
                metadata={
                    "tools_used": len(tool_calls_logged),
                    "tool_names": [call["name"] for call in tool_calls_logged],
                },
            )

            if hasattr(tracer, "trace") and hasattr(tracer.trace, "id"):
                metadata["trace_id"] = tracer.trace.id
            metadata["tools_used"] = len(tool_calls_logged)

            _cache_result(cache, prompt, response_text, metadata, context_data=context_data)

            logger.info(f"📊 Trace complete: {len(tool_calls_logged)} tools used")
            root.off(callback=event_handler)

            return response_text, metadata
        except Exception as e:
            tracer.log_error(e)
            raise


async def _run_without_observability(
    prompt: str,
    agent_type: str,
    model_id: str,
    conversation_history: list,
    cache,
    metadata: dict,
    context_data: dict | None = None,
) -> tuple[str, dict]:
    """Run agent without observability tracing."""
    agent = get_agent(agent_type, model_id)
    messages = _build_messages(prompt, conversation_history, context_data=context_data)

    response_text = await _execute_agent(agent, messages)
    _cache_result(cache, prompt, response_text, metadata, context_data=context_data)

    return response_text, metadata


async def run_agent(
    prompt: str,
    agent_type: str = None,
    model_id: str = None,
    session_id: str = None,
    user_id: str = None,
    conversation_history: list = None,
    context_data: dict | None = None,
) -> tuple[str, dict]:
    """
    Run the agent with the given prompt and conversation history for context.
    Checks cache first before running the agent.

    Args:
        prompt: The user's current message
        session_id: Session identifier for grouping related messages
        user_id: User identifier
        conversation_history: List of previous messages [{"role": "user"|"assistant", "content": "..."}]

    Returns:
        tuple: (response_text, metadata_dict) where metadata includes trace_id if observability is enabled
    """
    try:
        from cache import get_cache

        cache = get_cache()
    except ImportError:
        logger.warning("Cache module not available")
        cache = None

    cached_result = _check_cache(cache, prompt, context_data=context_data)
    if cached_result:
        return cached_result

    import importlib.util

    observability_enabled = importlib.util.find_spec("observability") is not None

    metadata = {}

    if observability_enabled:
        return await _run_with_observability(
            prompt,
            agent_type,
            model_id,
            session_id,
            user_id,
            conversation_history,
            cache,
            metadata,
            context_data=context_data,
        )
    return await _run_without_observability(
        prompt,
        agent_type,
        model_id,
        conversation_history,
        cache,
        metadata,
        context_data=context_data,
    )


def run_agent_sync(
    prompt: str,
    agent_type: str = None,
    model_id: str = None,
    session_id: str = None,
    user_id: str = None,
    conversation_history: list = None,
    context_data: dict | None = None,
) -> tuple[str, dict]:
    """Synchronous wrapper for Django views."""
    return asyncio.run(
        run_agent(
            prompt=prompt,
            agent_type=agent_type,
            model_id=model_id,
            session_id=session_id,
            user_id=user_id,
            conversation_history=conversation_history,
            context_data=context_data,
        )
    )
