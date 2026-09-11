#!/usr/bin/env bash
# ==============================================================================
# LifeBridge AI — Google Cloud Run Automated Deployment Script
# Deploys with Secret Manager integration and non-root secure container
# ==============================================================================

set -euo pipefail

SERVICE_NAME="lifebridge-ai"
REGION="${REGION:-us-central1}"

echo "============================================================"
echo " LifeBridge AI — Google Cloud Run Deployment"
echo "============================================================"

# Verify gcloud CLI is installed
if ! command -v gcloud &> /dev/null; then
    echo "ERROR: 'gcloud' CLI is not installed or not in PATH."
    echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Detect current project
PROJECT_ID=$(gcloud config get-value project 2> /dev/null || true)
if [ -z "${PROJECT_ID}" ] || [ "${PROJECT_ID}" = "(unset)" ]; then
    echo "ERROR: No active GCP project found."
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "Active Project: ${PROJECT_ID}"
echo "Target Region:  ${REGION}"
echo "Service Name:   ${SERVICE_NAME}"
echo ""

# Enable required GCP APIs
echo "Step 1: Enabling Cloud Run, Cloud Build, and Secret Manager APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    --project="${PROJECT_ID}"

# Optional Secret Manager integration
SECRET_NAME="gemini-api-key"
SECRET_FLAG=""

if gcloud secrets describe "${SECRET_NAME}" --project="${PROJECT_ID}" &> /dev/null; then
    echo "Step 2: Found Secret Manager secret '${SECRET_NAME}'. Binding to service..."
    SECRET_FLAG="--set-secrets=GEMINI_API_KEY=${SECRET_NAME}:latest"
else
    echo "Step 2: No secret '${SECRET_NAME}' found. The service will operate in deterministic fallback mode until configured."
    echo "To configure Secret Manager later:"
    echo "  echo -n 'YOUR_API_KEY' | gcloud secrets create ${SECRET_NAME} --data-file=-"
fi

# Build and deploy directly via Cloud Run source deploy
echo "Step 3: Building container and deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --source=. \
    --platform=managed \
    --region="${REGION}" \
    --allow-unauthenticated \
    --set-env-vars="GEMINI_MODEL=gemini-2.5-flash" \
    ${SECRET_FLAG} \
    --min-instances=0 \
    --max-instances=10 \
    --memory=512Mi \
    --cpu=1 \
    --timeout=60s \
    --project="${PROJECT_ID}"

echo ""
echo "============================================================"
echo " Deployment Complete!"
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --platform=managed --region="${REGION}" --format='value(status.url)' --project="${PROJECT_ID}")
echo " Live Service URL: ${SERVICE_URL}"
echo " Health Probe:    ${SERVICE_URL}/health"
echo "============================================================"
