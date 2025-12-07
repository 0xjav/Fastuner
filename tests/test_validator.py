"""Unit tests for DatasetValidator"""

import pytest
from fastuner.core.dataset.validator import DatasetValidator, ValidationError


class TestDatasetValidator:
    """Test suite for dataset validation"""

    def test_valid_dataset(self):
        """Test validation of a valid dataset"""
        jsonl = '\n'.join([
            '{"input_text": "Hello world", "target_text": "Bonjour monde"}',
            '{"input_text": "Good morning", "target_text": "Bonjour"}',
            '{"input_text": "Thank you", "target_text": "Merci"}',
        ])

        records = DatasetValidator.validate_jsonl(jsonl, skip_min_samples=True)
        assert len(records) == 3
        assert records[0]["input_text"] == "Hello world"

    def test_missing_input_text(self):
        """Test validation fails with missing input_text"""
        jsonl = '{"target_text": "Bonjour"}'

        with pytest.raises(ValidationError) as exc_info:
            DatasetValidator.validate_jsonl(jsonl, skip_min_samples=True)

        assert "missing required fields" in str(exc_info.value).lower()
        assert "input_text" in str(exc_info.value).lower()

    def test_missing_target_text(self):
        """Test validation fails with missing target_text"""
        jsonl = '{"input_text": "Hello"}'

        with pytest.raises(ValidationError) as exc_info:
            DatasetValidator.validate_jsonl(jsonl, skip_min_samples=True)

        assert "missing required fields" in str(exc_info.value).lower()
        assert "target_text" in str(exc_info.value).lower()

    def test_empty_input_text(self):
        """Test validation fails with empty input_text"""
        jsonl = '{"input_text": "", "target_text": "Bonjour"}'

        with pytest.raises(ValidationError) as exc_info:
            DatasetValidator.validate_jsonl(jsonl, skip_min_samples=True)

        assert "input_text" in str(exc_info.value).lower()
        assert "length must be between" in str(exc_info.value).lower()

    def test_empty_target_text(self):
        """Test validation fails with empty target_text"""
        jsonl = '{"input_text": "Hello", "target_text": ""}'

        with pytest.raises(ValidationError) as exc_info:
            DatasetValidator.validate_jsonl(jsonl, skip_min_samples=True)

        assert "target_text" in str(exc_info.value).lower()
        assert "length must be between" in str(exc_info.value).lower()

    def test_input_too_long(self):
        """Test validation fails with input_text exceeding max length"""
        long_text = "A" * 9000  # Exceeds MAX_INPUT_LENGTH (8192)
        jsonl = f'{{"input_text": "{long_text}", "target_text": "Short"}}'

        with pytest.raises(ValidationError) as exc_info:
            DatasetValidator.validate_jsonl(jsonl, skip_min_samples=True)

        assert "input_text" in str(exc_info.value).lower()
        assert "length must be between" in str(exc_info.value).lower()
        assert "8192" in str(exc_info.value)

    def test_target_too_long(self):
        """Test validation fails with target_text exceeding max length"""
        long_text = "A" * 3000  # Exceeds MAX_TARGET_LENGTH (2048)
        jsonl = f'{{"input_text": "Short", "target_text": "{long_text}"}}'

        with pytest.raises(ValidationError) as exc_info:
            DatasetValidator.validate_jsonl(jsonl, skip_min_samples=True)

        assert "target_text" in str(exc_info.value).lower()
        assert "length must be between" in str(exc_info.value).lower()
        assert "2048" in str(exc_info.value)

    def test_invalid_json(self):
        """Test validation fails with malformed JSON"""
        jsonl = '{"input_text": "Hello", invalid json}'

        with pytest.raises(ValidationError) as exc_info:
            DatasetValidator.validate_jsonl(jsonl, skip_min_samples=True)

        assert "invalid json" in str(exc_info.value).lower()

    def test_duplicate_detection(self):
        """Test duplicate detection via SHA-256"""
        # Same content should be deduplicated
        jsonl = '\n'.join([
            '{"input_text": "Hello", "target_text": "Bonjour"}',
            '{"input_text": "Hello", "target_text": "Bonjour"}',  # Duplicate
            '{"input_text": "Hi", "target_text": "Salut"}',
        ])

        records = DatasetValidator.validate_jsonl(jsonl, skip_min_samples=True)
        assert len(records) == 2  # Duplicate removed

    def test_minimum_samples_check(self):
        """Test validation fails with insufficient samples"""
        # Create only 50 samples (below MIN_UNIQUE_SAMPLES = 100)
        lines = [
            f'{{"input_text": "Sample {i}", "target_text": "Output {i}"}}'
            for i in range(50)
        ]
        jsonl = '\n'.join(lines)

        with pytest.raises(ValidationError) as exc_info:
            DatasetValidator.validate_jsonl(jsonl)  # Don't skip min samples

        assert "100" in str(exc_info.value)
        assert "50" in str(exc_info.value)

    def test_minimum_samples_pass(self):
        """Test validation passes with sufficient samples"""
        # Create exactly 100 samples
        lines = [
            f'{{"input_text": "Sample {i}", "target_text": "Output {i}"}}'
            for i in range(100)
        ]
        jsonl = '\n'.join(lines)

        records = DatasetValidator.validate_jsonl(jsonl)  # Don't skip min samples
        assert len(records) == 100

    def test_utf8_validation(self):
        """Test UTF-8 encoding validation"""
        # Valid UTF-8 with special characters
        jsonl = '{"input_text": "Hello 世界", "target_text": "Bonjour 🌍"}'

        records = DatasetValidator.validate_jsonl(jsonl, skip_min_samples=True)
        assert len(records) == 1
        assert "世界" in records[0]["input_text"]
        assert "🌍" in records[0]["target_text"]

    def test_non_string_fields(self):
        """Test validation fails with non-string fields"""
        jsonl = '{"input_text": 123, "target_text": "Bonjour"}'

        with pytest.raises(ValidationError) as exc_info:
            DatasetValidator.validate_jsonl(jsonl, skip_min_samples=True)

        assert "must be a string" in str(exc_info.value).lower()

    def test_extra_fields_allowed(self):
        """Test that extra fields are preserved"""
        jsonl = '{"input_text": "Hello", "target_text": "Bonjour", "metadata": {"lang": "fr"}}'

        records = DatasetValidator.validate_jsonl(jsonl, skip_min_samples=True)
        assert len(records) == 1
        assert "metadata" in records[0]
        assert records[0]["metadata"]["lang"] == "fr"

    def test_empty_dataset(self):
        """Test validation fails with empty dataset"""
        jsonl = ""

        with pytest.raises(ValidationError) as exc_info:
            DatasetValidator.validate_jsonl(jsonl)  # Don't skip min samples

        assert "0" in str(exc_info.value)

    def test_whitespace_only_lines_ignored(self):
        """Test that whitespace-only lines are ignored"""
        jsonl = '\n'.join([
            '{"input_text": "Hello", "target_text": "Bonjour"}',
            '   ',  # Whitespace line
            '{"input_text": "Hi", "target_text": "Salut"}',
            '',  # Empty line
            '{"input_text": "Thanks", "target_text": "Merci"}',
        ])

        records = DatasetValidator.validate_jsonl(jsonl, skip_min_samples=True)
        assert len(records) == 3
