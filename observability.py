"""
Langfuse Observability Integration for RealtyIQ
Provides tracing, monitoring, and cost tracking for LLM interactions
"""
import logging
import os
import time
from typing import Optional, Dict, Any
from contextlib import contextmanager
from functools import wraps

logger = logging.getLogger(__name__)

# Langfuse client (lazy-loaded)
_langfuse_client = None


def get_langfuse_client():
    """Get or create the Langfuse client singleton"""
    global _langfuse_client
    
    if _langfuse_client is not None:
        return _langfuse_client
    
    # Check if Langfuse is enabled
    if not os.getenv("LANGFUSE_ENABLED", "false").lower() == "true":
        return None
    
    try:
        from langfuse import Langfuse
        
        _langfuse_client = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com"),
        )
        logger.info("Langfuse observability enabled")
        return _langfuse_client
    except ImportError:
        logger.info("Langfuse not installed. Run: pip install langfuse")
        return None
    except Exception as e:
        logger.warning("Failed to initialize Langfuse: %s", e, exc_info=True)
        return None


def is_enabled():
    """Check if Langfuse observability is enabled and available"""
    return get_langfuse_client() is not None


@contextmanager
def trace_agent_run(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Context manager for tracing an agent run with Langfuse SDK 3.x+
    Uses start_as_current_observation() for proper nesting support
    
    Usage:
        with trace_agent_run(user_id="user123", session_id="session456") as tracer:
            tracer.log_input("What properties are available?")
            result = await agent.run(prompt)
            tracer.log_output(result)
    """
    client = get_langfuse_client()
    
    if client is None:
        # Return a no-op tracer if Langfuse is not available
        try:
            yield NoOpTracer()
        finally:
            pass
        return

    # Create trace using Langfuse SDK 3.x+ with context manager for proper nesting
    try:
        # Prepare metadata
        full_metadata = {
            "user_id": user_id,
            "session_id": session_id,
            **(metadata or {})
        }

        # Use start_as_current_observation as a context manager for automatic nesting
        with client.start_as_current_observation(
            name="realtyiq_agent_run",
            as_type="agent",
            metadata=full_metadata
        ) as observation:
            # Get trace ID from observation
            trace_id = observation.trace_id if hasattr(observation, 'trace_id') else None

            tracer = LangfuseTracer(client, observation, trace_id)

            try:
                yield tracer
            except Exception as e:
                try:
                    tracer.log_error(e)
                except Exception:
                    logger.exception("Failed to log error to Langfuse")
                raise
            finally:
                # Flush happens after yield completes (success or exception)
                try:
                    client.flush()
                except Exception as e:
                    logger.debug("Langfuse flush failed: %s", e)

    except Exception as e:
        logger.warning("Failed to create Langfuse trace: %s", e, exc_info=True)
        # Fall back to no-op tracer so caller can still run (and we handle their exception)
        try:
            yield NoOpTracer()
        except Exception:
            raise
        finally:
            pass


class LangfuseTracer:
    """Helper class for Langfuse tracing within an observation context"""
    
    def __init__(self, client, observation, trace_id):
        self.client = client
        self.observation = observation
        self.trace_id = trace_id
        self.start_time = time.time()
        self._input = None
        self._output = None
        self._model = None
        self._child_observations = []
        
        # Get the observation ID for reference
        self.observation_id = observation.id if hasattr(observation, 'id') else None
        
    def log_input(self, prompt: str, model: str = None):
        """Log input prompt"""
        self._input = prompt
        self._model = model
        try:
            self.observation.update(input=prompt)
            if model:
                self.observation.update(model=model)
        except Exception as e:
            logger.warning("Failed to update observation input: %s", e, exc_info=True)

    def log_output(self, response: str, usage: Optional[Dict] = None, metadata: Optional[Dict] = None):
        """Log output response and usage stats"""
        self._output = response
        try:
            update_data = {"output": response}
            if usage:
                update_data["usage"] = usage
            if metadata:
                update_data["metadata"] = metadata
            self.observation.update(**update_data)
        except Exception as e:
            logger.warning("Failed to update observation output: %s", e, exc_info=True)
    
    def log_tool_call(self, tool_name: str, tool_input: Any = None, tool_output: Any = None, args: Any = None, result: Any = None):
        """Log a tool call as a child generation
        
        Accepts both old (tool_input/tool_output) and new (args/result) parameter names for compatibility
        """
        # Support both parameter naming conventions
        actual_input = tool_input if tool_input is not None else args
        actual_output = tool_output if tool_output is not None else result
        
        try:
            # Create a child observation for the tool call using the client
            # The observation context manager doesn't have a generation() method
            # We need to create a new span within the current trace
            child_span = self.client.span(
                name=tool_name,
                input=actual_input,
                output=actual_output,
                metadata={"type": "tool_call"}
            )
            self._child_observations.append(child_span)
        except Exception as e:
            logger.debug("Failed to log tool call to Langfuse: %s", e)

    def log_error(self, error: Exception):
        """Log an error"""
        try:
            self.observation.update(
                output={"error": str(error)},
                level="ERROR"
            )
        except Exception as e:
            logger.warning("Failed to log error to Langfuse: %s", e, exc_info=True)
    
    def get_trace_url(self) -> Optional[str]:
        """Get the Langfuse trace URL"""
        if self.trace_id:
            host = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
            # Remove trailing slash if present
            host = host.rstrip('/')
            project_id = os.getenv("LANGFUSE_PUBLIC_KEY", "").split("-")[0] if os.getenv("LANGFUSE_PUBLIC_KEY") else "default"
            return f"{host}/project/{project_id}/traces/{self.trace_id}"
        return None


class NoOpTracer:
    """No-op tracer when Langfuse is not available"""
    
    def __init__(self):
        self.trace_id = None
        self.observation_id = None
    
    def log_input(self, prompt: str, model: str = None):
        pass
    
    def log_output(self, response: str, usage: Optional[Dict] = None, metadata: Optional[Dict] = None):
        pass
    
    def log_tool_call(self, tool_name: str, tool_input: Any = None, tool_output: Any = None, args: Any = None, result: Any = None):
        pass
    
    def log_error(self, error: Exception):
        pass
    
    def get_trace_url(self) -> Optional[str]:
        return None


def log_feedback(trace_id: str, score: float, comment: Optional[str] = None):
    """
    Log user feedback for a trace
    
    Args:
        trace_id: The Langfuse trace ID
        score: Feedback score (0.0 to 1.0, where 1.0 is positive)
        comment: Optional comment text
    """
    client = get_langfuse_client()
    if client is None:
        return
    
    try:
        client.score(
            trace_id=trace_id,
            name="user-feedback",
            value=score,
            comment=comment
        )
        client.flush()
    except Exception as e:
        logger.warning("Failed to log feedback: %s", e, exc_info=True)


def trace_function(name: Optional[str] = None):
    """
    Decorator to automatically trace a function
    
    Usage:
        @trace_function(name="my_function")
        def my_function(arg1, arg2):
            return result
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with trace_agent_run(metadata={"function": name or func.__name__}) as tracer:
                try:
                    tracer.log_input(f"Args: {args}, Kwargs: {kwargs}")
                    result = await func(*args, **kwargs)
                    tracer.log_output(str(result))
                    return result
                except Exception as e:
                    tracer.log_error(e)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with trace_agent_run(metadata={"function": name or func.__name__}) as tracer:
                try:
                    tracer.log_input(f"Args: {args}, Kwargs: {kwargs}")
                    result = func(*args, **kwargs)
                    tracer.log_output(str(result))
                    return result
                except Exception as e:
                    tracer.log_error(e)
                    raise
        
        # Return appropriate wrapper based on whether function is async
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
