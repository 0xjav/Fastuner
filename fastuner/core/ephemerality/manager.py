"""
Ephemerality Manager for TTL-based resource cleanup.

This module handles:
- Finding stale deployments based on TTL
- Automatic endpoint teardown
- Cost tracking and reporting
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from fastuner.models.deployment import Deployment, DeploymentStatus
from fastuner.core.inference import InferenceOrchestrator
from fastuner.database import SessionLocal

logger = logging.getLogger(__name__)


class EphemeralityManager:
    """Manages TTL-based cleanup of ephemeral resources"""

    def __init__(self):
        self.inference_orchestrator = InferenceOrchestrator()

    def find_stale_deployments(self, db: Session) -> List[Deployment]:
        """
        Find deployments that have exceeded their TTL.

        A deployment is stale if:
        - Status is ACTIVE
        - (last_used_at + ttl_seconds) < now

        Args:
            db: Database session

        Returns:
            List of stale deployments
        """
        now = datetime.utcnow()
        stale_deployments = []

        # Query all active deployments
        active_deployments = (
            db.query(Deployment)
            .filter(Deployment.status == DeploymentStatus.ACTIVE)
            .all()
        )

        for deployment in active_deployments:
            if deployment.last_used_at and deployment.ttl_seconds:
                expiry_time = deployment.last_used_at + timedelta(seconds=deployment.ttl_seconds)
                if now > expiry_time:
                    stale_deployments.append(deployment)
                    logger.info(
                        f"Found stale deployment {deployment.id}: "
                        f"last_used_at={deployment.last_used_at}, "
                        f"ttl={deployment.ttl_seconds}s, "
                        f"expired_at={expiry_time}"
                    )

        return stale_deployments

    def cleanup_stale_deployment(self, deployment: Deployment, db: Session) -> Dict[str, Any]:
        """
        Clean up a single stale deployment.

        Args:
            deployment: Deployment to clean up
            db: Database session

        Returns:
            Cleanup result with status and details
        """
        result = {
            "deployment_id": deployment.id,
            "endpoint_name": deployment.endpoint_name,
            "tenant_id": deployment.tenant_id,
            "success": False,
            "error": None,
        }

        try:
            # Delete SageMaker endpoint
            logger.info(f"Deleting stale endpoint: {deployment.endpoint_name}")
            self.inference_orchestrator.delete_endpoint(
                endpoint_name=deployment.endpoint_name,
                delete_config=True,
                delete_model=True,
            )

            # Update deployment status
            deployment.status = DeploymentStatus.DELETED
            deployment.deleted_at = datetime.utcnow()
            db.commit()

            result["success"] = True
            logger.info(f"Successfully cleaned up deployment {deployment.id}")

        except Exception as e:
            logger.error(f"Failed to clean up deployment {deployment.id}: {e}", exc_info=True)
            result["error"] = str(e)

            # Mark as failed but don't raise
            deployment.status = DeploymentStatus.FAILED
            db.commit()

        return result

    def run_cleanup_cycle(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Run a complete cleanup cycle.

        Args:
            dry_run: If True, only report stale deployments without deleting

        Returns:
            Summary of cleanup cycle
        """
        db = SessionLocal()
        try:
            # Find stale deployments
            stale_deployments = self.find_stale_deployments(db)

            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "dry_run": dry_run,
                "stale_count": len(stale_deployments),
                "cleaned_count": 0,
                "failed_count": 0,
                "results": [],
            }

            if not stale_deployments:
                logger.info("No stale deployments found")
                return summary

            logger.info(f"Found {len(stale_deployments)} stale deployment(s)")

            if dry_run:
                summary["results"] = [
                    {
                        "deployment_id": d.id,
                        "endpoint_name": d.endpoint_name,
                        "tenant_id": d.tenant_id,
                        "last_used_at": d.last_used_at.isoformat() if d.last_used_at else None,
                        "ttl_seconds": d.ttl_seconds,
                    }
                    for d in stale_deployments
                ]
                return summary

            # Clean up each stale deployment
            for deployment in stale_deployments:
                result = self.cleanup_stale_deployment(deployment, db)
                summary["results"].append(result)

                if result["success"]:
                    summary["cleaned_count"] += 1
                else:
                    summary["failed_count"] += 1

            logger.info(
                f"Cleanup cycle complete: "
                f"{summary['cleaned_count']} cleaned, "
                f"{summary['failed_count']} failed"
            )

            return summary

        finally:
            db.close()

    def get_cost_report(self, db: Session, tenant_id: str = None) -> Dict[str, Any]:
        """
        Generate a cost report for active deployments.

        Args:
            db: Database session
            tenant_id: Optional tenant ID to filter by

        Returns:
            Cost report with estimated hourly costs
        """
        # Instance type hourly costs (approximate)
        INSTANCE_COSTS = {
            "ml.t2.medium": 0.065,
            "ml.t2.large": 0.130,
            "ml.m5.xlarge": 0.269,
            "ml.m5.2xlarge": 0.538,
            "ml.g4dn.xlarge": 0.736,
            "ml.g4dn.2xlarge": 1.044,
            "ml.g5.xlarge": 1.408,
            "ml.g5.2xlarge": 1.515,
            "ml.g5.4xlarge": 2.449,
            "ml.p3.2xlarge": 3.825,
            "ml.p4d.24xlarge": 37.688,
        }

        query = db.query(Deployment).filter(Deployment.status == DeploymentStatus.ACTIVE)
        if tenant_id:
            query = query.filter(Deployment.tenant_id == tenant_id)

        active_deployments = query.all()

        total_hourly_cost = 0.0
        deployments_info = []

        for deployment in active_deployments:
            cost_per_hour = INSTANCE_COSTS.get(deployment.instance_type, 0.0) * deployment.instance_count
            total_hourly_cost += cost_per_hour

            # Calculate time since last use
            time_since_use = None
            if deployment.last_used_at:
                time_since_use = (datetime.utcnow() - deployment.last_used_at).total_seconds()

            deployments_info.append({
                "deployment_id": deployment.id,
                "endpoint_name": deployment.endpoint_name,
                "instance_type": deployment.instance_type,
                "instance_count": deployment.instance_count,
                "hourly_cost": cost_per_hour,
                "last_used_at": deployment.last_used_at.isoformat() if deployment.last_used_at else None,
                "time_since_use_seconds": time_since_use,
                "ttl_seconds": deployment.ttl_seconds,
            })

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "tenant_id": tenant_id,
            "active_count": len(active_deployments),
            "total_hourly_cost": round(total_hourly_cost, 3),
            "estimated_monthly_cost": round(total_hourly_cost * 730, 2),  # 730 hours/month average
            "deployments": deployments_info,
        }


def get_ephemerality_manager() -> EphemeralityManager:
    """Get EphemeralityManager instance"""
    return EphemeralityManager()
