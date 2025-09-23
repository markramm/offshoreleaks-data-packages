"""Offshore Leaks MCP Server.

A Model Context Protocol server for querying the ICIJ Offshore Leaks database.
"""

__version__ = "0.1.0"
__author__ = "Research Team"
__email__ = "research@example.com"

from .config import Config, load_config
from .server import OffshoreLeaksServer

# MCP server is conditionally imported (requires Python 3.10+)
try:
    from .mcp_server import MCPOffshoreLeaksServer

    __all__ = ["OffshoreLeaksServer", "MCPOffshoreLeaksServer", "Config", "load_config"]
except ImportError:
    __all__ = ["OffshoreLeaksServer", "Config", "load_config"]
