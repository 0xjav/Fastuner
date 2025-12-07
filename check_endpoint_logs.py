import boto3
from fastuner.config import get_settings

settings = get_settings()
logs = boto3.client('logs', region_name=settings.aws_region)

endpoint_name = "ft-default-sentiment-adapt-dep-9c9b"

try:
    # Get log streams for this endpoint
    streams = logs.describe_log_streams(
        logGroupName='/aws/sagemaker/Endpoints/' + endpoint_name,
        descending=True,
        limit=5
    )

    if streams['logStreams']:
        print(f"Found {len(streams['logStreams'])} log streams\n")

        # Get logs from the most recent stream
        stream_name = streams['logStreams'][0]['logStreamName']
        print(f"Reading from: {stream_name}\n")
        print("="*80)

        # Get the last 100 log events
        events = logs.get_log_events(
            logGroupName='/aws/sagemaker/Endpoints/' + endpoint_name,
            logStreamName=stream_name,
            limit=100,
            startFromHead=False
        )

        for event in events['events']:
            print(event['message'])
    else:
        print("No log streams found yet")

except Exception as e:
    print(f"Error fetching logs: {e}")
    print("\nTrying AllTraffic variant logs...")

    # Try AllTraffic variant logs
    try:
        streams = logs.describe_log_streams(
            logGroupName='/aws/sagemaker/Endpoints/' + endpoint_name,
            logStreamNamePrefix='AllTraffic',
            descending=True,
            limit=5
        )

        if streams['logStreams']:
            stream_name = streams['logStreams'][0]['logStreamName']
            print(f"Reading from: {stream_name}\n")
            print("="*80)

            events = logs.get_log_events(
                logGroupName='/aws/sagemaker/Endpoints/' + endpoint_name,
                logStreamName=stream_name,
                limit=100,
                startFromHead=False
            )

            for event in events['events']:
                print(event['message'])
    except Exception as e2:
        print(f"Error: {e2}")
