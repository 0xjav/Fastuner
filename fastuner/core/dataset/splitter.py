"""
Dataset splitting module for V0.

Implements task-aware, deterministic splitting:
- Classification: Stratified split (preserves label distribution)
- Generation/QA: Random shuffled split
- Seed-based reproducibility
- Minimum sample validation (80/10/10)
"""

import random
import logging
from typing import List, Dict, Any
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class SplitValidationError(Exception):
    """Exception for split validation errors"""

    pass


class DatasetSplitter:
    """Splits datasets with task-aware strategies"""

    # Default split ratios
    DEFAULT_RATIOS = {"train": 0.8, "val": 0.1, "test": 0.1}

    # Minimum absolute samples per split
    MIN_TRAIN_SAMPLES = 80
    MIN_VAL_SAMPLES = 10
    MIN_TEST_SAMPLES = 10

    # Minimum samples per label for classification
    MIN_SAMPLES_PER_LABEL = 3

    @classmethod
    def split(
        cls,
        records: List[Dict[str, str]],
        task_type: str,
        seed: int = 42,
        ratios: Dict[str, float] = None,
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Split dataset based on task type.

        Args:
            records: List of validated records
            task_type: One of "classification", "text_generation", "qa"
            seed: Random seed for reproducibility
            ratios: Custom split ratios (defaults to 80/10/10)

        Returns:
            Dict with keys "train", "val", "test" containing record lists

        Raises:
            SplitValidationError: If split fails validation
        """
        ratios = ratios or cls.DEFAULT_RATIOS

        if task_type == "classification":
            splits = cls._stratified_split(records, ratios, seed)
        else:  # text_generation or qa
            splits = cls._random_split(records, ratios, seed)

        # Validate splits
        cls._validate_splits(splits)

        logger.info(
            f"Split complete: train={len(splits['train'])}, "
            f"val={len(splits['val'])}, test={len(splits['test'])}"
        )

        return splits

    @classmethod
    def _random_split(
        cls,
        records: List[Dict[str, str]],
        ratios: Dict[str, float],
        seed: int,
    ) -> Dict[str, List[Dict[str, str]]]:
        """Random shuffled split for generation/QA tasks"""
        random.seed(seed)
        shuffled = records.copy()
        random.shuffle(shuffled)

        total = len(shuffled)
        train_end = int(total * ratios["train"])
        val_end = train_end + int(total * ratios["val"])

        return {
            "train": shuffled[:train_end],
            "val": shuffled[train_end:val_end],
            "test": shuffled[val_end:],
        }

    @classmethod
    def _stratified_split(
        cls,
        records: List[Dict[str, str]],
        ratios: Dict[str, float],
        seed: int,
    ) -> Dict[str, List[Dict[str, str]]]:
        """Stratified split for classification tasks"""
        random.seed(seed)

        # Group records by label
        label_groups: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        for record in records:
            label = record["target_text"]
            label_groups[label].append(record)

        # Validate minimum samples per label
        for label, group in label_groups.items():
            if len(group) < cls.MIN_SAMPLES_PER_LABEL:
                raise SplitValidationError(
                    f"Label '{label}' has only {len(group)} samples, "
                    f"need at least {cls.MIN_SAMPLES_PER_LABEL}"
                )

        # Split each label group proportionally
        train_records = []
        val_records = []
        test_records = []

        for label, group in label_groups.items():
            random.shuffle(group)  # Shuffle within each label

            total = len(group)
            train_end = int(total * ratios["train"])
            val_end = train_end + int(total * ratios["val"])

            train_records.extend(group[:train_end])
            val_records.extend(group[train_end:val_end])
            test_records.extend(group[val_end:])

        # Final shuffle to mix labels
        random.shuffle(train_records)
        random.shuffle(val_records)
        random.shuffle(test_records)

        splits = {
            "train": train_records,
            "val": val_records,
            "test": test_records,
        }

        # Validate label distribution
        cls._validate_label_distribution(label_groups, splits)

        return splits

    @classmethod
    def _validate_splits(cls, splits: Dict[str, List[Dict[str, str]]]) -> None:
        """Validate minimum sample requirements"""
        if len(splits["train"]) < cls.MIN_TRAIN_SAMPLES:
            raise SplitValidationError(
                f"Train split must have ≥{cls.MIN_TRAIN_SAMPLES} samples, "
                f"got {len(splits['train'])}"
            )

        if len(splits["val"]) < cls.MIN_VAL_SAMPLES:
            raise SplitValidationError(
                f"Val split must have ≥{cls.MIN_VAL_SAMPLES} samples, "
                f"got {len(splits['val'])}"
            )

        if len(splits["test"]) < cls.MIN_TEST_SAMPLES:
            raise SplitValidationError(
                f"Test split must have ≥{cls.MIN_TEST_SAMPLES} samples, "
                f"got {len(splits['test'])}"
            )

    @classmethod
    def _validate_label_distribution(
        cls,
        label_groups: Dict[str, List[Dict[str, str]]],
        splits: Dict[str, List[Dict[str, str]]],
    ) -> None:
        """Validate that label distributions are preserved in stratified splits"""
        for split_name, split_records in splits.items():
            split_label_counts = Counter(r["target_text"] for r in split_records)

            for label in label_groups.keys():
                if label not in split_label_counts:
                    logger.warning(
                        f"Label '{label}' missing from {split_name} split "
                        "(likely due to small sample size)"
                    )
