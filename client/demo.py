"""End-to-end demo script for the A2A client."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from client import A2AClient  # noqa: E402


def main() -> None:
    agent_url = os.getenv("AGENT_URL", "http://localhost:8000")

    with A2AClient(agent_url) as client:
        card = client.fetch_agent_card()

        print("\nAgent discovered:")
        print(f"  Name: {card.get('name')}")
        print(f"  URL:  {card.get('url')}")

        print("\nSkills:")
        for skill in client.get_skills():
            print(f"  - {skill['name']} ({skill['id']}): {skill['description']}")

        response = client.send_task("Hello from the client!")
        result_text = client.extract_text(response)

        print("\nResponse:")
        print(result_text)


if __name__ == "__main__":
    main()