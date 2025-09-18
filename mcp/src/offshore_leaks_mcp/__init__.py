"""Offshore Leaks MCP Server.

A Model Context Protocol server for querying the ICIJ Offshore Leaks database.
"""

__version__ = "0.1.0"
__author__ = "Research Team"
__email__ = "research@example.com"

from .config import Config, load_config
from .server import OffshoreLeaksServer

__all__ = ["OffshoreLeaksServer", "Config", "load_config"]
