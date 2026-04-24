# A2A Lab — Echo Agent

This repository contains a minimal but functional Agent-to-Agent (A2A) system built in Python. It includes:

- an A2A Server implemented with FastAPI
- an A2A Client implemented with `httpx`
- Docker packaging for Google Cloud Run
- a wrapper for deployment to Vertex AI Agent Engine

---

## Project Structure

```text
a2a-lab/
  server/
    main.py
    agent_card.py
    handlers.py
    agent_engine_wrapper.py
    Dockerfile
    requirements.txt
  client/
    client.py
    demo.py
  cloud/
    deploy_cloud_run.sh
    deploy_agent_engine.py
  report.md
  README.md
```

---

## Requirements

Install the following before running the lab:

- Python 3.10 or newer
- `pip`
- `venv`
- Docker Desktop
- Google Cloud CLI (`gcloud`)
- A Google Cloud project with billing enabled

Enable these Google Cloud APIs:
- Cloud Run
- Artifact Registry
- Vertex AI

---

## 1. Local Environment Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install fastapi uvicorn httpx pydantic google-cloud-aiplatform google-auth requests
```

---

## 2. Running the A2A Server Locally

Start the server with Uvicorn:

```bash
uvicorn server.main:app --reload --port 8000
```

### Test the local endpoints

Fetch the Agent Card:

```bash
curl http://localhost:8000/.well-known/agent.json
```

Check health:

```bash
curl http://localhost:8000/health
```

Send a normal task:

```bash
curl -X POST http://localhost:8000/tasks/send \
  -H "Content-Type: application/json" \
  -d '{"id":"t1","message":{"role":"user","parts":[{"type":"text","text":"Hello A2A"}]}}'
```

Send a summarise task:

```bash
curl -X POST http://localhost:8000/tasks/send \
  -H "Content-Type: application/json" \
  -d '{"id":"t2","message":{"role":"user","parts":[{"type":"text","text":"!summarise This is a long message to summarise"}]}}'
```

---

## 3. Running the A2A Client Locally

With the server running locally:

```bash
python client/demo.py
```

The client will:
1. fetch the Agent Card
2. print the agent name and skills
3. send a task to `/tasks/send`
4. print the returned text response

---

## 4. Server Files

### `server/agent_card.py`
Defines the Agent Card metadata:
- agent ID
- name
- version
- capabilities
- contact info
- skills

### `server/handlers.py`
Contains the task-processing logic:
- echoes plain text input
- returns a mock summary when the message starts with `!summarise`

### `server/main.py`
Implements the FastAPI server and exposes:
- `GET /.well-known/agent.json`
- `GET /health`
- `POST /tasks/send`

---

## 5. Client Files

### `client/client.py`
Implements a minimal A2A client with:
- Agent Card discovery
- task construction
- task sending
- response parsing
- context manager support

### `client/demo.py`
Shows an end-to-end demo using the client.

---

## 6. Docker Build for Cloud Run

The Dockerfile is in `server/Dockerfile`.

You can build the container manually with:

```bash
docker build -t echo-a2a-agent ./server
```

---

## 7. Deploying to Google Cloud Run

Edit `cloud/deploy_cloud_run.sh` and replace:

```bash
PROJECT_ID="your-gcp-project-id"
```

with your real Google Cloud project ID.

Then run:

```bash
bash cloud/deploy_cloud_run.sh
```

This script:
1. creates an Artifact Registry repository if needed
2. authenticates Docker to Artifact Registry
3. builds and pushes the server image
4. deploys the image to Cloud Run
5. prints the service URL
6. updates the `AGENT_URL` environment variable so the Agent Card advertises the deployed URL

### Cloud Run Service URL

Replace this placeholder with your real deployed URL:

```text
https://YOUR-CLOUD-RUN-SERVICE-URL.a.run.app
```

### Verify the deployed Agent Card

```bash
curl https://YOUR-CLOUD-RUN-SERVICE-URL.a.run.app/.well-known/agent.json
```

### Run the client against Cloud Run

```bash
AGENT_URL=https://YOUR-CLOUD-RUN-SERVICE-URL.a.run.app python client/demo.py
```

---

## 8. Deploying to Vertex AI Agent Engine

First create a staging bucket:

```bash
gsutil mb -l us-central1 gs://YOUR-PROJECT-ID-a2a-staging
```

Then edit `cloud/deploy_agent_engine.py` and replace:

```python
PROJECT_ID = "your-gcp-project-id"
```

with your real project ID.

Run the deployment:

```bash
python cloud/deploy_agent_engine.py
```

The script prints:
- the full resource name
- the Engine ID

### Test the deployed Agent Engine

```python
from vertexai.preview import reasoning_engines

agent = reasoning_engines.ReasoningEngine(
    "projects/YOUR_PROJECT/locations/us-central1/reasoningEngines/YOUR_ENGINE_ID"
)
response = agent.query(message_text="Hello from Agent Engine!")
print(response)
```

---

## 9. Notes on Cloud Deployment

### Public access
The Cloud Run deployment uses `--allow-unauthenticated`, which makes the service publicly accessible over HTTPS.

### Cold starts
Cloud Run can scale to zero when idle. The first request after inactivity may be slower because a new container instance must start.

---

## 10. Submission Checklist

Before submitting, verify that:

- `server/` contains:
  - `main.py`
  - `agent_card.py`
  - `handlers.py`
  - `Dockerfile`
  - `requirements.txt`

- `client/` contains:
  - `client.py`
  - `demo.py`

- `cloud/` contains:
  - `deploy_cloud_run.sh`
  - `deploy_agent_engine.py`

- `report.md` contains written answers for:
  - Section 3
  - Section 4
  - Section 5
  - Section 6

- `README.md` explains:
  - environment setup
  - how to run the server locally
  - how to run the client locally
  - how to deploy to Cloud Run
  - how to deploy to Agent Engine

- the Cloud Run Service URL is listed in this README

---

## 11. Cleanup

To delete the Cloud Run service after testing:

```bash
gcloud run services delete echo-a2a-agent --region=us-central1
```
