"""Agent Card definition for the A2A lab server."""

from __future__ import annotations

import os


AGENT_CARD = {
    "id": "echo-agent-v1",
    "name": "Echo Agent",
    "version": "1.0.0",
    "description": "A simple agent that echoes back any text it receives.",
    "url": os.getenv("AGENT_URL", "http://localhost:8000"),
    "contact": {
        "email": "student@example.com",
    },
    "capabilities": {
        "streaming": False,
        "pushNotifications": False,
    },
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain"],
    "skills": [
        {
            "id": "echo",
            "name": "Echo",
            "description": "Returns the user message verbatim.",
            "inputModes": ["text/plain"],
            "outputModes": ["text/plain"],
        },
        {
            "id": "summarise",
            "name": "Summarise",
            "description": "Returns a one-sentence summary of the provided text.",
            "inputModes": ["text/plain"],
            "outputModes": ["text/plain"],
        },
    ],
}


def validate_card(card: dict) -> bool:
    """Return True if the Agent Card contains all required top-level fields."""
    required_top_level = {
        "id",
        "name",
        "version",
        "description",
        "url",
        "contact",
        "capabilities",
        "defaultInputModes",
        "defaultOutputModes",
        "skills",
    }

    if not isinstance(card, dict):
        return False

    if not required_top_level.issubset(card.keys()):
        return False

    if not isinstance(card.get("contact"), dict):
        return False

    if "email" not in card["contact"]:
        return False

    capabilities = card.get("capabilities", {})
    if not isinstance(capabilities, dict):
        return False

    if "streaming" not in capabilities or "pushNotifications" not in capabilities:
        return False

    skills = card.get("skills", [])
    if not isinstance(skills, list) or len(skills) < 2:
        return False

    required_skill_fields = {"id", "name", "description", "inputModes", "outputModes"}
    for skill in skills:
        if not isinstance(skill, dict):
            return False
        if not required_skill_fields.issubset(skill.keys()):
            return False

    return True