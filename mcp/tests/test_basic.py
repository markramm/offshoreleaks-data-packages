"""Basic tests for the offshore leaks MCP server."""

import pytest

from offshore_leaks_mcp import __version__


def test_version() -> None:
    """Test that version is properly defined."""
    assert __version__ == "0.1.0"


def test_package_imports() -> None:
    """Test that package can be imported without errors."""
    import offshore_leaks_mcp  # noqa: F401

    # Basic smoke test
    assert offshore_leaks_mcp.__version__ is not None
    assert offshore_leaks_mcp.__author__ is not None


@pytest.mark.asyncio  # type: ignore[misc]
async def test_placeholder() -> None:
    """Placeholder test for async functionality."""
    # This will be replaced with actual server tests
    assert True
