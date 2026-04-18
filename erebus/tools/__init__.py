"""Extra built-in tools for the Erebus agent."""

from erebus.tools.ask_user import AskUserTools
from erebus.tools.code_agent import CodeAgentTools
from erebus.tools.file_edit import FileEditTools
from erebus.tools.glob_tool import GlobTools
from erebus.tools.grep_tool import GrepTools
from erebus.tools.notify import NotifyTools
from erebus.tools.obsidian import ObsidianTools
from erebus.tools.repl import REPLTools
from erebus.tools.scheduler import SchedulerTools
from erebus.tools.todo import TodoTools
from erebus.tools.web import WebFetchTools
from erebus.tools.workspace import WorkspaceTools

__all__ = [
    "AskUserTools",
    "CodeAgentTools",
    "FileEditTools",
    "GlobTools",
    "GrepTools",
    "NotifyTools",
    "ObsidianTools",
    "REPLTools",
    "SchedulerTools",
    "TodoTools",
    "WebFetchTools",
    "WorkspaceTools",
]
