# registries/gar.py
# Author: Sanjeev Maharjan <me@sanjeev.au>

from registries.base import BaseRegistry
from utils.types import ValidationResult


class GARRegistry(BaseRegistry):
  async def push_image(self, source: str) -> bool:
    """Push image to Google Artifact Registry"""
    repo, tag = self._parse_image(source)

    success_count = 0
    total_regions = len(self.config.gcp_regions)

    for region in self.config.gcp_regions:
      gar_url = f"{region}-docker.pkg.dev/{self.config.gcp_project_id}/k8s-assets"
      target = f"{gar_url}/{repo}:{tag}"

      self.logger.debug(f"Mirroring {source} to GAR: {target}")

      # Create repository if it doesn't exist
      success, stdout, stderr = await self._run_command(
        'gcloud', 'artifacts', 'repositories', 'describe', 'k8s-assets',
        '--location', region,
        '--project', self.config.gcp_project_id
      )

      if not success:
        self.logger.debug(f"Creating GAR repository: k8s-assets in {region}")
        success, stdout, stderr = await self._run_command(
          'gcloud', 'artifacts', 'repositories', 'create', 'k8s-assets',
          '--repository-format', 'docker',
          '--location', region,
          '--project', self.config.gcp_project_id
        )

        if not success:
          self.logger.error(f"Failed to create GAR repository: {stderr}")
          continue

      # Copy image
      success, stdout, stderr = await self._run_crane_command(
        'copy', source, target, '--platform', self.config.target_platform
      )

      if success:
        self.logger.debug(f"✅ Successfully mirrored to GAR: {target}")
        success_count += 1
      else:
        self.logger.error(f"❌ Failed to mirror to GAR: {target} - {stderr}")

    return success_count == total_regions

  async def validate_access(self) -> ValidationResult:
    """Validate GAR access in all configured regions"""
    if not self.config.gcp_project_id:
      return ValidationResult(
        success=False,
        message="GCP_PROJECT_ID not configured"
      )

    for region in self.config.gcp_regions:
      success, stdout, stderr = await self._run_command(
        'gcloud', 'artifacts', 'locations', 'describe', region
      )

      if not success:
        return ValidationResult(
          success=False,
          message=f"GAR access failed in {region}: {stderr}"
        )

    return ValidationResult(success=True)
