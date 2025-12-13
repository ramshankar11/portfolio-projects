# Serverless Data Lake (LocalStack)

This project simulates a Serverless Data Lake on AWS using LocalStack. It demonstrates an Event-Driven Architecture where file uploads automatically trigger processing.

## Architecture
1. **S3 Bucket (raw-data)**: Landing zone for JSON files.
2. **Lambda Function**: Triggered by `ObjectCreated` events.
3. **Processing logic**: Reads JSON, enriches it with metadata/timestamps.
4. **S3 Bucket (processed-data)**: Storage for results.

## Prerequisites
- Docker & Docker Compose
- Python 3+

## How to Run
1. **Start LocalStack**:
   ```bash
   cd Serverless_Lake
   docker-compose up -d
   ```

2. **Setup Infrastructure**:
   (Requires `boto3` installed: `pip install boto3`)
   ```bash
   cd scripts
   python setup.py
   ```
   This script creates the buckets, packages the Lambda, deploys it, and configures the S3 trigger.

3. **Test the Pipeline**:
   ```bash
   python test_pipeline.py
   ```
   You should see the processed JSON output with a `processed_at` timestamp.

## Technologies
- **LocalStack**: AWS Cloud Simulation
- **AWS Lambda**: Serverless Compute
- **AWS S3**: Object Storage
- **Boto3**: AWS SDK for Python
