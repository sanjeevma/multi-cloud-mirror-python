# registries/ecr.py
# Author: Sanjeev Maharjan <me@sanjeev.au>

from registries.base import BaseRegistry
from utils.types import ValidationResult


class ECRRegistry(BaseRegistry):
  async def push_image(self, source: str) -> bool:
    """Push image to AWS ECR"""
    repo, tag = self._parse_image(source)

    success_count = 0
    total_regions = len(self.config.ecr_regions)

    for region in self.config.ecr_regions:
      # Get AWS account ID for this region
      success, account_id, stderr = await self._run_command(
        'aws', 'sts', 'get-caller-identity',
        '--query', 'Account', '--output', 'text'
      )

      if not success:
        self.logger.error(f"Failed to get AWS account ID: {stderr}")
        continue

      ecr_url = f"{account_id.strip()}.dkr.ecr.{region}.amazonaws.com"
      target = f"{ecr_url}/{repo}:{tag}"

      self.logger.debug(f"Mirroring {source} to ECR: {target}")

      # Create repository if it doesn't exist
      success, stdout, stderr = await self._run_command(
        'aws', 'ecr', 'describe-repositories',
        '--repository-name', repo,
        '--region', region
      )

      if not success:
        self.logger.debug(f"Creating ECR repository: {repo}")
        success, stdout, stderr = await self._run_command(
          'aws', 'ecr', 'create-repository',
          '--repository-name', repo,
          '--image-scanning-configuration', 'scanOnPush=true',
          '--region', region
        )

        if not success:
          self.logger.error(f"Failed to create ECR repository: {stderr}")
          continue

      # Copy image
      success, stdout, stderr = await self._run_crane_command(
        'copy', source, target, '--platform', self.config.target_platform
      )

      if success:
        self.logger.debug(f"✅ Successfully mirrored to ECR: {target}")
        success_count += 1
      else:
        self.logger.error(f"❌ Failed to mirror to ECR: {target} - {stderr}")

    return success_count == total_regions

  async def validate_access(self) -> ValidationResult:
    """Validate ECR access in all configured regions"""
    for region in self.config.ecr_regions:
      success, stdout, stderr = await self._run_command(
        'aws', 'ecr', 'describe-repositories',
        '--region', region,
        '--max-items', '1'
      )

      if not success:
        return ValidationResult(
          success=False,
          message=f"ECR access failed in {region}: {stderr}"
        )

    return ValidationResult(success=True)
