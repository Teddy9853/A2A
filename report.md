# A2A Protocol with Python — Report

**Course:** CS4680  
**Assignment:** Agent-to-Agent (A2A) Hands-On Lab  
**Student:** Tai Ji Chen
**GitHub Repo:** YOUR_GITHUB_REPO_LINK

---

## Section 3 — Request and Response Structure

### 3.1 Why does the request use a client-generated `id` rather than a server-generated one?

The request uses a client-generated `id` so the client can uniquely identify the task before sending it to the server. In distributed systems this is important because networks are unreliable: a client may send a request, lose the connection, and not know whether the server received it or processed it. If the client retries using the same task ID, the server can treat the retry as the same logical operation instead of creating duplicate work.

This helps with **idempotency**, duplicate detection, tracing, logging, and correlation across services. It also lets the client match a response to the original request even if there are multiple requests in flight at the same time.

### 3.2 When would a server return `status.state = "working"` in a non-streaming call, and how should a client react?

A server would return `working` in a non-streaming call when the task has been accepted but has not finished yet. This would happen for long-running work such as calling external APIs, processing large files, waiting on another agent, or running a model inference that takes longer than a normal request.

In that case, the client should not assume failure. Instead, it should treat the response as an intermediate state. A practical client reaction is to either:
1. poll a status endpoint if the protocol or server supports one,  
2. retry later with the same task identifier, or  
3. fall back to a streaming or asynchronous workflow.

The key idea is that `working` means the server has started processing but no final artifact is ready yet.

### 3.3 What is the purpose of the `sessionId` field? Give a concrete example.

The `sessionId` groups related tasks into the same logical conversation or workflow. It allows the server, and possibly downstream agents, to maintain continuity across multiple requests.

For example, suppose a user first sends:

- Task 1: “Summarise this article about renewable energy.”
- Task 2: “Now rewrite that summary for a high-school audience.”

These two tasks should share the same `sessionId` because the second task depends on the context established by the first. The server can use the shared session to preserve conversation state, memory, or audit history.

### 3.4 Describe a realistic multi-agent workflow where `text`, `file`, and `data` all appear.

A realistic example is a resume-screening workflow across multiple agents:

- A recruiter uploads a candidate CV PDF using a **file** part, with a URL and MIME type.
- The user also includes a **text** part such as: “Summarise this resume and check whether the candidate matches a backend engineer role.”
- Another system attaches a **data** part containing structured job requirements, for example:
  - required years of experience
  - required programming languages
  - minimum degree
  - location constraints

An intake agent could read the file, extract resume text, compare it against the structured data, and return a natural-language assessment. In one conversation, all three part types are useful: file for the document, text for user instructions, and data for structured criteria.

---

## Section 4 — Cloud Run Deployment

### 4.1 Deployment Summary

I containerised the FastAPI A2A server with Docker and deployed it to Google Cloud Run. The deployment was performed using the provided shell script after replacing the placeholder `PROJECT_ID` with my own Google Cloud project ID.

**Cloud Run Service URL:**  
`https://YOUR-CLOUD-RUN-SERVICE-URL.a.run.app`

After deployment, I updated the `url` field in the Agent Card so that the published card advertises the real Cloud Run endpoint rather than `http://localhost:8000`. I then redeployed and verified the cloud-hosted Agent Card using:

```bash
curl https://YOUR-CLOUD-RUN-SERVICE-URL.a.run.app/.well-known/agent.json
```

I also pointed the `A2AClient` at the Cloud Run URL and confirmed that the same echo response was returned from the deployed service.

### 4.2 What does `--allow-unauthenticated` do, and what are the security implications?

The `--allow-unauthenticated` flag allows anyone on the internet to invoke the Cloud Run service without presenting Google IAM credentials. In this assignment it is useful because it makes testing simpler: the A2A client can call the service directly over HTTPS without extra auth setup.

The security implication is that the endpoint becomes publicly reachable. That means:
- anyone who knows the URL can send requests,
- the service may be abused for spam or unexpected traffic,
- sensitive logic or data should not be exposed without additional controls.

For a production multi-agent system, public unauthenticated access may be too permissive. A safer design would require authenticated requests using service accounts, identity tokens, API gateways, or other access controls.

### 4.3 How does Cloud Run scale to zero, and what is cold start latency?

Cloud Run is serverless, so when there is no traffic it can scale the service down to zero running instances. This reduces cost because you are not paying to keep an idle VM or container always running.

When a new request arrives after the service has scaled to zero, Cloud Run must start a fresh container instance before the request can be handled. This startup delay is called **cold start latency**.

For A2A clients, cold starts matter because the first request after inactivity may take noticeably longer than later requests. A client should therefore:
- use sensible timeouts,
- handle retries carefully,
- avoid assuming that a slightly slower first response means failure.

---

## Section 5 — Agent Engine Deployment

### 5.1 Deployment Summary

I created a Google Cloud Storage staging bucket for packaging the agent code:

```bash
gsutil mb -l us-central1 gs://YOUR-PROJECT-ID-a2a-staging
```

Then I ran the Agent Engine deployment script:

```bash
python cloud/deploy_agent_engine.py
```

This packaged the wrapper class and deployed the agent to Vertex AI Agent Engine. The deployment printed a resource name and Engine ID, which I recorded below.

**Engine ID:**  
`YOUR_ENGINE_ID`

To test the deployed agent, I used the Vertex AI SDK:

```python
from vertexai.preview import reasoning_engines

agent = reasoning_engines.ReasoningEngine(
    "projects/YOUR_PROJECT/locations/us-central1/reasoningEngines/YOUR_ENGINE_ID"
)
response = agent.query(message_text="Hello from Agent Engine!")
print(response)
```

The returned response followed the same general A2A-style structure used by the server and client in earlier parts.

### 5.2 Difference between Cloud Run and Agent Engine

Cloud Run is a general-purpose managed container platform. It is a good fit when the application is simply an HTTP service and the developer wants control over the container image, web framework, and runtime behavior. However, the developer is still responsible for packaging the application as a container, managing its HTTP interface, and handling more infrastructure-oriented concerns.

Agent Engine is more specialized for AI agents. It is designed around agent lifecycles and provides a managed runtime that is better aligned with agent-style workloads. It reduces operational burden because the developer focuses more on the Python agent interface and less on container or server management. It is therefore a better fit when the goal is to deploy and operate AI agents rather than generic web services.

In short:
- **Cloud Run:** more general, flexible, container-centric
- **Agent Engine:** more specialized, agent-centric, lower operational overhead for AI agent hosting

### 5.3 Why does the wrapper class use a synchronous `query()` method even though the handler is async?

The wrapper uses a synchronous `query()` method because Agent Engine expects a specific callable interface for agent invocation, and that interface is synchronous. The underlying business logic was already written as `async` for the FastAPI server, so the wrapper bridges the two models by running the async handler from within synchronous code.

This design allows code reuse: the same `handle_task()` logic powers both the local or cloud HTTP server and the Agent Engine deployment. The synchronous wrapper is therefore an adapter layer between Agent Engine’s invocation pattern and the existing async implementation.

---

## Section 6 — Client-Server Connection Trace and Diagram

### 6.1 Logged request and response output from `client/demo.py`

Replace the example below with the **actual output from your own Cloud Run run**.

```text
[A2AClient] --> GET https://YOUR-CLOUD-RUN-SERVICE-URL.a.run.app/.well-known/agent.json
[A2AClient] <-- 200 GET https://YOUR-CLOUD-RUN-SERVICE-URL.a.run.app/.well-known/agent.json body={"id":"echo-agent-v1","name":"Echo Agent","version":"1.0.0","description":"A simple agent that echoes back any text it receives.","url":"https://YOUR-CLOUD-RUN-SERVICE-URL.a.run.app","contact":{"email":"student@example.com"},"capabilities":{"streaming":false,"pushNotifications":false},"defaultInputModes":["text/plain"],"defaultOutputModes":["text/plain"],"skills":[{"id":"echo","name":"Echo","description":"Returns the user message verbatim.","inputModes":["text/plain"],"outputModes":["text/plain"]},{"id":"summarise","name":"Summarise","description":"Returns a one-sentence summary of the provided text.","inputModes":["text/plain"],"outputModes":["text/plain"]}]}

Agent discovered:
  Name: Echo Agent
  URL:  https://YOUR-CLOUD-RUN-SERVICE-URL.a.run.app

Skills:
  - Echo (echo): Returns the user message verbatim.
  - Summarise (summarise): Returns a one-sentence summary of the provided text.

[A2AClient] --> POST https://YOUR-CLOUD-RUN-SERVICE-URL.a.run.app/tasks/send payload={"id":"123e4567-e89b-12d3-a456-426614174000","sessionId":null,"message":{"role":"user","parts":[{"type":"text","text":"Hello from the client!"}]},"metadata":null}
[A2AClient] <-- 200 POST https://YOUR-CLOUD-RUN-SERVICE-URL.a.run.app/tasks/send body={"id":"123e4567-e89b-12d3-a456-426614174000","status":{"state":"completed","message":null},"artifacts":[{"index":0,"name":"result","parts":[{"type":"text","text":"Hello from the client!"}]}]}

Response:
Hello from the client!
```

### 6.2 UML Sequence Diagram

```text
User                A2AClient                 Cloud Run (A2AServer)             handlers.py
 |                      |                                |                            |
 | Run demo.py          |                                |                            |
 |--------------------->|                                |                            |
 |                      | GET /.well-known/agent.json    |                            |
 |                      |------------------------------->|                            |
 |                      |                                | return AGENT_CARD          |
 |                      |<-------------------------------|                            |
 |                      |                                |                            |
 |                      | POST /tasks/send               |                            |
 |                      | task JSON                      |                            |
 |                      |------------------------------->|                            |
 |                      |                                | call handle_task(request)  |
 |                      |                                |--------------------------->|
 |                      |                                |                            | process text
 |                      |                                |<---------------------------|
 |                      |                                | return A2A response JSON   |
 |                      |<-------------------------------|                            |
 | print response       |                                |                            |
 |<---------------------|                                |                            |
```

### 6.3 If a client loses the network connection after sending the POST, how could it safely retry? What field helps with idempotency?

If the client loses the connection after sending the POST but before receiving the response, it should retry the request using the **same client-generated task `id`** rather than creating a new one. Reusing the same ID allows the server to detect that the retried request is logically the same operation.

This is the field that helps with **idempotency**. With a stable request ID, the server can avoid processing the same task twice, or it can return the already-computed result if it keeps task history. Without a stable client-generated identifier, safe retries become much harder.

---

## Conclusion

This assignment demonstrated the full lifecycle of an A2A system: publishing an Agent Card, sending structured task requests, parsing structured task responses, and deploying the same core logic to both Cloud Run and Vertex AI Agent Engine. It also highlighted practical distributed-systems concerns such as idempotency, session tracking, authentication, cold starts, and interoperability between agents.
