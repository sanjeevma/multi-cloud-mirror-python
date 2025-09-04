# core/processor.py
# Author: Sanjeev Maharjan <me@sanjeev.au>

import asyncio
from typing import List, Dict, Any
from dataclasses import dataclass

from core.config import Config
from utils.logger import Logger
from utils.types import MirrorResult


@dataclass
class ImageTask:
  destinations: List[str]
  source: str
  line_number: int


class ImageProcessor:
  def __init__(self, config: Config, logger: Logger):
    self.config = config
    self.logger = logger
    self.semaphore = asyncio.Semaphore(config.max_parallel_jobs)

  async def process_images(self, images: List[Dict[str, Any]],
                          registries: Dict[str, Any]) -> MirrorResult:
    """Process all images with parallel execution and retry logic"""

    tasks = [
      ImageTask(
        destinations=img['destinations'],
        source=img['source'],
        line_number=img['line_number']
      )
      for img in images
    ]

    # Create coroutines for all images
    coroutines = [
      self._process_single_image(task, registries)
      for task in tasks
    ]

    # Execute with semaphore limiting
    results = await asyncio.gather(*coroutines, return_exceptions=True)

    # Count results
    successful_images = sum(1 for r in results if r is True)
    failed_images = sum(1 for r in results if r is not True)

    return MirrorResult(
      total_images=len(images),
      successful_images=successful_images,
      failed_images=failed_images
    )

  async def _process_single_image(self, task: ImageTask,
                                 registries: Dict[str, Any]) -> bool:
    """Process a single image with retry logic"""
    async with self.semaphore:
      for attempt in range(1, self.config.max_retries + 1):
        try:
          self.logger.debug(f"Attempt {attempt}/{self.config.max_retries} for {task.source}")

          success = True
          for destination in task.destinations:
            destination = destination.strip()

            if destination not in registries:
              self.logger.error(f"Unknown destination: {destination}")
              success = False
              continue

            registry = registries[destination]
            if not await registry.push_image(task.source):
              success = False

          if success:
            self.logger.success(f"Mirrored: {task.source}")
            return True
          else:
            if attempt < self.config.max_retries:
              self.logger.warning(
                f"Attempt {attempt} failed for {task.source}, "
                f"retrying in {self.config.retry_delay}s..."
              )
              await asyncio.sleep(self.config.retry_delay)

        except Exception as e:
          self.logger.error(f"Error processing {task.source}: {e}")
          if attempt < self.config.max_retries:
            await asyncio.sleep(self.config.retry_delay)

      self.logger.error(f"Failed to mirror after {self.config.max_retries} attempts: {task.source}")
      return False
