"""
Dataset splitting module for V0.

Implements deterministic splitting for text generation tasks:
- Random shuffled split for TEXT_GENERATION tasks
- 80/10/10 train/val/test split with configurable ratios
- Seed-based reproducibility
- Minimum sample validation (80/10/10 samples minimum)
"""

import random
import logging
from typing import List, Dict

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

    @classmethod
    def split(
        cls,
        records: List[Dict[str, str]],
        task_type: str,
        seed: int = 42,
        ratios: Dict[str, float] = None,
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Split dataset for text generation tasks.

        Args:
            records: List of validated records
            task_type: Task type (currently only TEXT_GENERATION supported)
            seed: Random seed for reproducibility
            ratios: Custom split ratios (defaults to 80/10/10)

        Returns:
            Dict with keys "train", "val", "test" containing record lists

        Raises:
            SplitValidationError: If split fails validation
        """
        ratios = ratios or cls.DEFAULT_RATIOS

        # Random shuffled split for text generation
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
