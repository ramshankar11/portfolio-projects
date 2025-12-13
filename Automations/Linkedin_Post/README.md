### Phase 1: LinkedIn Setup

#### 1. Create a LinkedIn Company Page (Optional)
If you want to post to a company page instead of a personal profile:
1.  Go to your LinkedIn Home feed.
2.  Click **"For Business"** in the top right.
3.  Select **"Create a Company Page"**.
4.  Choose the Page type (Company, Showcase page, etc.).
5.  Fill in the details (Name, URL, Industry, etc.) and click **Create**.

#### 2. Create a LinkedIn Developer App
1.  Go to the [LinkedIn Developer Portal](https://www.linkedin.com/developers/apps).
2.  Click **"Create App"**.
3.  Fill in the App Name, LinkedIn Page (link the one you created or your profile), and upload a logo.
4.  Under **"Products"**, request access to:
    *   **Share on LinkedIn** (for `w_member_social` - Personal Profile)
    *   **Advertising API** (sometimes needed for organization posts)
    *   **Marketing Developer Platform** (for `w_organization_social` - Company Page)

#### 3. Generate OAuth Access Token
You need an access token to authenticate API requests.
1.  Go to the **"Auth"** tab in your App settings.
2.  Note your `Client ID` and `Client Secret`.
3.  Use the **OAuth 2.0 Tools** text link in the Auth tab or use a tool like Postman to generate a token with the following scopes: ( Usually found as Bearer token itself displayed in UI )
    *   `w_member_social` (for Personal Profile)
    *   `w_organization_social` (for Company Page)
    *   `openid`, `profile`, `email` (standard)
4.  Save this token. It will be your `LINKEDIN_ACCESS_TOKEN`.

#### 4. Uploading Images (Crucial Step)
The script relies on existing Image URNs (e.g., `urn:li:digitalmediaAsset:...`). You must upload images to LinkedIn first to get these URNs.

**Step 0: Get Your Person URN**
Before registering an upload, you need your personal URN.
```bash
curl -X GET 'https://api.linkedin.com/v2/me' \
-H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
-H 'Content-Type: application/json'
```
From the JSON response, extract the `id` field. Your `YOUR_PERSON_URN` will be `urn:li:person:YOUR_ID`. For example, if the `id` is `AbC-dEfGhI`, your URN is `urn:li:person:AbC-dEfGhI`.

**Step A: Register the Upload**
```bash
curl -X POST 'https://api.linkedin.com/v2/assets?action=registerUpload' \
-H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
-H 'Content-Type: application/json' \
-d '{
    "registerUploadRequest": {
        "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
        "owner": "YOUR_PERSON_URN", 
        "serviceRelationships": [
            {
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }
        ]
    }
}'
```
*Note: Replace `YOUR_PERSON_URN` with the URN you obtained in Step 0.*

**Step B: Upload the Image**
The response from Step A will give you an `uploadUrl`. Use it to upload your image file.
```bash
curl -i --upload-file /path/to/your/image.jpg --header "Authorization: Bearer YOUR_ACCESS_TOKEN" 'YOUR_UPLOAD_URL_FROM_STEP_A'
```

**Step C: Get the Asset URN**
The `asset` value from the Step A response (e.g., `urn:li:digitalmediaAsset:C552...`) is what you need.
**Update the mappings in `main.py`** (inside the prompt string) with your specific topics and these Image URNs.

---

### Phase 2: Google Cloud Platform (GCP) Setup

1.  **Create a Project**: Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
2.  **Enable APIs**:
    *   BigQuery API
    *   Vertex AI API (or Gemini API)
    *   Cloud Functions API (if deploying)
    *   Cloud Scheduler API (for automated triggers)
    *   Cloud Pub/Sub API (for Cloud Scheduler to Cloud Functions communication)
3.  **BigQuery Setup**:
    *   Go to BigQuery.
    *   Create a Dataset named `linkedin_post_automation`.
    *   Create a Table named `previous_posts` with the schema:
        *   `topic` (STRING)
        *   `asset_uri` (STRING)
    *   Update `project_id` in `main.py` with your GCP Project ID.
4.  **Get Gemini API Key**:
    *   Go to [Google AI Studio](https://aistudio.google.com/).
    *   Create an API Key.

---

### Phase 3: Local Installation

1.  **Clone the Repository**
    ```bash
    git clone <your-repo-url>
    cd Linkedin_Post
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set Environment Variables**
    Set these in your terminal or use a `.env` file (if running locally):
    ```bash
    export GEMINI_API_KEY="your_google_ai_studio_key"
    export LINKEDIN_ACCESS_TOKEN="your_linkedin_oauth_token"
    ```
    *(On Windows PowerShell: `$env:GEMINI_API_KEY="your_key"`, etc.)*

---

## 💻 Code Overview

The `main.py` script orchestrates the entire process:

1.  **`get_topics_from_bq()`**: Queries BigQuery to find topics that have already been used to ensure variety.
2.  **`get_post_content_from_llm()`**:
    *   Constructs a prompt with "Key Skills" and "Already Used Topics".
    *   Calls the Gemini `gemini-2.5-flash` model.
    *   Returns a JSON object containing a catchy `topic`, the `post_body`, and a mapped `image_uri`.
3.  **`linkedin_send(request)`**:
    *   Main entry point (Cloud Function style).
    *   Verifies the selected image is accessible via LinkedIn's Asset API.
    *   Inserts the new topic into BigQuery.
    *   Constructs the LinkedIn UGC Post payload.
    *   **`send_linkedin_post()`**: Sends the final POST request to LinkedIn to publish the content.

---

### Deployment to Google Cloud Functions
    
```bash
gcloud functions deploy linkedin_poster \
--runtime python310 \
--trigger-topic your-pubsub-topic \
--set-env-vars GEMINI_API_KEY=...,LINKEDIN_ACCESS_TOKEN=... \
--region your-gcp-region # e.g., us-central1
```

### Automated Daily Scheduling with Cloud Scheduler

Once your Cloud Function is deployed and listening to a Pub/Sub topic (e.g., `your-pubsub-topic`), you can set up a Cloud Scheduler job to trigger it daily.

1.  **Create a Pub/Sub Topic (if not already created by Cloud Function deployment):**
    ```bash
    gcloud pubsub topics create your-pubsub-topic
    ```

2.  **Create a Cloud Scheduler Job:**
    This command creates a job that publishes a message to `your-pubsub-topic` every day at 9:00 AM UTC.
    ```bash
    gcloud scheduler jobs create pubsub daily-linkedin-post-trigger \
    --schedule "0 9 * * *" \
    --topic your-pubsub-topic \
    --message-body "{\"action\": \"trigger_linkedin_post\"}" \
    --location your-gcp-region # Must be the same region as your Cloud Function
    ```
    *   `--schedule "0 9 * * *"`: This is a cron string. `0 9 * * *` means "at 0 minutes past 9 o'clock every day". Adjust the time as needed (it's in UTC).
    *   `--topic your-pubsub-topic`: The name of the Pub/Sub topic your Cloud Function is subscribed to.
    *   `--message-body`: The payload sent to the Pub/Sub topic. Your Cloud Function can parse this if needed.
    *   `--location`: The GCP region where the scheduler job will run. This should ideally match your Cloud Function's region.

Now, your LinkedIn post generator will run automatically every day at the scheduled time!
