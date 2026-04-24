"""Deploy the EchoAgent wrapper to Vertex AI Reasoning Engine."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import vertexai
from vertexai.preview import reasoning_engines

PROJECT_ID = "a2a-project-494300"
REGION = "us-central1"
STAGING_BUCKET = f"gs://{PROJECT_ID}-a2a-staging"
GCS_DIR_NAME = "a2a-lab"

ROOT_DIR = Path(__file__).resolve().parent.parent
SERVER_DIR = ROOT_DIR / "server"

sys.path.insert(0, str(SERVER_DIR))
from agent_engine_wrapper import EchoAgent  # noqa: E402


def main() -> None:
    vertexai.init(
        project=PROJECT_ID,
        location=REGION,
        staging_bucket=STAGING_BUCKET,
    )

    remote_agent = reasoning_engines.ReasoningEngine.create(
        EchoAgent(),
        requirements=[
            "fastapi==0.111.0",
            "uvicorn==0.29.0",
            "pydantic==2.7.0",
        ],
        extra_packages=[str(SERVER_DIR)],
        display_name="Echo A2A Agent",
        description="A2A Lab - Echo Agent on Agent Engine",
        gcs_dir_name=GCS_DIR_NAME,
        sys_version="3.11",
    )

    print("Deployed! Resource name:", remote_agent.resource_name)
    print("Engine ID:", remote_agent.resource_name.split("/")[-1])


if __name__ == "__main__":
    main()