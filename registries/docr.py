# registries/docr.py
# Author: Sanjeev Maharjan <me@sanjeev.au>

from registries.base import BaseRegistry
from utils.types import ValidationResult


class DOCRRegistry(BaseRegistry):
  async def push_image(self, source: str) -> bool:
    """Push image to DigitalOcean Container Registry"""
    repo, tag = self._parse_image(source)

    success_count = 0
    total_regions = len(self.config.docr_regions or ['nyc3'])

    for region in (self.config.docr_regions or ['nyc3']):
      docr_url = f"registry.digitalocean.com/{self.config.docr_registry_name}"
      target = f"{docr_url}/{repo}:{tag}"

      self.logger.debug(f"Mirroring {source} to DOCR: {target}")

      # Copy image
      success, stdout, stderr = await self._run_crane_command(
        'copy', source, target, '--platform', self.config.target_platform
      )

      if success:
        self.logger.debug(f"✅ Successfully mirrored to DOCR: {target}")
        success_count += 1
      else:
        self.logger.error(f"❌ Failed to mirror to DOCR: {target} - {stderr}")

    return success_count == total_regions

  async def validate_access(self) -> ValidationResult:
    """Validate DigitalOcean Container Registry access"""
    if not self.config.docr_token:
      return ValidationResult(
        success=False,
        message="DOCR_TOKEN not configured"
      )

    if not self.config.docr_registry_name:
      return ValidationResult(
        success=False,
        message="DOCR_REGISTRY_NAME not configured"
      )

    return ValidationResult(success=True)
