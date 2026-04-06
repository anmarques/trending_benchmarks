"""
Concurrent Model Processor for parallel benchmark extraction.

Provides high-concurrency processing of models (20+ workers) using
asyncio for I/O-bound operations and ThreadPoolExecutor for CPU-bound tasks.
"""

import asyncio
import logging
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a processing task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProcessingTask:
    """
    Represents a single model processing task.

    Attributes:
        model_id: Unique identifier for the model
        model_data: Model information dictionary
        status: Current processing status
        result: Processing result (populated after completion)
        error: Error information (populated on failure)
    """
    model_id: str
    model_data: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ConcurrentModelProcessor:
    """
    Manages concurrent processing of models with configurable parallelism.

    Supports both I/O-bound operations (asyncio) and CPU-bound operations
    (ThreadPoolExecutor) to maximize throughput for 20+ concurrent models.
    """

    def __init__(
        self,
        max_workers: int = 20,
        use_async: bool = False
    ):
        """
        Initialize concurrent processor.

        Args:
            max_workers: Maximum number of concurrent workers (default: 20)
            use_async: Use asyncio for I/O-bound operations (default: False)
        """
        self.max_workers = max_workers
        self.use_async = use_async
        self.tasks: List[ProcessingTask] = []

    def process_models(
        self,
        models: List[Dict[str, Any]],
        process_func: Callable[[Dict[str, Any]], Dict[str, Any]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple models in parallel using ThreadPoolExecutor.

        Args:
            models: List of model dictionaries to process
            process_func: Function to process each model (takes model dict, returns result dict)
            progress_callback: Optional callback for progress updates (completed, total)

        Returns:
            List of processing results (same order as input models)

        Example:
            def extract_benchmarks(model_dict):
                # ... extract benchmarks from model ...
                return {"model_id": model_dict["id"], "benchmarks": [...]}

            processor = ConcurrentModelProcessor(max_workers=30)
            results = processor.process_models(models, extract_benchmarks)
        """
        if not models:
            return []

        logger.info(f"Starting parallel processing of {len(models)} models with {self.max_workers} workers")

        # Create tasks
        self.tasks = [
            ProcessingTask(
                model_id=model.get('id', f'model_{i}'),
                model_data=model
            )
            for i, model in enumerate(models)
        ]

        results = []
        completed = 0
        total = len(models)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._safe_process, task, process_func): task
                for task in self.tasks
            }

            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    results.append(result)

                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    logger.error(f"Failed to process {task.model_id}: {e}")
                    # Continue processing other models
                    results.append({
                        "model_id": task.model_id,
                        "error": str(e),
                        "status": "failed"
                    })

                finally:
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total)

        logger.info(
            f"Completed processing {len(models)} models: "
            f"{self.get_success_count()} succeeded, {self.get_failure_count()} failed"
        )

        return results

    async def process_models_async(
        self,
        models: List[Dict[str, Any]],
        async_process_func: Callable[[Dict[str, Any]], Any],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple models in parallel using asyncio (for I/O-bound operations).

        Args:
            models: List of model dictionaries to process
            async_process_func: Async function to process each model
            progress_callback: Optional callback for progress updates

        Returns:
            List of processing results
        """
        if not models:
            return []

        logger.info(f"Starting async processing of {len(models)} models with concurrency {self.max_workers}")

        # Create tasks
        self.tasks = [
            ProcessingTask(
                model_id=model.get('id', f'model_{i}'),
                model_data=model
            )
            for i, model in enumerate(models)
        ]

        results = []
        completed = 0
        total = len(models)

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.max_workers)

        async def process_with_semaphore(task: ProcessingTask):
            """Process a task with semaphore limiting."""
            async with semaphore:
                return await self._safe_process_async(task, async_process_func)

        # Process all tasks concurrently
        tasks_futures = [process_with_semaphore(task) for task in self.tasks]

        for coro in asyncio.as_completed(tasks_futures):
            try:
                result = await coro
                results.append(result)

            except Exception as e:
                logger.error(f"Async processing failed: {e}")
                results.append({"error": str(e), "status": "failed"})

            finally:
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

        logger.info(
            f"Completed async processing: "
            f"{self.get_success_count()} succeeded, {self.get_failure_count()} failed"
        )

        return results

    def _safe_process(
        self,
        task: ProcessingTask,
        process_func: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Safely execute processing function with error handling.

        Args:
            task: Processing task
            process_func: Function to process model data

        Returns:
            Processing result

        Raises:
            Exception: If processing fails
        """
        task.status = TaskStatus.RUNNING

        try:
            result = process_func(task.model_data)
            return result

        except Exception as e:
            logger.error(f"Error processing {task.model_id}: {e}")
            raise

    async def _safe_process_async(
        self,
        task: ProcessingTask,
        async_process_func: Callable[[Dict[str, Any]], Any]
    ) -> Dict[str, Any]:
        """
        Safely execute async processing function with error handling.

        Args:
            task: Processing task
            async_process_func: Async function to process model data

        Returns:
            Processing result
        """
        task.status = TaskStatus.RUNNING

        try:
            result = await async_process_func(task.model_data)
            task.status = TaskStatus.COMPLETED
            task.result = result
            return result

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Async error processing {task.model_id}: {e}")
            raise

    def get_success_count(self) -> int:
        """Get number of successfully completed tasks."""
        return sum(1 for task in self.tasks if task.status == TaskStatus.COMPLETED)

    def get_failure_count(self) -> int:
        """Get number of failed tasks."""
        return sum(1 for task in self.tasks if task.status == TaskStatus.FAILED)

    def get_failed_tasks(self) -> List[ProcessingTask]:
        """Get list of failed tasks with error details."""
        return [task for task in self.tasks if task.status == TaskStatus.FAILED]

    def get_summary(self) -> Dict[str, Any]:
        """
        Get processing summary statistics.

        Returns:
            Dictionary with counts and status breakdown
        """
        return {
            "total": len(self.tasks),
            "completed": self.get_success_count(),
            "failed": self.get_failure_count(),
            "pending": sum(1 for task in self.tasks if task.status == TaskStatus.PENDING),
            "running": sum(1 for task in self.tasks if task.status == TaskStatus.RUNNING),
        }
