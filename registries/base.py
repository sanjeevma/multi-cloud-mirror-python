# registries/base.py
# Author: Sanjeev Maharjan <me@sanjeev.au>

from abc import ABC, abstractmethod
import asyncio
import re
from typing import Tuple

from core.config import Config
from utils.logger import Logger
from utils.types import ValidationResult


class BaseRegistry(ABC):
  def __init__(self, config: Config, logger: Logger):
    self.config = config
    self.logger = logger

  def _parse_image(self, source: str) -> Tuple[str, str]:
    """Parse repository and tag from source image"""
    match = re.match(r'^[^/]*/(.+):(.+)$', source)
    if match:
      return match.group(1), match.group(2)

    # Fallback parsing
    if ':' in source:
      parts = source.split(':')
      tag = parts[-1]
      repo = ':'.join(parts[:-1])
      if '/' in repo:
        repo = '/'.join(repo.split('/')[1:])
      return repo, tag

    return source, 'latest'

  async def _run_crane_command(self, *args) -> Tuple[bool, str, str]:
    """Run crane command and return success, stdout, stderr"""
    try:
      proc = await asyncio.create_subprocess_exec(
        'crane', *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
      )
      stdout, stderr = await proc.communicate()

      return (
        proc.returncode == 0,
        stdout.decode().strip(),
        stderr.decode().strip()
      )
    except Exception as e:
      return False, '', str(e)

  async def _run_command(self, *args) -> Tuple[bool, str, str]:
    """Run generic command and return success, stdout, stderr"""
    try:
      proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
      )
      stdout, stderr = await proc.communicate()

      return (
        proc.returncode == 0,
        stdout.decode().strip(),
        stderr.decode().strip()
      )
    except Exception as e:
      return False, '', str(e)

  @abstractmethod
  async def push_image(self, source: str) -> bool:
    """Push image to registry"""
    pass

  async def validate_access(self) -> ValidationResult:
    """Validate access to registry - optional override"""
    return ValidationResult(success=True)
