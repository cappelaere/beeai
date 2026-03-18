"""
Helper utilities for workflow execution and management.

This module contains helper classes and functions to support workflow operations,
including WebSocket broadcasting and workflow execution management.
"""

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class WebSocketPrintCapture:
    """
    Capture stdout print statements and broadcast them via WebSocket.

    Used during workflow execution to stream real-time progress updates
    to connected WebSocket clients while also preserving terminal output.
    """

    def __init__(self, channel_layer, group_name: str, user_id: int, original_stdout):
        """
        Initialize the print capture.

        Args:
            channel_layer: Django Channels layer for broadcasting
            group_name: WebSocket group name to broadcast to
            user_id: User ID for filtering messages
            original_stdout: Original sys.stdout to preserve terminal output
        """
        self.channel_layer = channel_layer
        self.group_name = group_name
        self.user_id = user_id
        self.original_stdout = original_stdout
        self.buffer = []

    def write(self, text: str):
        """
        Write text to both terminal and WebSocket.

        Args:
            text: Text to write
        """
        # Write to original stdout (terminal)
        self.original_stdout.write(text)
        self.original_stdout.flush()

        # Also broadcast non-empty lines to WebSocket
        if text.strip():
            self.buffer.append(text)
            # Broadcast immediately for real-time updates
            if self.channel_layer:
                try:
                    # Create a coroutine to send the message
                    async def send_progress():
                        await self.channel_layer.group_send(
                            self.group_name,
                            {
                                "type": "workflow_message",
                                "message_type": "progress",
                                "text": text.rstrip(),
                                "user_id": self.user_id,
                            },
                        )

                    # Schedule it to run
                    asyncio.create_task(send_progress())
                except Exception as e:
                    logger.debug("Workflow progress broadcast failed: %s", e)

    def flush(self):
        """Flush the original stdout."""
        self.original_stdout.flush()


async def broadcast_workflow_status(channel_layer, run_id: str, user_id: int, status: str):
    """
    Broadcast workflow status update via WebSocket.

    Args:
        channel_layer: Django Channels layer
        run_id: Workflow run ID
        user_id: User ID
        status: Status to broadcast (running, completed, failed, etc.)
    """
    if channel_layer:
        await channel_layer.group_send(
            f"workflow_{run_id}",
            {
                "type": "workflow_message",
                "message_type": "status",
                "status": status,
                "user_id": user_id,
            },
        )


async def broadcast_workflow_steps(channel_layer, run_id: str, user_id: int, steps: list[str]):
    """
    Broadcast workflow step completion via WebSocket.

    Args:
        channel_layer: Django Channels layer
        run_id: Workflow run ID
        user_id: User ID
        steps: List of completed step descriptions
    """
    if channel_layer:
        group_name = f"workflow_{run_id}"
        for step in steps:
            await channel_layer.group_send(
                group_name,
                {
                    "type": "workflow_message",
                    "message_type": "step",
                    "step": step,
                    "user_id": user_id,
                },
            )


async def broadcast_workflow_complete(
    channel_layer, run_id: str, user_id: int, result: dict[str, Any]
):
    """
    Broadcast workflow completion via WebSocket.

    Args:
        channel_layer: Django Channels layer
        run_id: Workflow run ID
        user_id: User ID
        result: Workflow result data
    """
    if channel_layer:
        await channel_layer.group_send(
            f"workflow_{run_id}",
            {
                "type": "workflow_message",
                "message_type": "complete",
                "result": result,
                "user_id": user_id,
            },
        )


async def broadcast_workflow_waiting(
    channel_layer, run_id: str, user_id: int, pending_tasks: list[dict[str, Any]], message: str
):
    """
    Broadcast workflow waiting for task via WebSocket.

    Args:
        channel_layer: Django Channels layer
        run_id: Workflow run ID
        user_id: User ID
        pending_tasks: List of pending task details
        message: Message describing what the workflow is waiting for
    """
    if channel_layer:
        await channel_layer.group_send(
            f"workflow_{run_id}",
            {
                "type": "workflow_message",
                "message_type": "waiting",
                "status": "waiting_for_task",
                "pending_tasks": pending_tasks,
                "message": message,
                "user_id": user_id,
            },
        )


async def broadcast_workflow_error(channel_layer, run_id: str, user_id: int, error_message: str):
    """
    Broadcast workflow error via WebSocket.

    Args:
        channel_layer: Django Channels layer
        run_id: Workflow run ID
        user_id: User ID
        error_message: Error message to broadcast
    """
    if channel_layer:
        await channel_layer.group_send(
            f"workflow_{run_id}",
            {
                "type": "workflow_message",
                "message_type": "error",
                "message": error_message,
                "user_id": user_id,
            },
        )


def track_workflow_metrics(workflow_id: str, status: str, duration: float | None = None):
    """
    Track workflow metrics (completion, failure, duration).

    Args:
        workflow_id: ID of the workflow
        status: Status to track (completed, failed, running, etc.)
        duration: Optional duration in seconds for completed workflows
    """
    try:
        from agent_app.metrics_collector import (
            workflow_execution_duration_seconds,
            workflow_runs_total,
        )

        # Increment run counter
        workflow_runs_total.labels(workflow_id=workflow_id, status=status).inc()

        # Record duration if provided
        if duration is not None and status == "completed":
            workflow_execution_duration_seconds.labels(workflow_id=workflow_id).observe(duration)
    except Exception as e:
        logger.debug("Workflow metrics tracking failed: %s", e)
