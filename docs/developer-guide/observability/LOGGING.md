# Logging System

This document describes the logging system implemented in RealtyIQ Agent.

## Overview

The application uses timestamped log files to track all system activity. Log files are created on application startup and stored in the `logs/` folder.

## Features

- **Timestamped log files**: Each server start creates a new log file with format `realtyiq_YYYYMMDD_HHMMSS.log`
- **Persistent storage**: Logs are stored in the `logs/` folder in the project root
- **Multiple access methods**:
  - Web UI at `/logs/`
  - `/logs` slash command in chat
  - API endpoints for programmatic access
- **Log levels**: INFO, WARNING, ERROR, DEBUG
- **Console and file output**: Logs are written to both console (for development) and files (for persistence)

## File Structure

```
beeai/
├── logs/
│   ├── .gitignore               # Excludes *.log from version control
│   ├── realtyiq_20260221_170312.log
│   ├── realtyiq_20260221_170214.log
│   └── ...                       # Older log files
└── agent_ui/
    └── agent_ui/
        └── settings.py           # Logging configuration
```

## Configuration

The logging system is configured in `agent_ui/agent_ui/settings.py`:

### Key Settings

```python
LOG_DIR = BASE_DIR.parent / "logs"  # Log directory location
LOG_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")  # Timestamp format
LOG_FILE = LOG_DIR / f"realtyiq_{LOG_TIMESTAMP}.log"  # Current log file
CURRENT_LOG_FILE = LOG_FILE  # Accessible by views
```

### Logging Configuration

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': str(LOG_FILE),
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'agent_app': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'agent_runner': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'cache': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

## Usage

### Web Interface

1. Navigate to `/logs/` in your browser
2. View the list of available log files
3. Click on a log file to view its contents
4. Use the dropdown to select how many lines to display (100-5000 or all)
5. Download or copy log contents using the toolbar buttons

Features:
- **Real-time display**: Auto-selects the current log file
- **Color-coded log levels**: ERROR (red), WARNING (yellow), INFO (blue), DEBUG (gray)
- **Responsive controls**: Refresh, download, copy to clipboard
- **File information**: Size, line count, last modified timestamp

### Slash Command

```bash
# List all log files
/logs

# View current log file (last 50 lines)
/logs current

# View current log file (last 100 lines)
/logs current 100

# View specific log file
/logs realtyiq_20260221_170312.log

# View specific log file (last 200 lines)
/logs realtyiq_20260221_170312.log 200
```

### API Endpoints

#### List Log Files

```http
GET /api/logs/
```

Response:
```json
{
  "logs": [
    {
      "name": "realtyiq_20260221_170312.log",
      "size": 45678,
      "size_formatted": "44.6 KB",
      "modified": 1708532592.123456,
      "is_current": true
    },
    ...
  ],
  "current_log": "realtyiq_20260221_170312.log"
}
```

#### View Log File

```http
GET /api/logs/<log_name>/?tail=1000
```

Parameters:
- `log_name`: Name of the log file
- `tail`: Number of lines to return (default: 1000, max: 10000, -1 for all)

Response:
```json
{
  "name": "realtyiq_20260221_170312.log",
  "content": "INFO 2026-02-21 17:03:12,345 django.server GET /api/...\n...",
  "total_lines": 1000,
  "size": 45678,
  "modified": 1708532592.123456
}
```

### Python Code

```python
import logging

# Get logger
logger = logging.getLogger(__name__)

# Log messages
logger.info("User logged in")
logger.warning("API rate limit approaching")
logger.error("Database connection failed", exc_info=True)
logger.debug("Request parameters: %s", params)
```

## Log Format

### File Format (Verbose)

```
INFO 2026-02-21 17:03:12,345 agent_app.views 12345 67890 User logged in
^    ^                       ^                ^     ^     ^
|    |                       |                |     |     |
|    |                       |                |     |     Message
|    |                       |                |     Thread ID
|    |                       |                Process ID
|    |                       Logger name
|    Timestamp
Log level
```

### Console Format (Simple)

```
INFO 2026-02-21 17:03:12,345 agent_app.views User logged in
^    ^                       ^                ^
|    |                       |                Message
|    |                       Logger name
|    Timestamp
Log level
```

## Log Levels

- **DEBUG**: Detailed diagnostic information (verbose)
- **INFO**: General informational messages (default)
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error messages for serious problems

## Best Practices

### 1. Use Appropriate Log Levels

```python
# Use DEBUG for detailed diagnostic info
logger.debug("Processing request with params: %s", params)

# Use INFO for general information
logger.info("Agent started: %s", agent_type)

# Use WARNING for potential issues
logger.warning("API rate limit at 80%: %s", usage)

# Use ERROR for failures
logger.error("Failed to load document: %s", error, exc_info=True)
```

### 2. Include Context

```python
# Good: Includes context
logger.info("User %s switched to agent %s", user_id, agent_name)

# Bad: Lacks context
logger.info("Agent switched")
```

### 3. Use Exception Info

```python
try:
    process_data()
except Exception as e:
    # Include exc_info=True to log full traceback
    logger.error("Data processing failed: %s", e, exc_info=True)
```

### 4. Avoid Sensitive Data

```python
# Good: Masks sensitive data
logger.info("User authenticated: %s", user_id)

# Bad: Logs sensitive data
logger.info("User login: %s / %s", username, password)  # DON'T DO THIS
```

## Log Rotation

Currently, logs are not automatically rotated. Each application start creates a new log file.

### Manual Cleanup

To clean up old logs:

```bash
# Remove logs older than 30 days
find logs/ -name "*.log" -mtime +30 -delete

# Keep only last 10 log files
cd logs && ls -t *.log | tail -n +11 | xargs rm -f
```

### Future Enhancement

Consider implementing automatic log rotation using `RotatingFileHandler` or `TimedRotatingFileHandler`:

```python
'file': {
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': str(LOG_FILE),
    'formatter': 'verbose',
    'encoding': 'utf-8',
    'maxBytes': 10 * 1024 * 1024,  # 10 MB
    'backupCount': 5,
}
```

## Troubleshooting

### Logs Not Appearing

1. **Check permissions**: Ensure the `logs/` directory is writable
   ```bash
   chmod 755 logs/
   ```

2. **Check log level**: Ensure logger is set to appropriate level
   ```python
   logger.setLevel(logging.INFO)
   ```

3. **Check file path**: Verify `CURRENT_LOG_FILE` setting
   ```python
   from django.conf import settings
   print(settings.CURRENT_LOG_FILE)
   ```

### Log File Too Large

1. **Use tail parameter**: View only last N lines
   ```
   /logs current 100
   ```

2. **Archive old logs**: Move old logs to archive folder
   ```bash
   mkdir logs/archive
   mv logs/realtyiq_202601*.log logs/archive/
   ```

3. **Implement rotation**: Add log rotation handler (see above)

## Related Files

- `agent_ui/agent_ui/settings.py` - Logging configuration
- `agent_ui/agent_app/views.py` - Log viewing endpoints
- `agent_ui/agent_app/commands/logs.py` - /logs command handler
- `agent_ui/templates/logs.html` - Web interface
- `logs/.gitignore` - Exclude logs from version control

## References

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Django Logging Configuration](https://docs.djangoproject.com/en/stable/topics/logging/)
- [Logging Best Practices](https://docs.python-guide.org/writing/logging/)
