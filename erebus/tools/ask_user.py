"""Agno Toolkit for interactive user Q&A.

When the agent is running in the SSE streaming context (web UI), this
tool sends a question event on the SSE stream and blocks until the user
responds via the ``POST /api/chat/answer/{stream_id}`` endpoint.

In non-streaming contexts (CLI, direct API) the tool falls back to
stdin input.
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Optional

from agno.tools.toolkit import Toolkit

logger = logging.getLogger(__name__)

# Global registry: stream_id -> threading.Queue (for passing answers back)
_answer_queues: dict[str, queue.Queue] = {}
_aq_lock = threading.Lock()

# Active stream_id for the current agent run (set externally by server.py)
_active_stream_id: Optional[str] = None
_active_stream_lock = threading.Lock()

# Callback to put events into the SSE queue (set externally by server.py)
_put_event_fn = None
_put_event_lock = threading.Lock()

_ASK_TIMEOUT = 300  # 5 minutes


def register_stream(stream_id: str, put_fn) -> None:
    """Register the SSE stream for a run.  Called by server.py before agent.run()."""
    global _active_stream_id, _put_event_fn
    with _active_stream_lock:
        _active_stream_id = stream_id
    with _put_event_lock:
        _put_event_fn = put_fn
    with _aq_lock:
        _answer_queues[stream_id] = queue.Queue()


def unregister_stream(stream_id: str) -> None:
    """Clean up after a run.  Called by server.py after agent.run()."""
    global _active_stream_id, _put_event_fn
    with _active_stream_lock:
        if _active_stream_id == stream_id:
            _active_stream_id = None
    with _put_event_lock:
        _put_event_fn = None
    with _aq_lock:
        _answer_queues.pop(stream_id, None)


def deliver_answer(stream_id: str, answer: str) -> bool:
    """Deliver an answer to a waiting ask_user call.  Called by the API endpoint."""
    with _aq_lock:
        q = _answer_queues.get(stream_id)
    if q is None:
        return False
    q.put(answer)
    return True


class AskUserTools(Toolkit):
    """Agent tool for asking the user a question interactively."""

    def __init__(self, stream_id: Optional[str] = None) -> None:
        self._stream_id = stream_id
        super().__init__(name="ask_user")
        self.register(self.ask_user)

    def ask_user(
        self,
        question: str,
        options: Optional[list[str]] = None,
    ) -> str:
        """Ask the user a question and wait for their response.

        In the web UI, this pauses the agent and surfaces the question in
        the chat interface.  The agent resumes once the user answers.

        Use this sparingly — only when genuinely blocked by ambiguity.
        For most tasks, make a reasonable assumption and proceed rather
        than interrupting the user.

        Parameters
        ----------
        question:
            The question to ask.  Be concise and specific.
        options:
            Optional list of suggested answer options to display as quick
            replies.  The user can still type a free-form response.

        Returns
        -------
        str
            The user's answer.
        """
        # Determine active stream
        stream_id = self._stream_id
        if not stream_id:
            with _active_stream_lock:
                stream_id = _active_stream_id

        if stream_id:
            return self._ask_via_sse(stream_id, question, options)
        return self._ask_via_stdin(question, options)

    def _ask_via_sse(
        self,
        stream_id: str,
        question: str,
        options: Optional[list[str]],
    ) -> str:
        """Send question event over SSE and block until answered."""
        with _aq_lock:
            if stream_id not in _answer_queues:
                _answer_queues[stream_id] = queue.Queue()
            q = _answer_queues[stream_id]

        # Emit the question as an SSE event
        with _put_event_lock:
            put_fn = _put_event_fn
        if put_fn:
            payload = {"question": question}
            if options:
                payload["options"] = options
            put_fn("ask_user", payload)
        else:
            logger.warning("ask_user: no SSE put_fn registered, falling back to stdin")
            return self._ask_via_stdin(question, options)

        # Block until answer arrives
        try:
            answer = q.get(timeout=_ASK_TIMEOUT)
            return str(answer)
        except queue.Empty:
            return "[No response received within timeout]"

    def _ask_via_stdin(
        self,
        question: str,
        options: Optional[list[str]],
    ) -> str:
        """Fallback: read answer from stdin."""
        prompt = f"\n❓ {question}"
        if options:
            opts = "\n".join(f"  {i+1}. {o}" for i, o in enumerate(options))
            prompt += f"\nOptions:\n{opts}"
        prompt += "\n> "
        try:
            return input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            return "[User did not answer]"
