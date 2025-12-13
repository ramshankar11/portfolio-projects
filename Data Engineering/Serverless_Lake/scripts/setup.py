import boto3
import time
import zipfile
import os

# Config
ENDPOINT = "http://localhost:4566"
REGION = "us-east-1"
LAMBDA_ZIP = "function.zip"

def get_client(service):
    return boto3.client(service, endpoint_url=ENDPOINT, region_name=REGION)

def create_zip():
    print("Zipping lambda...")
    with zipfile.ZipFile(LAMBDA_ZIP, 'w') as z:
        z.write('../lambda/function.py', 'function.py')

def setup_infrastructure():
    s3 = get_client('s3')
    lam = get_client('lambda')

    # 1. Create Buckets
    print("Creating buckets...")
    s3.create_bucket(Bucket='raw-data')
    s3.create_bucket(Bucket='processed-data')

    # 2. Create Lambda
    print("Creating Lambda function...")
    with open(LAMBDA_ZIP, 'rb') as f:
        zipped_code = f.read()

    lam.create_function(
        FunctionName='ProcessData',
        Runtime='python3.9',
        Role='arn:aws:iam::000000000000:role/lambda-role',
        Handler='function.lambda_handler',
        Code={'ZipFile': zipped_code},
        Timeout=30
    )

    # 3. Configure S3 Notification
    print("Configuring S3 notification...")
    # Grant permission (LocalStack sometimes needs this explicitly or mocks it)
    # Configure bucket notification
    lambda_arn = lam.get_function(FunctionName='ProcessData')['Configuration']['FunctionArn']
    
    s3.put_bucket_notification_configuration(
        Bucket='raw-data',
        NotificationConfiguration={
            'LambdaFunctionConfigurations': [
                {
                    'LambdaFunctionArn': lambda_arn,
                    'Events': ['s3:ObjectCreated:*']
                }
            ]
        }
    )
    print("Setup complete.")

if __name__ == "__main__":
    create_zip()
    setup_infrastructure()
    # cleanup
    os.remove(LAMBDA_ZIP)
