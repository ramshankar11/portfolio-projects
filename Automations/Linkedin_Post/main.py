import functions_framework
import requests
import json
import google.generativeai as genai
from google.cloud import bigquery
import base64
import os

project_id = "PROJECTID"
dataset_id = "DATASETID"
table_id = "TABLEID"

client = bigquery.Client(project=project_id)

def get_topics_from_bq(projectid,datasetid,tableid):

    # Construct a query to select data from the table.
    query = f"""
        SELECT distinct topic
        FROM `{projectid}.{datasetid}.{tableid}`
    """

    # Run the query.
    print("Executing query...")
    query_job = client.query(query)  # API request

    already_use_topics = []
    # Fetch the results.
    try:
        results = query_job.result()  # Waits for job to complete
        
        print("\nQuery results:")
        for row in results:
            # Rows can be accessed by field name or index
            already_use_topics.append(row["topic"])
        return already_use_topics
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def get_post_content_from_llm(API_KEY,topic_list):
    genai.configure(api_key=API_KEY) 
    model = genai.GenerativeModel('gemini-2.5-flash')

    system_instructions = """
    You are a LinkedIn Marketing or Engagement Specialist who is assigned a work on generating posts for a LinkedIn account. Your primary goal is to create posts that achieve high impressions and engagement, and are visually attractive in terms of content look (using emojis, line breaks, and other non-markdown formatting) on key topics in IT. Your outputs must be in JSON format.
    Note: The JSON should be in a format to be readable in python using "json.loads(response)"

    """

    prompt = system_instructions+"""
    You are a LinkedIn content generation assistant. Your task is to craft a highly engaging and visually attractive LinkedIn post based on the provided key skills. Ensure the chosen topic has not been used before from the list of already used topics.

    Please generate the output in JSON format with two fields: "topic" and "post_body".

    Here are the inputs:
    - **Key Skills:** [LIST DOWN YOUR SKILLS SEPERATED BY COMMA]
    - **Already Used Topics:** ```   
    """+topic_list+"""  ```
    - ImageUri to Skill Mapping: 
    ```
    Update the urn to description mapping here for all the skills related images
    Eg:
    'urn:li:digitalmediaAsset:assetid': 'Agentic AI',
    'urn:li:digitalmediaAsset:assetid': 'Artificial Intelligence',
    ```
    ---

    **Instructions for Post Generation:**

    1.  Select ONE key skill from the 'Key Skills' list that has not been the primary focus of any topic in the 'Already Used Topics' list. Prioritize skills that have been used less frequently or not at all ( should use a skill thats not been used in the last couple of topics ).

    2.  Formulate a **CONCISE, COMPELLING, and VISUALLY APPEALING 'topic'** for the LinkedIn post. This topic should act as an eye-catching headline, clearly explaining what the post will discuss, and **MUST incorporate relevant emojis** to capture immediate attention. Ensure this topic is new, distinct, and highly relevant to the chosen skill.

    3.  **IMPORTANT FORMATTING RULE:** Avoid using Markdown formatting like asterisks (**bold**), underscores (_italic_), or backticks (`code`) in both the 'topic' and 'post_body'. Instead, use **CAPITAL LETTERS for EMPHASIS** and unicode text for bold/italic or similar formatting wherever needed, strategic line breaks for readability, and **abundant relevant emojis** for visual appeal, as these are generally better supported by LinkedIn's native formatting.

    4.  Write the 'post_body' for LinkedIn. The post should:
        *   Be engaging, informative, and provide value to the reader.
        *   Clearly highlight a specific aspect, benefit or challenge related to the chosen skill.
        * The content should be unique and should be a little technical so that the people can learn something new.
        *   **INCORPORATE EMOJIS AND VISUAL ELEMENTS NATURALLY** throughout the text to enhance readability and engagement. Break up text with line breaks for easier scanning.
        *   Encourage discussion or interaction (e.g., ask a question, suggest a tip, invite experiences) with a clear call to action. but it should not be completely asking people to comment or iit should not be like want them to connect or something like that.
        *   Include 3-5 **HIGHLY RELEVANT, POPULAR, and IMPRESSION-DRIVEN** hashtags.
        *   Be approximately 150-450 words in length.
        *   The content should be something like the viewers should learn something new both technically and also theoretically.

    5. Utilize the imageuri to skill mapping provided above to include the image_uri in your json response along with the topic and post body. 

    6.  Output the topic and post body and the image_uri strictly in the specified JSON format.

    ---

    **Example of Desired Output Format:**

    ```json
    {
    "topic": "🤖 The Rise of Agentic AI: Beyond Simple Prompts! ✨",
    "post_body": "Are you keeping up with the latest in AI? 🚀 Agentic AI is revolutionizing how we think about automation and intelligence! Forget basic chatbots – we're talking about AI systems that can plan, reason, and take action autonomously to achieve complex goals.\n\nImagine an AI agent breaking down a multi-step task, executing each part, and course-correcting along the way. This isn't just about large language models; it's about combining them with tools, memory, and planning capabilities to create truly intelligent, self-directed systems. It's a HUGE leap! 🤯\n\nWhat applications excite you most for Agentic AI? Share your thoughts and predictions below! 👇\n\n#AgenticAI #ArtificialIntelligence #AITrends #FutureTech #Innovation",
    "image_uri": "urn:li:digitalmediaAsset:D5622AQGgB8Xl_hoofA"
    }
    ```
    """
    try:
        response = model.generate_content(contents=prompt)
        linkedin_post_content = response.text.replace("```json\n","").replace("\n```","").replace("```json","").replace("```","")
        print("Generated Post:")
        return linkedin_post_content
    except Exception as e:
        print(f"Error generating content from Gemini API: {e}")
        return None

def send_linkedin_post(ugc_post_url,headers,post_data):
    # Make the POST request to the UGC API
    try:
        print("EXECUTING API REQUEST....")
        response = requests.post(ugc_post_url, headers=headers, data=json.dumps(post_data))
        print("DONE API REQUEST")
        print(response)
        response.raise_for_status() # Raise an exception for bad status codes

        print("\nLinkedIn post successful! ✅")
        print("Response:")
        print(response.json())
        return True
    except requests.exceptions.HTTPError as err:
        print(f"\nHTTP Error: {err}")
        print(f"Response content: {err.response.text}")
        return False
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        return False

@functions_framework.cloud_event
def linkedin_send(request):

    print(base64.b64decode(request.data["message"]["data"]))
    # Check the request method
    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
    LINKEDIN_ACCESS_TOKEN = os.environ["LINKEDIN_ACCESS_TOKEN"]

    already_use_topics = get_topics_from_bq(project_id,dataset_id,table_id)

    if already_use_topics:
        text_already_used_topics = "\n".join(already_use_topics)
        response_llm = get_post_content_from_llm(GEMINI_API_KEY,text_already_used_topics)
        if response_llm:
            print(response_llm)
            post_content = json.loads(response_llm)
            asset_url = post_content["image_uri"]
            content_to_post = post_content["topic"] + "\n\n\n" + post_content["post_body"]


            user_urn = "urn:li:person:PERSONURN"
            ugc_post_url = "https://api.linkedin.com/v2/ugcPosts"
            headers = {
                "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }


            print("CHECKING IF THE IMAGE URN IS AVAILABLE BEFORE POSTING...")
            verify_post_image_available = {
                "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
            }
            asset_uri_no = asset_url.split(":")[-1]
            response = requests.get(f"https://api.linkedin.com/v2/assets/{asset_uri_no}",headers=verify_post_image_available)
            if response.status_code in (200,201):
                response_json = response.json()
                if response_json["status"] == "ALLOWED":
                    print("IMAGE Accessible")
                else:
                    raise Exception("Image not accessible")
            else:
                print(response.json())
                raise Exception("Image not accessible")
                    
            print("GOOD TO GO......")

            rows_to_insert = [
                {'topic': post_content["topic"], 'asset_uri': asset_url }
            ]
            errors = client.insert_rows_json(project_id+"."+dataset_id+"."+table_id, rows_to_insert)

            if errors:
                print("Encountered errors while inserting rows: {}".format(errors))
            else:
                print("New rows have been added successfully.")
            
            post_data = {
                "author": user_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content_to_post
                        },
                        "shareMediaCategory": "IMAGE",
                        "media": [
                            {
                                "status": "READY",
                                "description": {
                                    "text": "Image for the Post"
                                },
                                "media": asset_url,
                                "title": {
                                    "text": "Image for the Post"
                                }
                            }
                        ]
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            print("SENDING LINKEDIN POST....")
            send_linkedin_post(ugc_post_url,headers,post_data)

    else:
        return "NOT OK",400
