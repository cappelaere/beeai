"""
Django settings for agent_ui project.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Add parent directory to path so we can import agents module
REPO_ROOT = BASE_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Load environment variables from .env file in the root directory
env_path = BASE_DIR.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key-change-in-production")
DEBUG = os.environ.get("DEBUG", "True").lower() in ("1", "true", "yes")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "agent_app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "agent_app.middleware.workflow_sync.WorkflowSyncMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "agent_app.middleware.prometheus_middleware.PrometheusMiddleware",
]

# When run from repo root (uvicorn), settings load as agent_ui.agent_ui.settings; use full path.
# When run from agent_ui/ (manage.py), settings load as agent_ui.settings; use short path.
_settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")
if _settings_module == "agent_ui.agent_ui.settings":
    ROOT_URLCONF = "agent_ui.agent_ui.urls"
    WSGI_APPLICATION = "agent_ui.agent_ui.wsgi.application"
    ASGI_APPLICATION = "agent_ui.agent_ui.asgi.application"
else:
    ROOT_URLCONF = "agent_ui.urls"
    WSGI_APPLICATION = "agent_ui.wsgi.application"
    ASGI_APPLICATION = "agent_ui.asgi.application"

# Workflows dir at repo root: per-workflow run result templates live in workflows/<workflow_id>/run_result.html
WORKFLOWS_TEMPLATES_DIR = REPO_ROOT / "workflows"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates", WORKFLOWS_TEMPLATES_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "agent_app.context_processors.observability_settings",
                "agent_app.context_processors.version_info",
                "agent_app.context_processors.section_508_settings",
                "agent_app.context_processors.model_choices",
                "agent_app.context_processors.agent_choices",
                "agent_app.context_processors.user_context",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Django Channels Configuration
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL", "redis://localhost:6379/0")],
        },
    },
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR.parent / "diagrams",  # Add diagrams folder as static files
]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR.parent / "media"  # Store media files in project root

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging Configuration
import logging
from datetime import datetime

LOG_DIR = BASE_DIR.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Create timestamped log file name
LOG_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"realtyiq_{LOG_TIMESTAMP}.log"


class HealthCheckFilter(logging.Filter):
    """Filter out health check and polling endpoint logs"""

    def filter(self, record):
        # Filter out frequent polling endpoints
        excluded_paths = ["/api/tasks/count/", "/api/health/", "/health/", "/ping/"]
        return not any(path in record.getMessage() for path in excluded_paths)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "health_check": {
            "()": HealthCheckFilter,
        },
    },
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "()": f"{__name__.rsplit('.', 1)[0]}.log_formatter.DjangoStyleFormatter",
            "format": "%(levelname_colored)s %(asctime)s %(name)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": True,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "filters": ["health_check"],
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": str(LOG_FILE),
            "formatter": "verbose",
            "encoding": "utf-8",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "agent_app": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "agent_runner": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "cache": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
            "filters": ["health_check"],
        },
    },
}

# Store log file path for access by views
CURRENT_LOG_FILE = LOG_FILE
