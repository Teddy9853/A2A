#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="a2a-project-494300"
REGION="us-central1"
SERVICE="echo-a2a-agent"
REPO="a2a-lab"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE}:latest"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SERVER_DIR="${ROOT_DIR}/server"

echo "PROJECT_ID=${PROJECT_ID}"
echo "REGION=${REGION}"
echo "SERVICE=${SERVICE}"

# 1. Create Artifact Registry repo (idempotent)
gcloud artifacts repositories create "${REPO}" \
  --repository-format=docker \
  --location="${REGION}" \
  --project="${PROJECT_ID}" \
  --quiet 2>/dev/null || true

# 2. Authenticate Docker to Artifact Registry
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# 3. Build and push the container
docker build -t "${IMAGE}" "${SERVER_DIR}"
docker push "${IMAGE}"

# 4. Deploy to Cloud Run
gcloud run deploy "${SERVICE}" \
  --image="${IMAGE}" \
  --platform=managed \
  --region="${REGION}" \
  --allow-unauthenticated \
  --port=8080 \
  --project="${PROJECT_ID}"

# 5. Fetch the service URL
SERVICE_URL="$(gcloud run services describe "${SERVICE}" \
  --platform=managed \
  --region="${REGION}" \
  --format='value(status.url)' \
  --project="${PROJECT_ID}")"

echo "Initial Service URL: ${SERVICE_URL}"

# 6. Update env var so the Agent Card advertises the real cloud URL
gcloud run services update "${SERVICE}" \
  --region="${REGION}" \
  --platform=managed \
  --project="${PROJECT_ID}" \
  --update-env-vars "AGENT_URL=${SERVICE_URL}"

FINAL_URL="$(gcloud run services describe "${SERVICE}" \
  --platform=managed \
  --region="${REGION}" \
  --format='value(status.url)' \
  --project="${PROJECT_ID}")"

echo "Cloud Run service deployed successfully."
echo "Service URL: ${FINAL_URL}"
echo "Test with:"
echo "  curl ${FINAL_URL}/.well-known/agent.json"
echo "  AGENT_URL=${FINAL_URL} python client/demo.py"