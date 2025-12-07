import boto3
import sys

# Get your AWS region from .env
try:
    from fastuner.config import get_settings
    settings = get_settings()
    region = settings.aws_region
except:
    region = 'us-west-2'  # Fallback

logs = boto3.client('logs', region_name=region)
job_name = 'ft-default--job-ac8a-20251207-044232'

print(f"Checking logs for: {job_name}")
print(f"Region: {region}\n")

try:
    # Get log streams
    streams = logs.describe_log_streams(
        logGroupName='/aws/sagemaker/TrainingJobs',
        logStreamNamePrefix=job_name,
        descending=True,
        limit=5
    )

    if streams['logStreams']:
        stream_name = streams['logStreams'][0]['logStreamName']
        print(f"Reading from: {stream_name}\n")
        print("="*80)

        # Get logs
        events = logs.get_log_events(
            logGroupName='/aws/sagemaker/TrainingJobs',
            logStreamName=stream_name,
            limit=100,
            startFromHead=False
        )

        for event in events['events']:
            print(event['message'])
    else:
        print("No logs found yet - job may still be starting")
        print("Wait a few minutes and try again")

except Exception as e:
    print(f"Error fetching logs: {e}")
    print("\nMake sure:")
    print("1. AWS credentials are configured")
    print("2. Job name is correct")
    print("3. Region is correct")
    sys.exit(1)
