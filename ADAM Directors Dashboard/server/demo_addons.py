#!/usr/bin/env python3
"""
DEPRECATED - superseded 2026-05-04.

The director views formerly drafted here have been promoted into a
production module: dashboard_views.py. This file is retained empty so
the wiring import chain from any older clone of this deployment fails
cleanly with a clear message rather than silently mounting outdated
routes.

Do not import this module. Import dashboard_views instead.
"""

raise ImportError(
    "demo_addons has been superseded by dashboard_views. "
    "Update netstreamx_app.py to import dashboard_views.register."
)
