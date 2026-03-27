"""
Constants for website analytics collection and filtering.
"""

MAX_LOCATION_VALUE_LENGTH = 120
MAX_QUERY_VALUE_LENGTH = 256
MAX_QUERY_VALUES_PER_KEY = 5

# Extra defensive denylist: these are dropped even if allowlisted by mistake.
SENSITIVE_QUERY_PARAM_DENYLIST = {
    "password",
    "passwd",
    "pwd",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "auth",
    "code",
    "secret",
    "apikey",
    "api_key",
    "key",
    "session",
    "sessionid",
    "csrf",
    "csrftoken",
}

# Trusted proxy/CDN headers (first non-empty wins per field).
DEFAULT_LOCATION_HEADER_MAP = {
    "country": (
        "CF-IPCountry",
        "X-Country-Code",
        "X-AppEngine-Country",
        "CloudFront-Viewer-Country",
    ),
    "state": (
        "X-Region-Code",
        "X-Region",
        "CloudFront-Viewer-Country-Region",
    ),
    "city": (
        "X-City",
        "X-AppEngine-City",
        "CloudFront-Viewer-City",
    ),
}

# Paths never treated as page-view candidates.
DEFAULT_ANALYTICS_EXCLUDED_PATH_PREFIXES = (
    "/api/",
    "/static/",
    "/media/",
    "/metrics/",
    "/prometheus/",
    "/health",
    "/ping",
    "/favicon.ico",
)
