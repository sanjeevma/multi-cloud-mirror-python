# core/mirror.py
# Author: Sanjeev Maharjan <me@sanjeev.au>

import asyncio
from typing import List, Dict, Any
from pathlib import Path

from core.config import Config
from core.auth import RegistryAuthenticator
from core.processor import ImageProcessor
from utils.logger import Logger
from utils.types import ValidationResult, MirrorResult
from registries.ecr import ECRRegistry
from registries.gar import GARRegistry
from registries.acr import ACRRegistry
from registries.jfrog import JFrogRegistry
from registries.docr import DOCRRegistry


class ContainerMirror:
  def __init__(self, config: Config, logger: Logger):
    self.config = config
    self.logger = logger
    self.authenticator = RegistryAuthenticator(config, logger)
    self.processor = ImageProcessor(config, logger)
    self.registries = self._initialize_registries()

  def _initialize_registries(self) -> Dict[str, Any]:
    """Initialize all registry handlers"""
    registries = {}

    if self.config.ecr_regions:
      registries['ECR'] = ECRRegistry(self.config, self.logger)

    if self.config.gcp_regions:
      registries['GAR'] = GARRegistry(self.config, self.logger)

    if self.config.azure_regions:
      registries['ACR'] = ACRRegistry(self.config, self.logger)

    if self.config.jfrog_url:
      registries['JFROG'] = JFrogRegistry(self.config, self.logger)

    if self.config.docr_token:
      registries['DOCR'] = DOCRRegistry(self.config, self.logger)

    return registries

  async def validate_setup(self) -> ValidationResult:
    """Validate tools, authentication, and configuration"""
    self.logger.info("Validating setup...")

    # Validate crane tool
    try:
      proc = await asyncio.create_subprocess_exec(
        'crane', 'version',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
      )
      await proc.communicate()
      if proc.returncode != 0:
        return ValidationResult(success=False, message="crane tool not found")
    except FileNotFoundError:
      return ValidationResult(success=False, message="crane tool not installed")

    # Validate image list file
    if not Path(self.config.image_list_file).exists():
      return ValidationResult(
        success=False,
        message=f"Image list file not found: {self.config.image_list_file}"
      )

    # Validate registry authentication
    auth_result = await self.authenticator.authenticate_all()
    if not auth_result.success:
      return auth_result

    # Validate registry access
    for registry_name, registry in self.registries.items():
      if hasattr(registry, 'validate_access'):
        result = await registry.validate_access()
        if not result.success:
          return ValidationResult(
            success=False,
            message=f"{registry_name} validation failed: {result.message}"
          )

    self.logger.success("Setup validation passed")
    return ValidationResult(success=True)

  async def run(self) -> MirrorResult:
    """Run the mirroring process"""
    self.logger.info(f"Processing image list: {self.config.image_list_file}")

    # Authenticate first
    auth_result = await self.authenticator.authenticate_all()
    if not auth_result.success:
      raise RuntimeError(f"Authentication failed: {auth_result.message}")

    # Load and parse image list
    images = self._load_image_list()

    self.logger.info(f"Total images to mirror: {len(images)}")

    # Process images with parallel execution
    results = await self.processor.process_images(images, self.registries)

    # Summary
    self.logger.info("")
    self.logger.info("Mirroring Summary")
    self.logger.info("=================")
    self.logger.success(f"Successful: {results.successful_images}")

    if results.failed_images > 0:
      self.logger.error(f"Failed: {results.failed_images}")
    else:
      self.logger.success(f"Failed: {results.failed_images}")

    self.logger.info(f"Total: {results.total_images}")

    return results

  def _load_image_list(self) -> List[Dict[str, str]]:
    """Load and parse the image list file"""
    images = []

    with open(self.config.image_list_file, 'r') as f:
      for line_num, line in enumerate(f, 1):
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith('#') or line.startswith('--'):
          continue

        parts = line.split()
        if len(parts) < 2:
          self.logger.warning(f"Line {line_num}: Invalid format, skipping")
          continue

        dest = parts[0]
        source = parts[1]

        # Validate destination
        valid_targets = ['ECR', 'GAR', 'ACR', 'JFROG', 'DOCR']
        dest_targets = [d.strip() for d in dest.split(',')]

        if not any(target in valid_targets for target in dest_targets):
          self.logger.warning(f"Line {line_num}: Invalid destination '{dest}', skipping")
          continue

        images.append({
          'destinations': dest_targets,
          'source': source,
          'line_number': line_num
        })

    return images
