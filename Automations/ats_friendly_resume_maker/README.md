### Deployment to Google Cloud Run

Follow these steps to deploy the `ats-streamlit` application to Google Cloud Run:

1.  **Prerequisites:**
    *   Ensure you have a Google Cloud project set up.
    *   Install and configure the `gcloud` CLI.
    *   Enable the Cloud Run API, Container Registry API, and Secret Manager API in your Google Cloud project.
    *   Create a secret named `GEMINI_API_KEY` in Google Secret Manager, containing your Gemini API key.
    * update the photo.jpg with your photo to be displayed in the resume.
    * update the resume_content with your resume content.

2.  **Build and Push Docker Image:**
    Replace `your-gcp-project-id` with your actual Google Cloud Project ID.
    ```bash
    docker build -t ats-streamlit .
    docker tag ats-streamlit gcr.io/your-gcp-project-id/ats-streamlit
    docker push gcr.io/your-gcp-project-id/ats-streamlit
    ```

3.  **Deploy to Cloud Run:**
    You can deploy using the `gcloud` CLI or through the Google Cloud Console UI.

    *   **Using `gcloud` CLI (Recommended):**
        Replace `your-gcp-project-id` with your actual Google Cloud Project ID.
        Replace `your-service-account@your-gcp-project-id.iam.gserviceaccount.com` with the email of a service account that has permissions to invoke Cloud Run services and access Secret Manager secrets.
        ```bash
        gcloud run deploy ats-streamlit \
          --image gcr.io/your-gcp-project-id/ats-streamlit \
          --region us-central1 \
          --port 8080 \
          --concurrency 2 \
          --cpu 1 \
          --memory 512Mi \
          --max-instances 1 \
          --service-account your-service-account@your-gcp-project-id.iam.gserviceaccount.com \
          --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest \
          --allow-unauthenticated \
          --project your-gcp-project-id
        ```

    *   **Using Google Cloud Console UI:**
        1.  Navigate to the Cloud Run section in the Google Cloud Console.
        2.  Click "Create Service" (for first-time deployment) or select your existing service and click "Deploy new revision".
        3.  Select the container image: `gcr.io/your-gcp-project-id/ats-streamlit`.
        4.  Configure the service settings:
            *   **Region:** `us-central1` (or your preferred region)
            *   **Port:** `8080`
            *   **Concurrency:** `2`
            *   **CPU:** `1`
            *   **Memory:** `512Mi`
            *   **Max instances:** `1`
            *   **Authentication:** Allow unauthenticated invocations.
            *   **Service account:** Select the appropriate service account with necessary permissions.
            *   **Secrets:** Add a secret reference for `GEMINI_API_KEY`, mapping it to the `GEMINI_API_KEY` secret in Secret Manager.
        5.  Click "Deploy".