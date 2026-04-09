"""Built-in web-search skill using DuckDuckGo."""

from agno.tools.duckduckgo import DuckDuckGoTools

SKILL_META = {
    "name": "web_search",
    "description": "Search the web using DuckDuckGo for current information.",
}


def tools():
    """Return the DuckDuckGo toolkit."""
    return [DuckDuckGoTools()]
