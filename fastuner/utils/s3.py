"""S3 utility functions for dataset and model storage"""

import boto3
import logging
from typing import List, Dict, Any
from botocore.exceptions import ClientError
import json

from fastuner.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class S3Client:
    """Wrapper for S3 operations"""

    def __init__(self):
        self.s3 = boto3.client("s3", region_name=settings.aws_region)

    def upload_jsonl(
        self,
        bucket: str,
        key: str,
        records: List[Dict[str, Any]],
    ) -> str:
        """
        Upload JSONL records to S3.

        Args:
            bucket: S3 bucket name
            key: S3 object key
            records: List of dict records to write as JSONL

        Returns:
            S3 URI (s3://bucket/key)
        """
        try:
            # Convert records to JSONL
            jsonl_content = "\n".join(json.dumps(record) for record in records)

            # Upload to S3
            self.s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=jsonl_content.encode("utf-8"),
                ContentType="application/x-ndjson",
            )

            s3_uri = f"s3://{bucket}/{key}"
            logger.info(f"Uploaded {len(records)} records to {s3_uri}")
            return s3_uri

        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise

    def download_jsonl(self, bucket: str, key: str) -> List[Dict[str, Any]]:
        """
        Download JSONL file from S3.

        Args:
            bucket: S3 bucket name
            key: S3 object key

        Returns:
            List of dict records
        """
        try:
            response = self.s3.get_object(Bucket=bucket, Key=key)
            content = response["Body"].read().decode("utf-8")

            # Parse JSONL
            records = []
            for line in content.strip().split("\n"):
                if line:
                    records.append(json.loads(line))

            logger.info(f"Downloaded {len(records)} records from s3://{bucket}/{key}")
            return records

        except ClientError as e:
            logger.error(f"S3 download failed: {e}")
            raise

    def delete_object(self, bucket: str, key: str) -> None:
        """Delete an object from S3"""
        try:
            self.s3.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Deleted s3://{bucket}/{key}")
        except ClientError as e:
            logger.error(f"S3 delete failed: {e}")
            raise

    def delete_prefix(self, bucket: str, prefix: str) -> None:
        """Delete all objects with a given prefix"""
        try:
            # List objects
            paginator = self.s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

            delete_keys = []
            for page in pages:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        delete_keys.append({"Key": obj["Key"]})

            # Delete in batches of 1000 (S3 limit)
            if delete_keys:
                for i in range(0, len(delete_keys), 1000):
                    batch = delete_keys[i : i + 1000]
                    self.s3.delete_objects(
                        Bucket=bucket, Delete={"Objects": batch}
                    )

                logger.info(f"Deleted {len(delete_keys)} objects with prefix s3://{bucket}/{prefix}")

        except ClientError as e:
            logger.error(f"S3 delete prefix failed: {e}")
            raise

    def object_exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists in S3"""
        try:
            self.s3.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False


def get_s3_client() -> S3Client:
    """Get S3 client instance"""
    return S3Client()
