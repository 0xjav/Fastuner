"""ID generation utilities"""

import uuid


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID with optional prefix.

    Args:
        prefix: Prefix for the ID (e.g., "ds_", "job_", "adp_")

    Returns:
        UUID string with prefix
    """
    uid = str(uuid.uuid4())
    return f"{prefix}{uid}" if prefix else uid


def generate_dataset_id() -> str:
    """Generate dataset ID"""
    return generate_id("ds_")


def generate_job_id() -> str:
    """Generate fine-tune job ID"""
    return generate_id("job_")


def generate_adapter_id() -> str:
    """Generate adapter ID"""
    return generate_id("adp_")


def generate_deployment_id() -> str:
    """Generate deployment ID"""
    return generate_id("dep_")


def generate_tenant_id() -> str:
    """Generate tenant ID"""
    return generate_id("tenant_")
