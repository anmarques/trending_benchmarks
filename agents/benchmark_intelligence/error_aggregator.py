"""
Error aggregation for benchmark extraction pipeline.

Provides type-based bucketing of errors with sample tracking for debugging
and quality monitoring.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


class ErrorAggregator:
    """
    Thread-safe error aggregator with type-based bucketing.

    Tracks errors by type, maintains counts, and stores representative samples
    for debugging. Designed for concurrent processing environments.

    Example:
        >>> aggregator = ErrorAggregator()
        >>> aggregator.add_error("fetch_failure", "model_1", {"url": "...", "error": "timeout"})
        >>> aggregator.add_error("fetch_failure", "model_2", {"url": "...", "error": "404"})
        >>> summary = aggregator.get_summary()
        >>> print(f"Fetch failures: {summary['fetch_failure']['count']}")
    """

    def __init__(self, max_samples_per_type: int = 5):
        """
        Initialize error aggregator.

        Args:
            max_samples_per_type: Maximum number of error samples to keep per type (default: 5)
        """
        self._errors: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "samples": [],
            "models_affected": set()
        })
        self._max_samples = max_samples_per_type
        self._lock = Lock()

        logger.debug(f"ErrorAggregator initialized with max_samples={max_samples_per_type}")

    def add_error(
        self,
        error_type: str,
        model_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add an error to the aggregator.

        Thread-safe method for recording errors during concurrent processing.

        Args:
            error_type: Type of error (e.g., "fetch_failure", "extraction_error", "parse_error")
            model_id: Identifier of the model where error occurred
            details: Optional dictionary with additional error details

        Example:
            >>> aggregator.add_error(
            ...     "arxiv_fetch_failure",
            ...     "meta-llama/Llama-3.1-8B",
            ...     {"url": "https://arxiv.org/abs/...", "status_code": 404}
            ... )
        """
        if not error_type or not model_id:
            logger.warning("add_error called with empty error_type or model_id, skipping")
            return

        with self._lock:
            error_bucket = self._errors[error_type]

            # Increment count
            error_bucket["count"] += 1

            # Track affected model
            error_bucket["models_affected"].add(model_id)

            # Add sample if we haven't reached the limit
            if len(error_bucket["samples"]) < self._max_samples:
                sample = {
                    "model_id": model_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # Add details if provided
                if details:
                    sample["details"] = details

                error_bucket["samples"].append(sample)

            logger.debug(
                f"Error recorded: {error_type} for {model_id} "
                f"(total: {error_bucket['count']})"
            )

    def get_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summary of all errors with counts and samples.

        Returns a dictionary mapping error types to their statistics:
        - count: Total number of errors of this type
        - models_affected: Number of unique models affected
        - samples: List of error samples (up to max_samples_per_type)

        Returns:
            Dictionary of error_type → {count, models_affected, samples}

        Example:
            >>> summary = aggregator.get_summary()
            >>> for error_type, stats in summary.items():
            ...     print(f"{error_type}: {stats['count']} errors, {stats['models_affected']} models")
            ...     for sample in stats['samples']:
            ...         print(f"  - {sample['model_id']}: {sample.get('details', {})}")
        """
        with self._lock:
            summary = {}

            for error_type, error_data in self._errors.items():
                summary[error_type] = {
                    "count": error_data["count"],
                    "models_affected": len(error_data["models_affected"]),
                    "samples": error_data["samples"].copy()
                }

            return summary

    def get_total_errors(self) -> int:
        """
        Get total count of all errors across all types.

        Returns:
            Total number of errors recorded

        Example:
            >>> total = aggregator.get_total_errors()
            >>> print(f"Total errors encountered: {total}")
        """
        with self._lock:
            return sum(error_data["count"] for error_data in self._errors.values())

    def get_error_types(self) -> List[str]:
        """
        Get list of all error types that have been recorded.

        Returns:
            List of error type strings

        Example:
            >>> types = aggregator.get_error_types()
            >>> print(f"Error types: {', '.join(types)}")
        """
        with self._lock:
            return list(self._errors.keys())

    def has_errors(self) -> bool:
        """
        Check if any errors have been recorded.

        Returns:
            True if errors exist, False otherwise

        Example:
            >>> if aggregator.has_errors():
            ...     print("Errors were encountered during processing")
        """
        with self._lock:
            return len(self._errors) > 0

    def reset(self) -> None:
        """
        Clear all recorded errors.

        Useful for resetting state between pipeline runs.

        Example:
            >>> aggregator.reset()
            >>> assert aggregator.get_total_errors() == 0
        """
        with self._lock:
            self._errors.clear()
            logger.info("ErrorAggregator reset")

    def format_summary_text(self) -> str:
        """
        Format error summary as human-readable text.

        Returns:
            Formatted string with error statistics

        Example:
            >>> print(aggregator.format_summary_text())
            Error Summary:
              arxiv_fetch_failure: 15 errors (12 models affected)
              extraction_timeout: 3 errors (3 models affected)
        """
        summary = self.get_summary()

        if not summary:
            return "No errors recorded"

        lines = ["Error Summary:"]

        # Sort by count (descending)
        sorted_types = sorted(
            summary.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )

        for error_type, stats in sorted_types:
            lines.append(
                f"  {error_type}: {stats['count']} errors "
                f"({stats['models_affected']} models affected)"
            )

        total = self.get_total_errors()
        lines.append(f"\nTotal errors: {total}")

        return "\n".join(lines)
