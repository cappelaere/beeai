"""
Chat API endpoints
Handles chat message processing and history retrieval.
"""

import json
import logging
import time

from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from agent_app.constants import ANONYMOUS_USER_ID
from agent_app.models import ChatMessage, ChatSession, PromptSuggestion, UserPreference
from agents.base import DEFAULT_MODEL, get_model_display_name, get_model_id_from_short_key
from agents.registry import get_agent_display_name

logger = logging.getLogger(__name__)


def _validate_chat_request(request_body):
    """
    Validate and parse chat request data.

    Returns:
        tuple: (prompt, session_id, elapsed_ms, agent_type, model_id_short) or (None, error_response)
    """
    try:
        body = json.loads(request_body)
        prompt = (body.get("prompt") or body.get("message") or "").strip()
        session_id = body.get("session_id")
        elapsed_ms = body.get("elapsed_ms", 0)
        agent_type = body.get("agent", "gres")
        model_id_short = body.get("model") or (
            "claude-sonnet-4" if agent_type == "bpmn_expert" else DEFAULT_MODEL
        )
        context_data = body.get("context_data")

        if not prompt:
            return None, JsonResponse({"error": "Empty prompt"}, status=400)

        return (prompt, session_id, elapsed_ms, agent_type, model_id_short, context_data), None
    except (json.JSONDecodeError, TypeError):
        return None, JsonResponse({"error": "Invalid JSON or missing 'prompt'"}, status=400)


def _get_or_create_session(request, session_id, user_id):
    """
    Get existing session or create a new one.

    Returns:
        ChatSession object or (None, error_response)
    """
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    if session_id:
        session_obj = get_object_or_404(ChatSession, pk=session_id)
        if session_obj.user_id != user_id:
            return None, JsonResponse({"error": "Forbidden"}, status=403)
        return session_obj, None
    # Get most recent session for this user, or create new one
    session_obj = (
        ChatSession.objects.filter(session_key=session_key, user_id=user_id)
        .order_by("-created_at")
        .first()
    )

    if not session_obj:
        session_obj = ChatSession.objects.create(
            session_key=session_key, user_id=user_id, title="New Chat"
        )
    return session_obj, None


def _handle_slash_command(command, request, session_obj, prompt):
    """
    Handle slash commands.

    Returns:
        dict: Command result or None to continue with normal execution
    """
    from agent_app.command_dispatcher import dispatcher

    # Store command as user message
    ChatMessage.objects.create(session=session_obj, role=ChatMessage.ROLE_USER, content=prompt)

    # Execute command
    result = dispatcher.dispatch(command, request, session_obj.id)

    # Check command result type
    if result.get("execute_card"):
        # Return card execution info to continue with agent
        return {
            "continue": True,
            "prompt": result["card_prompt"],
            "agent_type": result.get("card_agent", "gres"),
        }
    if result.get("metadata", {}).get("execute_prompt"):
        # Return saved prompt execution info
        return {"continue": True, "prompt": result.get("prompt_text", ""), "agent_type": "gres"}
    if result.get("metadata", {}).get("open_diagram"):
        # Store and return diagram response
        ChatMessage.objects.create(
            session=session_obj,
            role=ChatMessage.ROLE_ASSISTANT,
            content=result["content"],
            tokens_used=0,
            elapsed_ms=0,
        )
        return {
            "response": JsonResponse(
                {
                    "response": result["content"],
                    "session_id": session_obj.id,
                    "metadata": result.get("metadata", {}),
                    "is_command": True,
                    "diagram_url": result.get("diagram_url"),
                    "section_508_enabled": False,
                }
            )
        }
    # Store and return command response
    ChatMessage.objects.create(
        session=session_obj,
        role=ChatMessage.ROLE_ASSISTANT,
        content=result["content"],
        tokens_used=0,
        elapsed_ms=0,
    )
    return {
        "response": JsonResponse(
            {
                "response": result["content"],
                "session_id": session_obj.id,
                "metadata": result.get("metadata", {}),
                "is_command": True,
                "section_508_enabled": False,
            }
        )
    }


def _handle_at_mention(request, command, remaining_text, session_key, session_obj, original_prompt):
    """
    Handle @Agent mentions.

    Returns:
        tuple: (agent_type, prompt) or (None, error_response)
    """
    from agent_app.commands.at_mention import handle_at_mention

    result = handle_at_mention(request, command.name, remaining_text, session_key)

    if result.get("content") and result.get("metadata", {}).get("error"):
        return None, JsonResponse({"error": result["content"]}, status=400)

    # Store original @Agent message as user message
    ChatMessage.objects.create(
        session=session_obj,
        role=ChatMessage.ROLE_USER,
        content=f"@{command.name} {result['message']}",
    )

    return (result["override_agent"], result["message"]), None


def _get_conversation_history(session_obj, user_id, context_count):
    """Get the most recent N messages (before current turn) for context. Chronological order for the model."""
    conversation_history = []

    if context_count > 0:
        # Last N messages by created_at (most recent first), then reverse to chronological order
        last_messages = list(session_obj.messages.order_by("-created_at")[:context_count])
        for msg in reversed(last_messages):
            conversation_history.append({"role": msg.role, "content": msg.content})
        logger.info(
            f"📚 Loaded {len(conversation_history)} previous messages for context (user setting: {context_count})"
        )
    else:
        logger.info(f"📚 Context disabled (user setting: {context_count})")

    return conversation_history


def _execute_agent(
    prompt,
    agent_type,
    model_id,
    session_obj,
    user_id,
    conversation_history,
    context_data=None,
):
    """
    Execute the agent and return response.

    Returns:
        tuple: (response_text, trace_id, from_cache, elapsed_ms) or raises exception
    """
    from agent_runner import run_agent_sync

    start_time = time.time()
    trace_id = None
    from_cache = False

    try:
        response_text, metadata = run_agent_sync(
            prompt,
            agent_type=agent_type,
            model_id=model_id,
            session_id=str(session_obj.pk),
            user_id=str(user_id),
            conversation_history=conversation_history,
            context_data=context_data,
        )
        trace_id = metadata.get("trace_id")
        from_cache = metadata.get("from_cache", False)

        if from_cache:
            logger.info(f"🎯 Cache HIT - Returning cached response for prompt: {prompt[:50]}...")
        else:
            logger.info(f"⚙️  Cache MISS - Generated new response for prompt: {prompt[:50]}...")

    except GeneratorExit:
        response_text = "Request processing was interrupted"
        logger.warning("Request was interrupted during processing")
    except Exception as e:
        response_text = _format_error_response(e)

    elapsed_ms = int((time.time() - start_time) * 1000)
    return response_text, trace_id, from_cache, elapsed_ms


def _is_rate_limit_error(exception: Exception, error_msg: str) -> bool:
    msg_lower = error_msg.lower()
    cause = getattr(exception, "__cause__", None)
    return (
        "rate limit" in msg_lower
        or "429" in error_msg
        or (cause and "rate limit" in str(cause).lower())
    )


def _extract_anthropic_error_payload(exception: Exception) -> dict | None:
    current = exception
    while current:
        current_msg = str(current)
        if current_msg.strip().startswith("{"):
            try:
                parsed = json.loads(current_msg)
                if isinstance(parsed, dict) and "error" in parsed:
                    return parsed
            except (json.JSONDecodeError, ValueError) as e:
                logger.debug("Could not parse error shape from exception: %s", e)

        if hasattr(current, "body"):
            try:
                if isinstance(current.body, dict):
                    return current.body
                if isinstance(current.body, str):
                    parsed_body = json.loads(current.body)
                    if isinstance(parsed_body, dict):
                        return parsed_body
            except (json.JSONDecodeError, ValueError, AttributeError) as e:
                logger.debug("Could not parse error shape from exception: %s", e)

        current = getattr(current, "__cause__", None)
    return None


def _format_error_response(exception):
    """Format exception as user-friendly error message."""
    error_msg = str(exception)
    error_type = type(exception).__name__

    logger.error(f"Error in chat_api: {error_type}: {error_msg}", exc_info=True)

    if _is_rate_limit_error(exception, error_msg):
        return (
            "**Rate limit reached**\n\n"
            "The model provider is temporarily limiting requests. "
            "Please wait a minute and try again."
        )

    anthropic_error = _extract_anthropic_error_payload(exception)
    if anthropic_error and isinstance(anthropic_error, dict):
        error_details = anthropic_error.get("error", {})
        error_subtype = error_details.get("type", "unknown_error")
        error_message = error_details.get("message", error_msg)
        logger.error(f"Anthropic API error details: {json.dumps(anthropic_error, indent=2)}")
        return f"**Anthropic API Error ({error_subtype})**\n\n{error_message}"
    return f"**Error ({error_type})**\n\n{error_msg}"


def _start_tts_synthesis(user_id, assistant_message, response_text):
    """Start TTS synthesis in background if Section 508 is enabled."""
    import os
    import threading

    from agent_app.tts_client import synthesize_for_message

    default_508 = os.getenv("SECTION_508_MODE", "false").lower() in ("true", "1", "yes")
    pref = UserPreference.objects.filter(user_id=user_id).first()
    section_508_enabled = (
        pref.section_508_enabled if (pref and pref.section_508_enabled is not None) else default_508
    )

    audio_url = None
    if section_508_enabled and response_text:
        tts_thread = threading.Thread(
            target=synthesize_for_message, args=(assistant_message.pk, response_text), daemon=True
        )
        tts_thread.start()
        logger.info(f"Started TTS synthesis for message {assistant_message.pk}")

    return section_508_enabled, audio_url


def _save_prompt_suggestion(prompt, user_id):
    """Save prompt to suggestions database."""
    prompt_suggestion, created = PromptSuggestion.objects.get_or_create(
        prompt=prompt, defaults={"is_predefined": False}
    )
    prompt_suggestion.usage_count += 1
    prompt_suggestion.last_used = timezone.now()
    prompt_suggestion.save()


def _process_commands(request, session_obj, prompt, agent_type):
    """
    Parse and handle commands (slash commands and @mentions).

    Returns:
        dict: Result with 'response', 'prompt', and 'agent_type' keys
    """
    from agent_app.command_parser import parse_command

    command, remaining_text = parse_command(prompt)

    if command:
        if command.cmd_type == "slash":
            result = _handle_slash_command(command, request, session_obj, prompt)
            if result.get("response"):
                return result
            if result.get("continue"):
                return {
                    "prompt": result["prompt"],
                    "agent_type": result.get("agent_type", agent_type),
                }
        elif command.cmd_type == "at_mention":
            mention_result, error_response = _handle_at_mention(
                request, command, remaining_text, request.session.session_key, session_obj, prompt
            )
            if error_response:
                return {"response": error_response}
            agent_type, prompt = mention_result
            return {"prompt": prompt, "agent_type": agent_type}
    else:
        # Normal message - store user message
        ChatMessage.objects.create(session=session_obj, role=ChatMessage.ROLE_USER, content=prompt)

    return {"prompt": prompt, "agent_type": agent_type}


@require_http_methods(["POST"])
def chat_api(request):
    """
    Handle chat API requests.
    Complexity reduced from 32 to ~7 by extracting helper functions.
    """
    # 1. Validate request
    validation_result, error_response = _validate_chat_request(request.body)
    if error_response:
        return error_response
    prompt, session_id, elapsed_ms, agent_type, model_id_short, context_data = validation_result

    # Convert short model ID to full model ID; BPMN expert always uses Sonnet to avoid rate limits
    if agent_type == "bpmn_expert":
        model_id_short = "claude-sonnet-4"
    model_id = get_model_id_from_short_key(model_id_short)

    try:
        # 2. Get or create session
        user_id = request.session.get("user_id", ANONYMOUS_USER_ID)
        session_obj, error_response = _get_or_create_session(request, session_id, user_id)
        if error_response:
            return error_response

        # 3. Parse and handle commands
        command_result = _process_commands(request, session_obj, prompt, agent_type)
        if command_result.get("response"):
            return command_result["response"]
        prompt = command_result.get("prompt", prompt)
        agent_type = command_result.get("agent_type", agent_type)

        # 4. Save prompt suggestion
        _save_prompt_suggestion(prompt, user_id)

        # 5. Get conversation history (BPMN expert needs enough turns to remember propose/apply flow)
        pref = UserPreference.objects.filter(user_id=user_id).first()
        context_count = pref.context_message_count if pref else 0
        if agent_type == "bpmn_expert" and context_count < 10:
            context_count = 10
        conversation_history = _get_conversation_history(session_obj, user_id, context_count)

        # 6–9. Execute agent, save message, TTS, build response (return 200 with error in body on failure)
        try:
            response_text, trace_id, from_cache, server_elapsed_ms = _execute_agent(
                prompt,
                agent_type,
                model_id,
                session_obj,
                user_id,
                conversation_history,
                context_data=context_data,
            )

            # 7. Save assistant message
            assistant_message = ChatMessage.objects.create(
                session=session_obj,
                role=ChatMessage.ROLE_ASSISTANT,
                content=response_text,
                elapsed_ms=elapsed_ms or server_elapsed_ms,
                tokens_used=0,
            )

            # 8. Start TTS if enabled
            section_508_enabled, audio_url = _start_tts_synthesis(
                user_id, assistant_message, response_text
            )

            # 9. Build response
            agent_display_name = get_agent_display_name(agent_type, "RealtyIQ Agent")
            model_display_name = get_model_display_name(model_id)

            return JsonResponse(
                {
                    "session_id": session_obj.pk,
                    "message_id": assistant_message.pk,
                    "response": response_text,
                    "trace_id": trace_id,
                    "from_cache": from_cache,
                    "elapsed_ms": server_elapsed_ms,
                    "agent_name": agent_display_name,
                    "model_name": model_display_name,
                    "audio_url": audio_url,
                    "section_508_enabled": section_508_enabled,
                }
            )
        except Exception as e:
            # Return 200 with error in "response" so UI shows it instead of crashing
            logger.error(f"Error in chat_api (agent/save/response): {e}", exc_info=True)
            response_text = _format_error_response(e)
            try:
                assistant_message = ChatMessage.objects.create(
                    session=session_obj,
                    role=ChatMessage.ROLE_ASSISTANT,
                    content=response_text,
                    elapsed_ms=elapsed_ms or 0,
                    tokens_used=0,
                )
                message_id = assistant_message.pk
            except Exception as e:
                logger.warning(
                    "Failed to create ChatMessage for error response: %s", e, exc_info=True
                )
                message_id = None
            agent_display_name = get_agent_display_name(agent_type, "RealtyIQ Agent")
            model_display_name = get_model_display_name(model_id)
            return JsonResponse(
                {
                    "session_id": session_obj.pk,
                    "message_id": message_id,
                    "response": response_text,
                    "trace_id": None,
                    "from_cache": False,
                    "elapsed_ms": 0,
                    "agent_name": agent_display_name,
                    "model_name": model_display_name,
                    "audio_url": None,
                    "section_508_enabled": False,
                }
            )

    except ChatSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)
    except Exception:
        from agent_app.http_utils import json_response_500

        return json_response_500("Unexpected error in chat_api")


@require_GET
def chat_history_api(request, session_id):
    """Get chat history for a specific session"""
    try:
        session_obj = get_object_or_404(ChatSession, pk=session_id)
        user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

        if session_obj.user_id != user_id:
            return JsonResponse({"error": "Forbidden"}, status=403)

        messages = list(
            session_obj.messages.order_by("created_at").values(
                "id",
                "role",
                "content",
                "created_at",
                "elapsed_ms",
                "tokens_used",
                "feedback",
                "audio_url",
            )
        )

        return JsonResponse({"messages": messages})
    except Exception:
        from agent_app.http_utils import json_response_500

        return json_response_500("Error fetching chat history")


CHART_CACHE_PREFIX = "agent_chart_"


@require_GET
def serve_agent_chart(request, chart_id):
    """Serve a chart PNG stored by the chart_time_series tool (reduces token usage vs base64 in chat)."""
    key = f"{CHART_CACHE_PREFIX}{chart_id}"
    png_bytes = cache.get(key)
    if png_bytes is None:
        return HttpResponse(status=404)
    return HttpResponse(png_bytes, content_type="image/png")
