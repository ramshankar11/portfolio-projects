import functions_framework
import tweepy
import requests
import json
import os
import base64

def generate_tweet_with_gemini(GEMINI_API_KEY):
    """
    Calls the Gemini API to generate a tweet based on the trending topics.
    """
    prompt = f"Search Google for the current top 10 trending topics worldwide and use them as inspiration. Write a witty, engaging tweet of up to 280 characters (never exceed this limit). The tweet must feel natural and human, without any mention of AI, trends, or how it was created. It should be funny, creative, and relatable. Include catchy hashtags that can boost engagement. Output only the tweet text."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {
            "temperature": 1.0,
            "maxOutputTokens": 20000
        }
    }

    headers = {"Content-Type": "application/json"}
    try:
        print(f"Requested Gemini to generate content....")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Raise an exception for bad status codes
                
        result = response.json()
        candidate = result.get("candidates", [{}])[0]
        generated_text = candidate.get("content", {}).get("parts", [{}])[0].get("text")
                
        if generated_text:
            print("Successfully generated tweet content.")
            return generated_text
        else:
            print("Gemini API response did not contain text.")
            return None
    except Exception as e:
        print(f"Exception occured when generating content: {e}")
        return None
        
def trim_with_hashtags(text, limit=280):
    if len(text) <= limit:
        return text
    
    trimmed = text[:limit]  
    words = trimmed.split()
    
    # remove partial hashtags (those that were cut off)
    while words and words[-1].startswith("#") and words[-1] not in text.split():
        words.pop()
    
    return " ".join(words)

def post_tweet(tweet_text,BEARER_TOKEN,API_KEY,API_SECRET_KEY,ACCESS_TOKEN,ACCESS_TOKEN_SECRET):
    """
    Posts the provided tweet text to the X (Twitter) account using the API v2 endpoint.
    This works with most developer access levels.
    """
    try:
        print("Authenticating with X API for posting using v2 client...")
        # Use the tweepy.Client for API v2 endpoints
        client = tweepy.Client(
            bearer_token=BEARER_TOKEN,
            consumer_key=API_KEY,
            consumer_secret=API_SECRET_KEY,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_TOKEN_SECRET
        )

        # Check if the tweet text is too long (X's limit is 280 characters)
        tweet_text = trim_with_hashtags(tweet_text)

        print(f"Posting tweet: '{tweet_text}'")

        try:
            response = client.create_tweet(text=tweet_text)
            
            print("Successful response I guess....")
            
            # Check for a successful response with a tweet ID
            if response.data and 'id' in response.data:
                print("Tweet posted successfully! Tweet ID: " + response.data['id'])
                return True
            else:
                print("Failed to post tweet. Response did not contain a tweet ID.")
                return False
        except Exception as e:
            print(f"Unable to send tweet.. {e}")
            return True

    except tweepy.TweepyException as e:
        print(f"Error posting tweet: {e}")
        return False
    

@functions_framework.cloud_event
def twitter_send(request):

    print(base64.b64decode(request.data["message"]["data"]))
    # Check the request method
    API_KEY = os.environ["TWITTER_API_KEY"]
    API_SECRET_KEY = os.environ["TWITTER_API_KEY_SECRET"]
    ACCESS_TOKEN = os.environ["TWITTER_ACCESS_TOKEN"]
    ACCESS_TOKEN_SECRET = os.environ["TWITTER_ACCESS_TOKEN_SECRET"]
    BEARER_TOKEN = os.environ["TWITTER_BEARER_TOKEN"]
    
    # Gemini API Key
    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
    new_tweet_text = generate_tweet_with_gemini(GEMINI_API_KEY)
    print(f"Generated Tweet Text: {new_tweet_text}")
    if new_tweet_text:
        response = post_tweet(new_tweet_text,BEARER_TOKEN,API_KEY,API_SECRET_KEY,ACCESS_TOKEN,ACCESS_TOKEN_SECRET)
        if response:
            return "OK", 200
        else:
            return "NOT OK",400