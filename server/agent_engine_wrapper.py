"""Reasoning Engine wrapper for the Echo A2A Agent."""

from __future__ import annotations

import asyncio
import uuid
from types import SimpleNamespace

try:
    from server.handlers import handle_task
except ImportError:
    from handlers import handle_task


class EchoAgent:
    """Agent Engine wrapper for the Echo A2A Agent."""

    def set_up(self):
        """Called once when the container starts."""
        print("EchoAgent.set_up() called")

    @staticmethod
    def _run_async(coro):
        """Run an async coroutine from a synchronous context."""
        try:
            return asyncio.run(coro)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()

    def query(
        self,
        *,
        task_id: str | None = None,
        message_text: str,
        session_id: str | None = None,
    ) -> dict:
        """
        Agent Engine calls this method for each request.
        We mirror the A2A task send/receive pattern here.
        """
        fake_request = SimpleNamespace(
            id=task_id or str(uuid.uuid4()),
            sessionId=session_id,
            message=SimpleNamespace(
                role="user",
                parts=[SimpleNamespace(type="text", text=message_text)],
            ),
            metadata=None,
        )

        result_text = self._run_async(handle_task(fake_request))

        return {
            "id": fake_request.id,
            "status": {
                "state": "completed",
                "message": None,
            },
            "artifacts": [
                {
                    "index": 0,
                    "name": "result",
                    "parts": [
                        {
                            "type": "text",
                            "text": result_text,
                        }
                    ],
                }
            ],
        }