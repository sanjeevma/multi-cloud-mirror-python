# registries/acr.py
# Author: Sanjeev Maharjan <me@sanjeev.au>

from registries.base import BaseRegistry
from utils.types import ValidationResult


class ACRRegistry(BaseRegistry):
  async def push_image(self, source: str) -> bool:
    """Push image to Azure Container Registry"""
    repo, tag = self._parse_image(source)

    success_count = 0
    total_regions = len(self.config.azure_regions)

    for region in self.config.azure_regions:
      acr_name = (self.config.azure_acr_name or
                  f"{self.config.azure_acr_name_prefix or 'org'}acr{region}")
      acr_url = f"{acr_name}.azurecr.io"
      target = f"{acr_url}/{repo}:{tag}"

      self.logger.debug(f"Mirroring {source} to ACR: {target}")

      # Create ACR if it doesn't exist
      success, stdout, stderr = await self._run_command(
        'az', 'acr', 'show',
        '--name', acr_name,
        '--resource-group', self.config.azure_resource_group
      )

      if not success:
        self.logger.debug(f"Creating ACR: {acr_name}")
        success, stdout, stderr = await self._run_command(
          'az', 'acr', 'create',
          '--name', acr_name,
          '--resource-group', self.config.azure_resource_group,
          '--location', region,
          '--sku', 'Standard',
          '--admin-enabled', 'false'
        )

        if not success:
          self.logger.error(f"Failed to create ACR: {stderr}")
          continue

      # Login to ACR
      success, stdout, stderr = await self._run_command(
        'az', 'acr', 'login', '--name', acr_name
      )

      if not success:
        self.logger.error(f"Failed to login to ACR: {stderr}")
        continue

      # Copy image
      success, stdout, stderr = await self._run_crane_command(
        'copy', source, target, '--platform', self.config.target_platform
      )

      if success:
        self.logger.debug(f"✅ Successfully mirrored to ACR: {target}")
        success_count += 1
      else:
        self.logger.error(f"❌ Failed to mirror to ACR: {target} - {stderr}")

    return success_count == total_regions

  async def validate_access(self) -> ValidationResult:
    """Validate ACR access"""
    if not self.config.azure_resource_group:
      return ValidationResult(
        success=False,
        message="AZURE_RESOURCE_GROUP not configured"
      )

    # Check if resource group exists
    success, stdout, stderr = await self._run_command(
      'az', 'group', 'show', '--name', self.config.azure_resource_group
    )

    if not success:
      return ValidationResult(
        success=False,
        message=f"Azure resource group not found: {self.config.azure_resource_group}"
      )

    return ValidationResult(success=True)
