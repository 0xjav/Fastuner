"""Unit tests for DatasetSplitter"""

import pytest
from fastuner.core.dataset.splitter import DatasetSplitter, SplitError
from fastuner.models.dataset import TaskType


class TestDatasetSplitter:
    """Test suite for dataset splitting"""

    @pytest.fixture
    def classification_records(self):
        """Sample classification dataset with labels"""
        return [
            {"input_text": f"Sample {i}", "target_text": f"class_{i % 3}"}
            for i in range(120)  # 40 of each class
        ]

    @pytest.fixture
    def generation_records(self):
        """Sample generation dataset"""
        return [
            {"input_text": f"Input {i}", "target_text": f"Output {i}"}
            for i in range(120)
        ]

    def test_random_split_default_ratios(self, generation_records):
        """Test random split with default 80/10/10 ratio"""
        splits = DatasetSplitter.split(
            records=generation_records,
            task_type=TaskType.TEXT_GENERATION,
            seed=42,
        )

        assert "train" in splits
        assert "validation" in splits
        assert "test" in splits

        # Check approximate ratios (80/10/10)
        total = len(generation_records)
        assert len(splits["train"]) == pytest.approx(total * 0.8, abs=2)
        assert len(splits["validation"]) == pytest.approx(total * 0.1, abs=2)
        assert len(splits["test"]) == pytest.approx(total * 0.1, abs=2)

        # Check no data loss
        assert len(splits["train"]) + len(splits["validation"]) + len(splits["test"]) == total

    def test_random_split_custom_ratios(self, generation_records):
        """Test random split with custom ratios"""
        splits = DatasetSplitter.split(
            records=generation_records,
            task_type=TaskType.TEXT_GENERATION,
            seed=42,
            ratios=(0.7, 0.2, 0.1),
        )

        total = len(generation_records)
        assert len(splits["train"]) == pytest.approx(total * 0.7, abs=2)
        assert len(splits["validation"]) == pytest.approx(total * 0.2, abs=2)
        assert len(splits["test"]) == pytest.approx(total * 0.1, abs=2)

    def test_stratified_split_classification(self, classification_records):
        """Test stratified split maintains class distribution"""
        splits = DatasetSplitter.split(
            records=classification_records,
            task_type=TaskType.CLASSIFICATION,
            seed=42,
        )

        # Count classes in each split
        def count_classes(records):
            classes = {}
            for r in records:
                label = r["target_text"]
                classes[label] = classes.get(label, 0) + 1
            return classes

        train_classes = count_classes(splits["train"])
        val_classes = count_classes(splits["validation"])
        test_classes = count_classes(splits["test"])

        # Each class should appear in each split
        assert len(train_classes) == 3
        assert len(val_classes) == 3
        assert len(test_classes) == 3

        # Check rough proportions are maintained
        total_per_class = 40
        for label in ["class_0", "class_1", "class_2"]:
            assert train_classes[label] == pytest.approx(total_per_class * 0.8, abs=2)
            assert val_classes[label] == pytest.approx(total_per_class * 0.1, abs=1)
            assert test_classes[label] == pytest.approx(total_per_class * 0.1, abs=1)

    def test_reproducible_splits(self, generation_records):
        """Test that same seed produces same splits"""
        splits1 = DatasetSplitter.split(
            records=generation_records.copy(),
            task_type=TaskType.TEXT_GENERATION,
            seed=42,
        )

        splits2 = DatasetSplitter.split(
            records=generation_records.copy(),
            task_type=TaskType.TEXT_GENERATION,
            seed=42,
        )

        # Same seed should produce identical splits
        assert splits1["train"] == splits2["train"]
        assert splits1["validation"] == splits2["validation"]
        assert splits1["test"] == splits2["test"]

    def test_different_seeds_different_splits(self, generation_records):
        """Test that different seeds produce different splits"""
        splits1 = DatasetSplitter.split(
            records=generation_records.copy(),
            task_type=TaskType.TEXT_GENERATION,
            seed=42,
        )

        splits2 = DatasetSplitter.split(
            records=generation_records.copy(),
            task_type=TaskType.TEXT_GENERATION,
            seed=99,
        )

        # Different seeds should produce different splits
        assert splits1["train"] != splits2["train"]

    def test_minimum_split_validation(self):
        """Test validation fails with insufficient samples"""
        # Create dataset with only 50 samples (below minimum for splits)
        small_records = [
            {"input_text": f"Sample {i}", "target_text": f"Output {i}"}
            for i in range(50)
        ]

        with pytest.raises(SplitError) as exc_info:
            DatasetSplitter.split(
                records=small_records,
                task_type=TaskType.TEXT_GENERATION,
                seed=42,
            )

        assert "insufficient samples" in str(exc_info.value).lower()

    def test_no_data_leakage(self, generation_records):
        """Test that splits don't share any samples"""
        splits = DatasetSplitter.split(
            records=generation_records,
            task_type=TaskType.TEXT_GENERATION,
            seed=42,
        )

        # Convert to sets of tuples for comparison
        train_set = {(r["input_text"], r["target_text"]) for r in splits["train"]}
        val_set = {(r["input_text"], r["target_text"]) for r in splits["validation"]}
        test_set = {(r["input_text"], r["target_text"]) for r in splits["test"]}

        # Check no overlap
        assert len(train_set & val_set) == 0
        assert len(train_set & test_set) == 0
        assert len(val_set & test_set) == 0

    def test_qa_task_type_random_split(self):
        """Test that QA task type uses random split"""
        qa_records = [
            {"input_text": f"Question {i}", "target_text": f"Answer {i}"}
            for i in range(120)
        ]

        splits = DatasetSplitter.split(
            records=qa_records,
            task_type=TaskType.QA,
            seed=42,
        )

        # Should work like random split
        assert len(splits["train"]) == pytest.approx(120 * 0.8, abs=2)

    def test_invalid_ratios_sum(self, generation_records):
        """Test validation fails with invalid ratio sum"""
        with pytest.raises(SplitError) as exc_info:
            DatasetSplitter.split(
                records=generation_records,
                task_type=TaskType.TEXT_GENERATION,
                seed=42,
                ratios=(0.5, 0.3, 0.1),  # Sum is 0.9, not 1.0
            )

        assert "ratios must sum to 1.0" in str(exc_info.value).lower()

    def test_invalid_ratios_negative(self, generation_records):
        """Test validation fails with negative ratios"""
        with pytest.raises(SplitError) as exc_info:
            DatasetSplitter.split(
                records=generation_records,
                task_type=TaskType.TEXT_GENERATION,
                seed=42,
                ratios=(0.9, 0.2, -0.1),
            )

        assert "ratios must be positive" in str(exc_info.value).lower()

    def test_empty_records(self):
        """Test validation fails with empty records"""
        with pytest.raises(SplitError) as exc_info:
            DatasetSplitter.split(
                records=[],
                task_type=TaskType.TEXT_GENERATION,
                seed=42,
            )

        assert "empty" in str(exc_info.value).lower()

    def test_single_class_stratification(self):
        """Test stratified split with only one class"""
        single_class_records = [
            {"input_text": f"Sample {i}", "target_text": "class_A"}
            for i in range(120)
        ]

        # Should still work (degenerates to random split)
        splits = DatasetSplitter.split(
            records=single_class_records,
            task_type=TaskType.CLASSIFICATION,
            seed=42,
        )

        assert len(splits["train"]) == pytest.approx(120 * 0.8, abs=2)
