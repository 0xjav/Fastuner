"""
AWS Lambda handler for ephemerality cleanup.

This function is designed to run on a schedule (e.g., every 5 minutes)
via AWS EventBridge to clean up stale deployments.

Environment Variables:
    DATABASE_URL: SQLite/PostgreSQL connection string
    DRY_RUN: Set to "true" to only report without deleting
"""

import json
import logging
import os
from fastuner.core.ephemerality import EphemeralityManager

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Lambda handler for TTL-based cleanup.

    Args:
        event: EventBridge event (scheduled)
        context: Lambda context

    Returns:
        Response with cleanup summary
    """
    try:
        # Get configuration
        dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"

        logger.info(f"Starting cleanup cycle (dry_run={dry_run})")

        # Run cleanup
        manager = EphemeralityManager()
        summary = manager.run_cleanup_cycle(dry_run=dry_run)

        logger.info(f"Cleanup complete: {json.dumps(summary)}")

        return {
            "statusCode": 200,
            "body": json.dumps(summary),
        }

    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
