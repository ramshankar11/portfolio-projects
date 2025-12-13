import json
import boto3
import os
import datetime

# LocalStack endpoint integration in Lambda environment can be tricky
# Usually http://localstack:4566 if running in same network, or standard if mocked
# We will use the endpoint only if we can find it, else default AWS
endpoint_url = os.environ.get('AWS_ENDPOINT_URL') # LocalStack sets this automatically in newer versions?

if not endpoint_url and os.environ.get('LOCALSTACK_HOSTNAME'):
     endpoint_url = f"http://{os.environ['LOCALSTACK_HOSTNAME']}:4566"

s3 = boto3.client('s3', endpoint_url=endpoint_url)

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    
    try:
        # Get bucket and key from event
        record = event['Records'][0]
        src_bucket = record['s3']['bucket']['name']
        src_key = record['s3']['object']['key']
        
        # Read object
        response = s3.get_object(Bucket=src_bucket, Key=src_key)
        content = json.loads(response['Body'].read().decode('utf-8'))
        
        # Transform
        content['processed_at'] = datetime.datetime.utcnow().isoformat()
        content['status'] = 'processed'
        
        # Write to target bucket
        tgt_bucket = 'processed-data'
        tgt_key = f"processed_{src_key}"
        
        print(f"Writing to {tgt_bucket}/{tgt_key}")
        s3.put_object(
            Bucket=tgt_bucket,
            Key=tgt_key,
            Body=json.dumps(content)
        )
        
        return {'status': 'success'}
    except Exception as e:
        print(f"Error: {e}")
        raise e
