"""
/logs command handler - View system logs
"""


def _handle_logs_list(log_files):
    """List all available log files."""
    from django.conf import settings

    lines = ["Available Log Files:", ""]

    for log_file in log_files:
        stat = log_file.stat()
        size_kb = stat.st_size / 1024
        is_current = (
            log_file == settings.CURRENT_LOG_FILE
            if hasattr(settings, "CURRENT_LOG_FILE")
            else False
        )

        line = f"  • {log_file.name}"
        if is_current:
            line += " (CURRENT)"
        line += f" - {size_kb:.1f} KB"
        lines.append(line)

    lines.extend(
        [
            "",
            "Commands:",
            "  /logs current - View current log file",
            "  /logs <filename> [lines] - View specific log file",
            "",
            "To view logs in browser, visit: /logs/",
        ]
    )

    return {"content": "\n".join(lines), "metadata": {"command": "logs", "count": len(log_files)}}


def _handle_logs_show(args, log_files, log_dir):
    """Show contents of a specific log file."""
    from django.conf import settings

    log_name = args[0]
    tail_lines = 50

    if len(args) > 1:
        try:
            tail_lines = int(args[1])
            if tail_lines < 1:
                tail_lines = 50
        except ValueError:
            pass

    if log_name == "current":
        if hasattr(settings, "CURRENT_LOG_FILE"):
            log_file = settings.CURRENT_LOG_FILE
        else:
            log_file = log_files[0] if log_files else None
    else:
        log_file = log_dir / log_name

    if not log_file or not log_file.exists():
        return {
            "content": f"Error: Log file '{log_name}' not found\n\nUse /logs to see available files",
            "metadata": {"command": "logs", "error": True},
        }

    try:
        with log_file.open(encoding="utf-8") as f:
            all_lines = f.readlines()
            lines_to_show = all_lines[-tail_lines:] if tail_lines > 0 else all_lines
            content = "".join(lines_to_show)

            header = [
                f"Log File: {log_file.name}",
                f"Size: {log_file.stat().st_size / 1024:.1f} KB",
                f"Lines: Showing {len(lines_to_show)} of {len(all_lines)}",
                "=" * 60,
                "",
            ]

            return {
                "content": "\n".join(header) + content,
                "metadata": {
                    "command": "logs",
                    "log_name": log_file.name,
                    "total_lines": len(all_lines),
                    "shown_lines": len(lines_to_show),
                },
            }
    except Exception as e:
        return {
            "content": f"Error reading log file: {e}",
            "metadata": {"command": "logs", "error": True},
        }


def handle_logs(request, args, session_key):
    """
    Display and manage system logs.

    Commands:
        /logs - List all log files
        /logs current - Show current log file tail
        /logs <filename> [lines] - Show specified log file

    Args:
        request: Django HTTP request
        args: Command arguments
        session_key: User session key

    Returns:
        Dictionary with content and metadata
    """
    from django.conf import settings

    log_dir = settings.BASE_DIR.parent / "logs"

    if not log_dir.exists():
        return {
            "content": "No logs directory found. Logs will be created on next server start.",
            "metadata": {"command": "logs", "error": True},
        }

    log_files = sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)

    if not log_files:
        return {
            "content": "No log files found. Start the server to generate logs.",
            "metadata": {"command": "logs"},
        }

    if not args:
        return _handle_logs_list(log_files)

    return _handle_logs_show(args, log_files, log_dir)
