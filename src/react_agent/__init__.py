"""React Agent.

This module defines a custom reasoning and action agent graph.
It invokes tools in a simple loop.
"""

from react_agent.graph import graph

from utils.disable_ssl import patch_global_requests
from utils.uipath_config import get_uipath_config

__all__ = ["graph"]
