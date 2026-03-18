#!/bin/bash

# G-NOV SENTINEL: Automated Deployment Script
# Target: Google Cloud Run (Serverless)
LINK=https://docs.google.com/document/d/1-kCA2kBpOsP2Cj8pQrtKMNYdeRITKwU3IQsblUIEJ7g/edit?tab=t.0
PROJECT_ID=""
REGION="us-central1"
SERVICE_NAME="gnov-sentinel-api"

echo "🚀 Step 1: Building Docker Container..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME .

echo "🌐 Step 2: Deploying to Google Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars=MODEL_ID=gemini-3-flash

echo "✅ Deployment Complete! Sentinel is Live."