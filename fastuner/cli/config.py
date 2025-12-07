"""CLI configuration and utilities"""

import os
from pathlib import Path
from typing import Optional
import json

# CLI config file location
CONFIG_DIR = Path.home() / ".fastuner"
CONFIG_FILE = CONFIG_DIR / "config.json"
TOKEN_FILE = CONFIG_DIR / "token"


def ensure_config_dir():
    """Ensure CLI config directory exists"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def get_api_base_url() -> str:
    """Get API base URL from config or environment"""
    # Check environment variable first
    url = os.getenv("FASTUNER_API_URL")
    if url:
        return url

    # Check config file
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config.get("api_url", "http://localhost:8000")

    # Default
    return "http://localhost:8000"


def set_api_base_url(url: str):
    """Set API base URL in config"""
    ensure_config_dir()

    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

    config["api_url"] = url

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_tenant_id() -> Optional[str]:
    """Get tenant ID from config or environment"""
    # For V0, use environment variable or default
    tenant_id = os.getenv("FASTUNER_TENANT_ID", "default-tenant")
    return tenant_id


def get_token() -> Optional[str]:
    """Get authentication token (for future use)"""
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    return None


def set_token(token: str):
    """Set authentication token"""
    ensure_config_dir()
    TOKEN_FILE.write_text(token)
    TOKEN_FILE.chmod(0o600)  # Secure permissions
