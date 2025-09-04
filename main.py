#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path

import click

from core.mirror import ContainerMirror
from core.config import ConfigManager
from utils.logger import Logger


@click.command()
@click.option('-f', '--file', 'image_list_file',
              default='config/example-list.txt',
              help='Image list file')
@click.option('-j', '--jobs', 'max_parallel_jobs',
              default=3, type=int,
              help='Max parallel jobs')
@click.option('-r', '--retries', 'max_retries',
              default=3, type=int,
              help='Max retries per image')
@click.option('-p', '--platform', 'target_platform',
              default='linux/amd64',
              help='Target platform')
@click.option('-d', '--debug', 'debug_mode',
              is_flag=True,
              help='Enable debug output')
@click.option('-v', '--validate', 'validate_only',
              is_flag=True,
              help='Run validation only')
@click.help_option('-h', '--help')
def main(image_list_file, max_parallel_jobs, max_retries, target_platform, debug_mode, validate_only):
  """Multi-cloud container image mirroring tool"""

  logger = Logger(debug=debug_mode)
  logger.info("🚀 Multi-Cloud Container Mirror")
  logger.info("===============================")

  try:
    config_manager = ConfigManager(
      image_list_file=image_list_file,
      max_parallel_jobs=max_parallel_jobs,
      max_retries=max_retries,
      target_platform=target_platform,
      debug=debug_mode
    )

    config = config_manager.load_config()

    mirror = ContainerMirror(config, logger)

    if validate_only:
      result = asyncio.run(mirror.validate_setup())
      if not result.success:
        logger.error("Validation failed")
        sys.exit(1)
      logger.success("Validation passed!")
      return

    result = asyncio.run(mirror.run())

    if result.failed_images > 0:
      logger.error(f"Mirroring completed with {result.failed_images} failures")
      sys.exit(1)

    logger.success("Multi-cloud mirroring complete!")

  except KeyboardInterrupt:
    logger.info("Cleaning up...")
    sys.exit(130)
  except Exception as e:
    logger.error(f"Fatal error: {e}")
    if debug_mode:
      import traceback
      traceback.print_exc()
    sys.exit(1)


if __name__ == '__main__':
  main()
