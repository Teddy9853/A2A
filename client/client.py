"""Minimal A2A-compliant client."""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional

import httpx


class A2AClient:
    """Minimal A2A-compliant client."""

    def __init__(self, agent_url: str):
        self.agent_url = agent_url.rstrip("/")
        self._card: Optional[dict[str, Any]] = None
        self._http = httpx.Client(timeout=30)

    def __enter__(self) -> "A2AClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    @staticmethod
    def _abbrev(payload: Any, limit: int = 220) -> str:
        """Return a shortened JSON-ish string for logging."""
        if isinstance(payload, (dict, list)):
            text = json.dumps(payload, ensure_ascii=False)
        else:
            text = str(payload)

        if len(text) <= limit:
            return text
        return text[:limit] + "...<truncated>"

    def fetch_agent_card(self) -> dict:
        """Fetch and cache the Agent Card."""
        if self._card is None:
            url = f"{self.agent_url}/.well-known/agent.json"
            print(f"[A2AClient] --> GET {url}")

            resp = self._http.get(url)
            print(
                f"[A2AClient] <-- {resp.status_code} GET {url} "
                f"body={self._abbrev(resp.text)}"
            )

            resp.raise_for_status()
            self._card = resp.json()

        return self._card

    def get_skills(self) -> list:
        """Return the skills list from the cached Agent Card."""
        card = self.fetch_agent_card()
        return card.get("skills", [])

    def _build_task(
        self,
        text: str,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict:
        """Build a conformant A2A task payload."""
        return {
            "id": task_id or str(uuid.uuid4()),
            "sessionId": session_id,
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": text}],
            },
            "metadata": metadata,
        }

    def _validate_text_modes(self) -> None:
        """Ensure the remote agent supports text/plain input and output."""
        card = self.fetch_agent_card()

        input_modes = card.get("defaultInputModes", [])
        output_modes = card.get("defaultOutputModes", [])

        if "text/plain" not in input_modes:
            raise RuntimeError("Remote agent does not advertise text/plain input support.")

        if "text/plain" not in output_modes:
            raise RuntimeError("Remote agent does not advertise text/plain output support.")

    def send_task(self, text: str, **kwargs) -> dict:
        """Send a task and return the parsed response."""
        self.fetch_agent_card()
        self._validate_text_modes()

        payload = self._build_task(text, **kwargs)
        url = f"{self.agent_url}/tasks/send"

        print(f"[A2AClient] --> POST {url} payload={self._abbrev(payload)}")
        resp = self._http.post(url, json=payload)
        print(
            f"[A2AClient] <-- {resp.status_code} POST {url} "
            f"body={self._abbrev(resp.text)}"
        )

        resp.raise_for_status()
        data = resp.json()

        state = data.get("status", {}).get("state")
        if state != "completed":
            message = data.get("status", {}).get("message")
            raise RuntimeError(f"A2A task did not complete successfully. state={state!r}, message={message!r}")

        return data

    @staticmethod
    def extract_text(response: dict) -> str:
        """Return text from the first artifact, or a file URL if the first part is a file."""
        artifacts = response.get("artifacts", [])
        if not artifacts:
            return ""

        first_artifact = artifacts[0]
        parts = first_artifact.get("parts", [])
        if not parts:
            return ""

        first_part = parts[0]

        if first_part.get("type") == "file":
            file_obj = first_part.get("file", {})
            return file_obj.get("url", "")

        if first_part.get("type") == "text":
            return first_part.get("text", "")

        return ""

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()