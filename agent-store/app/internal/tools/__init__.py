# app/internal/tools/__init__.py
"""
Internal tools module.

This module manages the registry of internal tools and imports all tool definitions
to register them automatically.
"""

from app.internal.tools.registry import register_internal_tool, InternalToolDef, get_internal_tool, get_all_internal_tools  # noqa: F401

# Import all tool definitions - this triggers their registration
from app.internal.tools import definitions  # noqa: F401
