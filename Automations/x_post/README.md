# 🐦 Automated X (Twitter) Post Generator

This project automates the creation and posting of trending, witty tweets to X (formerly Twitter). It uses **Google Gemini AI** (with Google Search capabilities) to identify real-time global trends and generates engaging, human-like content.

---

## ✨ Features

*   ** Trend-Aware AI**: Asks Gemini to "Search Google for the current top 10 trending topics worldwide" to ensure relevance.
*   **Witty & Human-Like**: Prompts the AI to write natural, funny, and creative tweets without robotic "AI" language.
*   **Smart Formatting**: Automatically trims tweets to 280 characters while preserving whole words and hashtags.
*   **Automated Posting**: Uses `tweepy` (Twitter API v2) to publish directly to your account.

---

## 🛠️ Prerequisites

*   **Python 3.8+**
*   **X (Twitter) Developer Account** with "Elevated" access (essential for API v2 write access).
*   **Google Cloud Platform (GCP)** account with Gemini API access.

---

## 📝 Setup Guide

### Phase 1: X (Twitter) Developer Setup

To post tweets via API, you need a Developer App with the right permissions.

1.  **Apply for a Developer Account**:
    *   Go to [developer.twitter.com](https://developer.twitter.com/).
    *   Apply for a developer account (the "Free" tier allows posting, but "Basic" is recommended for more features).

2.  **Create a Project & App**:
    *   In the Developer Portal, create a specific Project.
    *   Create an App within that project.

3.  **Set User Authentication Settings**:
    *   Go to your App settings -> **User authentication settings**.
    *   Enable **OAuth 1.0a** and **OAuth 2.0**.
    *   Select **Read and Write** permissions.
    *   For "Type of App", select **Native App** (or Web App if you have a callback URL).
    *   (You can use `http://localhost` as the Callback URL / Website URL for script usage).

4.  **Generate Keys and Tokens**:
    *   Go to the **Keys and Tokens** tab.
    *   Generate and save the following:
        *   **API Key** (Consumer Key)
        *   **API Key Secret** (Consumer Secret)
        *   **Bearer Token**
        *   **Access Token** (ensure it has Read and Write permissions!)
        *   **Access Token Secret**

### Phase 2: Google Gemini Setup

1.  **Get API Key**:
    *   Go to [Google AI Studio](https://aistudio.google.com/).
    *   Get an API Key.
    *   Ensure the account supports the `gemini-2.5-flash` model and the `google_search` tool.

---

## 💻 Local Installation & Configuration

1.  **Clone the Repository**
    ```bash
    git clone <your-repo-url>
    cd x_post
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set Environment Variables**
    Set these in your terminal or use a `.env` file for local testing:

    ```bash
    # X (Twitter) Credentials
    export TWITTER_API_KEY="your_api_key"
    export TWITTER_API_KEY_SECRET="your_api_key_secret"
    export TWITTER_BEARER_TOKEN="your_bearer_token"
    export TWITTER_ACCESS_TOKEN="your_access_token_with_write_permission"
    export TWITTER_ACCESS_TOKEN_SECRET="your_access_token_secret"

    # Google Gemini Credential
    export GEMINI_API_KEY="your_gemini_api_key"
    ```

---

## 🚀 Deployment

### Deploy to Google Cloud Functions

This script is designed to run as a Google Cloud Function (`functions_framework`).

```bash
gcloud functions deploy twitter_poster \
--runtime python310 \
--trigger-topic twitter-daily-post \
--set-env-vars TWITTER_API_KEY=...,TWITTER_API_KEY_SECRET=...,TWITTER_ACCESS_TOKEN=...,TWITTER_ACCESS_TOKEN_SECRET=...,TWITTER_BEARER_TOKEN=...,GEMINI_API_KEY=... \
--region us-central1
```

### Schedule Daily Posts

Use **Cloud Scheduler** to trigger the Pub/Sub topic defined above (e.g., `twitter-daily-post`) to automate tweets every day.

```bash
gcloud scheduler jobs create pubsub daily-tweet \
--schedule "0 10 * * *" \
--topic twitter-daily-post \
--message-body "{\"action\": \"trigger_tweet\"}" \
--location us-central1
```

---

## 🔍 Code Explanation

*   **`generate_tweet_with_gemini()`**: Sends a prompt to Gemini 1.5 Flash asking it to "Search Google" for trends and write a tweet. It uses the specific `tools: [{"google_search": {}}]` configuration.
*   **`trim_with_hashtags()`**: A helper function ensuring the tweet stays under 280 characters. It intelligently cuts off text but removes any partial hashtags at the end to keep it clean.
*   **`post_tweet()`**: Authenticates with `tweepy.Client` and posts the text.
