import boto3
from fastuner.config import get_settings
from datetime import datetime, timezone

settings = get_settings()
sagemaker = boto3.client('sagemaker', region_name=settings.aws_region)

import sys

# Get endpoint name from command line or use default
endpoint_name = sys.argv[1] if len(sys.argv) > 1 else "ft-default-sentiment-adapt-dep-98cc"

try:
    response = sagemaker.describe_endpoint(EndpointName=endpoint_name)
    print(f"Endpoint: {endpoint_name}")
    print(f"Status: {response['EndpointStatus']}")
    print(f"Creation Time: {response['CreationTime']}")

    # Calculate time elapsed
    creation_time = response['CreationTime']
    if creation_time.tzinfo is None:
        creation_time = creation_time.replace(tzinfo=timezone.utc)
    elapsed = datetime.now(timezone.utc) - creation_time
    print(f"Time Elapsed: {elapsed.total_seconds() / 60:.1f} minutes")

    if response.get('FailureReason'):
        print(f"\nFailure Reason: {response['FailureReason']}")

    # Get endpoint config details
    config_name = response.get('EndpointConfigName')
    if config_name:
        print(f"\nEndpoint Config: {config_name}")
        config = sagemaker.describe_endpoint_config(EndpointConfigName=config_name)
        model_name = config['ProductionVariants'][0]['ModelName']
        print(f"Model Name: {model_name}")

        # Get model details to see if there are any issues
        try:
            model = sagemaker.describe_model(ModelName=model_name)
            print(f"\nModel Image: {model['PrimaryContainer']['Image']}")
            print(f"Model Environment:")
            for k, v in model['PrimaryContainer']['Environment'].items():
                print(f"  {k}: {v}")
        except Exception as me:
            print(f"Could not get model details: {me}")

    if response['EndpointStatus'] == 'Creating':
        print("\n⏳ Endpoint is still being created. ML instances can take 15-25 minutes.")

except Exception as e:
    print(f"Error: {e}")
