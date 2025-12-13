import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    try:
        user_id = event['pathParameters']['id']
        
        # Fetch from DB (Mocking logic for portfolio if DB doesn't exist yet)
        response = table.get_item(Key={'id': user_id})
        
        if 'Item' not in response:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "User not found"})
            }

        return {
            "statusCode": 200,
            "body": json.dumps(response['Item'])
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
