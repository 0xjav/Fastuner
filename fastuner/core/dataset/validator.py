"""
Dataset validation module for V0.

Implements strict JSONL validation according to the design spec:
- Schema validation (input_text, target_text)
- UTF-8 encoding check
- Length constraints (1-8192 input, 1-2048 target)
- Deduplication via SHA-256
- Minimum 100 unique samples
"""

import json
import hashlib
import logging
from typing import List, Dict, Any, Set
from io import StringIO

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for dataset validation errors"""

    pass


class DatasetValidator:
    """Validates datasets according to V0 schema requirements"""

    # Schema constraints
    SCHEMA_VERSION = "v0_text"
    MIN_INPUT_LENGTH = 1
    MAX_INPUT_LENGTH = 8192
    MIN_TARGET_LENGTH = 1
    MAX_TARGET_LENGTH = 2048
    MIN_UNIQUE_SAMPLES = 100

    @classmethod
    def validate_jsonl(cls, file_content: str) -> List[Dict[str, str]]:
        """
        Validate and parse JSONL file content.

        Args:
            file_content: Raw JSONL file content as string

        Returns:
            List of validated and deduplicated records

        Raises:
            ValidationError: If validation fails
        """
        records = []
        seen_hashes: Set[str] = set()
        line_number = 0

        try:
            for line in StringIO(file_content):
                line_number += 1
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Parse JSON
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    raise ValidationError(
                        f"Line {line_number}: Invalid JSON - {str(e)}"
                    )

                # Validate schema
                cls._validate_record_schema(record, line_number)

                # Validate field constraints
                cls._validate_field_constraints(record, line_number)

                # Deduplicate
                record_hash = cls._compute_hash(record)
                if record_hash in seen_hashes:
                    logger.debug(f"Line {line_number}: Duplicate record, skipping")
                    continue

                seen_hashes.add(record_hash)
                records.append(record)

        except UnicodeDecodeError as e:
            raise ValidationError(f"Line {line_number}: Non-UTF-8 encoding - {str(e)}")

        # Validate minimum samples
        if len(records) < cls.MIN_UNIQUE_SAMPLES:
            raise ValidationError(
                f"Need ≥{cls.MIN_UNIQUE_SAMPLES} unique samples, got {len(records)}"
            )

        logger.info(f"Validation successful: {len(records)} unique samples")
        return records

    @classmethod
    def _validate_record_schema(cls, record: Any, line_number: int) -> None:
        """Validate that record has required fields"""
        if not isinstance(record, dict):
            raise ValidationError(
                f"Line {line_number}: Record must be a JSON object, got {type(record).__name__}"
            )

        required_fields = {"input_text", "target_text"}
        missing_fields = required_fields - set(record.keys())

        if missing_fields:
            raise ValidationError(
                f"Line {line_number}: Missing required fields: {missing_fields}"
            )

    @classmethod
    def _validate_field_constraints(cls, record: Dict[str, Any], line_number: int) -> None:
        """Validate field types and length constraints"""
        # Validate input_text
        input_text = record["input_text"]
        if not isinstance(input_text, str):
            raise ValidationError(
                f"Line {line_number}: 'input_text' must be a string, got {type(input_text).__name__}"
            )

        # Check UTF-8 encoding
        try:
            input_text.encode("utf-8")
        except UnicodeEncodeError:
            raise ValidationError(
                f"Line {line_number}: 'input_text' contains non-UTF-8 characters"
            )

        # Check length
        if not (cls.MIN_INPUT_LENGTH <= len(input_text) <= cls.MAX_INPUT_LENGTH):
            raise ValidationError(
                f"Line {line_number}: 'input_text' length must be between "
                f"{cls.MIN_INPUT_LENGTH} and {cls.MAX_INPUT_LENGTH} chars, got {len(input_text)}"
            )

        # Validate target_text
        target_text = record["target_text"]
        if not isinstance(target_text, str):
            raise ValidationError(
                f"Line {line_number}: 'target_text' must be a string, got {type(target_text).__name__}"
            )

        try:
            target_text.encode("utf-8")
        except UnicodeEncodeError:
            raise ValidationError(
                f"Line {line_number}: 'target_text' contains non-UTF-8 characters"
            )

        if not (cls.MIN_TARGET_LENGTH <= len(target_text) <= cls.MAX_TARGET_LENGTH):
            raise ValidationError(
                f"Line {line_number}: 'target_text' length must be between "
                f"{cls.MIN_TARGET_LENGTH} and {cls.MAX_TARGET_LENGTH} chars, got {len(target_text)}"
            )

    @staticmethod
    def _compute_hash(record: Dict[str, str]) -> str:
        """Compute SHA-256 hash of record for deduplication"""
        content = record["input_text"] + record["target_text"]
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
