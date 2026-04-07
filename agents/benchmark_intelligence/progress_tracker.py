"""
Real-time progress tracking for benchmark extraction pipeline.

Provides thread-safe progress counters with periodic console updates
for monitoring long-running operations.
"""

import logging
import time
from typing import Optional
from threading import Lock, Thread
from datetime import datetime

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Thread-safe progress tracker with live console updates.

    Tracks multiple metrics (models, benchmarks, errors) and displays periodic
    progress updates to the console. Designed for concurrent processing with
    high throughput.

    Example:
        >>> tracker = ProgressTracker(total_models=100, update_interval=5.0)
        >>> tracker.start()
        >>> # In worker threads:
        >>> tracker.increment_models_processed()
        >>> tracker.increment_benchmarks_extracted(15)
        >>> tracker.increment_errors_encountered()
        >>> # ...
        >>> tracker.stop()
    """

    def __init__(
        self,
        total_models: int = 0,
        update_interval: float = 5.0,
        enable_console_updates: bool = True
    ):
        """
        Initialize progress tracker.

        Args:
            total_models: Total number of models to process (for percentage calculation)
            update_interval: Seconds between console updates (default: 5.0)
            enable_console_updates: Enable periodic console output (default: True)
        """
        # Counters
        self._models_processed = 0
        self._benchmarks_extracted = 0
        self._errors_encountered = 0
        self._total_models = total_models

        # Configuration
        self._update_interval = update_interval
        self._enable_console = enable_console_updates

        # Thread control
        self._lock = Lock()
        self._running = False
        self._update_thread: Optional[Thread] = None
        self._start_time: Optional[float] = None

        logger.debug(
            f"ProgressTracker initialized: total_models={total_models}, "
            f"update_interval={update_interval}s"
        )

    def increment_models_processed(self, count: int = 1) -> None:
        """
        Increment the count of models processed.

        Thread-safe method for updating progress from worker threads.

        Args:
            count: Number of models to add (default: 1)

        Example:
            >>> tracker.increment_models_processed()  # Add 1
            >>> tracker.increment_models_processed(5)  # Add 5
        """
        with self._lock:
            self._models_processed += count

    def increment_benchmarks_extracted(self, count: int = 1) -> None:
        """
        Increment the count of benchmarks extracted.

        Thread-safe method for updating benchmark extraction progress.

        Args:
            count: Number of benchmarks to add (default: 1)

        Example:
            >>> tracker.increment_benchmarks_extracted(15)  # Model yielded 15 benchmarks
        """
        with self._lock:
            self._benchmarks_extracted += count

    def increment_errors_encountered(self, count: int = 1) -> None:
        """
        Increment the count of errors encountered.

        Thread-safe method for tracking errors during processing.

        Args:
            count: Number of errors to add (default: 1)

        Example:
            >>> tracker.increment_errors_encountered()  # Record an error
        """
        with self._lock:
            self._errors_encountered += count

    def get_stats(self) -> dict:
        """
        Get current progress statistics.

        Returns:
            Dictionary with current counters and calculated metrics

        Example:
            >>> stats = tracker.get_stats()
            >>> print(f"Progress: {stats['models_processed']}/{stats['total_models']} "
            ...       f"({stats['percent_complete']:.1f}%)")
        """
        with self._lock:
            elapsed = time.time() - self._start_time if self._start_time else 0
            percent = (
                (self._models_processed / self._total_models * 100)
                if self._total_models > 0
                else 0
            )

            return {
                "models_processed": self._models_processed,
                "benchmarks_extracted": self._benchmarks_extracted,
                "errors_encountered": self._errors_encountered,
                "total_models": self._total_models,
                "percent_complete": percent,
                "elapsed_seconds": elapsed,
            }

    def start(self) -> None:
        """
        Start the progress tracker and begin periodic console updates.

        Spawns a background thread that displays progress every update_interval seconds.

        Example:
            >>> tracker = ProgressTracker(total_models=100)
            >>> tracker.start()
            >>> # ... processing happens ...
            >>> tracker.stop()
        """
        if self._running:
            logger.warning("ProgressTracker already running")
            return

        with self._lock:
            self._running = True
            self._start_time = time.time()

        if self._enable_console:
            self._update_thread = Thread(target=self._update_loop, daemon=True)
            self._update_thread.start()
            logger.debug("ProgressTracker started with console updates")
        else:
            logger.debug("ProgressTracker started (console updates disabled)")

    def stop(self) -> None:
        """
        Stop the progress tracker and display final statistics.

        Stops the background update thread and prints a final progress summary.

        Example:
            >>> tracker.stop()
            ✓ Processing complete: 100/100 models, 1,247 benchmarks, 3 errors
        """
        if not self._running:
            return

        with self._lock:
            self._running = False

        # Wait for update thread to finish
        if self._update_thread and self._update_thread.is_alive():
            self._update_thread.join(timeout=1.0)

        # Display final stats
        if self._enable_console:
            self._display_progress(final=True)

        logger.debug("ProgressTracker stopped")

    def _update_loop(self) -> None:
        """
        Background thread that periodically displays progress updates.

        Runs in a daemon thread, updating console every update_interval seconds.
        """
        while self._running:
            time.sleep(self._update_interval)
            if self._running:  # Check again after sleep
                self._display_progress()

    def _display_progress(self, final: bool = False) -> None:
        """
        Display current progress to console.

        Args:
            final: If True, display as final summary (default: False)
        """
        stats = self.get_stats()

        models = stats["models_processed"]
        total = stats["total_models"]
        benchmarks = stats["benchmarks_extracted"]
        errors = stats["errors_encountered"]
        percent = stats["percent_complete"]
        elapsed = stats["elapsed_seconds"]

        # Format elapsed time
        if elapsed >= 60:
            time_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
        else:
            time_str = f"{int(elapsed)}s"

        # Build status message
        if final:
            prefix = "✓ Processing complete:"
        else:
            prefix = "  Progress:"

        # Format numbers with commas for readability
        benchmarks_str = f"{benchmarks:,}"

        if total > 0:
            msg = (
                f"{prefix} {models}/{total} models ({percent:.1f}%), "
                f"{benchmarks_str} benchmarks, {errors} errors [{time_str}]"
            )
        else:
            msg = (
                f"{prefix} {models} models, {benchmarks_str} benchmarks, "
                f"{errors} errors [{time_str}]"
            )

        # Use logger for periodic updates, direct print for final
        if final:
            logger.info(msg)
        else:
            logger.info(msg)

    def reset(self) -> None:
        """
        Reset all counters to zero.

        Useful for running multiple batches with the same tracker instance.

        Example:
            >>> tracker.reset()
            >>> tracker.start()
            >>> # Process new batch...
        """
        if self._running:
            raise RuntimeError("Cannot reset while tracker is running. Call stop() first.")

        with self._lock:
            self._models_processed = 0
            self._benchmarks_extracted = 0
            self._errors_encountered = 0
            self._start_time = None

        logger.debug("ProgressTracker reset")

    def set_total_models(self, total: int) -> None:
        """
        Update the total number of models to process.

        Useful when total is not known at initialization time.

        Args:
            total: Total number of models

        Example:
            >>> tracker = ProgressTracker()
            >>> tracker.set_total_models(150)
            >>> tracker.start()
        """
        with self._lock:
            self._total_models = total

        logger.debug(f"Total models set to {total}")
