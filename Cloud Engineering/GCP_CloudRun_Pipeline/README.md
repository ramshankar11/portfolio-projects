# GCP Cloud Run Event Pipeline

This project deploys a serverless container on **Cloud Run** designed to process events (like Pub/Sub messages).

## Components
- **main.tf**: Terraform to enable APIs and deploy the Cloud Run service.
- **app.py**: A Flask app that accepts HTTP POST requests (standard contract for Cloud Run triggers).
- **Dockerfile**: Containerizes the application.

## How to Deploy
1. **Build & Push Image**:
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/event-processor
   ```

2. **Deploy Infra**:
   ```bash
   terraform init
   terraform apply -var="project_id=YOUR_PROJECT_ID"
   ```

3. **Test**:
   Send a POST request to the Output URL:
   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"message": {"data": "SGVsbG8gQ2xvdWQh"}}' <SERVICE_URL>
   ```
   *Note: data is base64 encoded "Hello Cloud!"*

## Key Concepts
- **Serverless Containers**: Running Docker containers without managing nodes.
- **Event Driven**: Architecture designed to react to push events.
