"""Task handlers for the A2A lab server."""

from __future__ import annotations


async def handle_task(request) -> str:
    """Process an incoming A2A task and return a text result."""
    text_parts = [
        getattr(part, "text", "")
        for part in request.message.parts
        if getattr(part, "type", None) == "text"
    ]
    combined = " ".join(part.strip() for part in text_parts if part and part.strip()).strip()

    if not combined:
        return "No text content received."

    first_word = combined.split(maxsplit=1)[0]

    if first_word == "!summarise":
        remainder = combined.split(maxsplit=1)[1] if len(combined.split(maxsplit=1)) > 1 else ""
        if remainder:
            return (
                "Mock summary: The text describes a single main idea and can be "
                "condensed into one short sentence."
            )
        return "Mock summary: No text was provided to summarise."

    return combined