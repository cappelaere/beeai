"""
Application constants. Use these instead of magic literals for session/default user.
"""

# Default/fallback user id when session has no user_id (e.g. anonymous or legacy).
# Use where "anonymous" or "default user" is an explicit design choice; where auth
# is required, check for user_id and return 401/403 instead of defaulting.
ANONYMOUS_USER_ID = 9
