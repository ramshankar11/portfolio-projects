import boto3
import json
import time

ENDPOINT = "http://localhost:4566"
s3 = boto3.client('s3', endpoint_url=ENDPOINT)

def test_pipeline():
    # Upload file
    data = {"id": 1, "message": "hello world"}
    print(f"Uploading: {data}")
    s3.put_object(Bucket='raw-data', Key='test.json', Body=json.dumps(data))
    
    # Wait for processing
    print("Waiting for Lambda...")
    time.sleep(5)
    
    # Check target
    try:
        obj = s3.get_object(Bucket='processed-data', Key='processed_test.json')
        content = json.loads(obj['Body'].read().decode('utf-8'))
        print("Success! Processed content:")
        print(json.dumps(content, indent=2))
    except Exception as e:
        print(f"Failed to find processed file: {e}")

if __name__ == "__main__":
    test_pipeline()
