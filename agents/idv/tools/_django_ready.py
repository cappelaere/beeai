"""
Lazy Django setup for IDV tools.
Call get_identity_verification_model() only when a tool runs, not at import time,
so agent config can be loaded during Django's AppConfig.ready() without
 triggering "populate() isn't reentrant".
"""


def get_identity_verification_model():
    import os

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_ui.settings")
    if not django.apps.apps.ready:
        django.setup()
    from agent_app.models import IdentityVerification

    return IdentityVerification
