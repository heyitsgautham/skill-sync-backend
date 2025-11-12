#!/bin/bash
# Deploy Backend to Google Cloud Run

# Configuration
PROJECT_ID="learnweave-477312"
SERVICE_NAME="skillsync-backend"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying SkillSync Backend to Google Cloud Run..."

# Build and push Docker image
echo "📦 Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo "🌐 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --add-cloudsql-instances learnweave-477312:us-central1:skillsync-db \
  --set-env-vars "ENVIRONMENT=production,AWS_REGION=ap-south-1,AWS_S3_BUCKET_NAME=skillsync-resumes-gautham-1762381748,SMTP_HOST=smtp.gmail.com,SMTP_PORT=587,SMTP_USERNAME=gouthamkrishna732006@gmail.com,SENDER_EMAIL=gouthamkrishna732006@gmail.com,SENDER_NAME=SkillSync" \
  --set-secrets "DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=SECRET_KEY:latest,GOOGLE_API_KEY=GOOGLE_API_KEY:latest,AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID:latest,AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY:latest,SMTP_PASSWORD=SMTP_PASSWORD:latest"

echo "✅ Deployment complete!"
echo "🔗 Your backend URL: https://${SERVICE_NAME}-${REGION}.run.app"
