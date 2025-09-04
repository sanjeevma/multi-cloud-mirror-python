# registries/jfrog.py
# Author: Sanjeev Maharjan <me@sanjeev.au>

from registries.base import BaseRegistry
from utils.types import ValidationResult


class JFrogRegistry(BaseRegistry):
  async def push_image(self, source: str) -> bool:
    """Push image to JFrog Artifactory"""
    repo, tag = self._parse_image(source)

    jfrog_docker_url = f"{self.config.jfrog_url}/artifactory/{self.config.jfrog_repository or 'docker-local'}"
    target = f"{jfrog_docker_url}/{repo}:{tag}"

    self.logger.debug(f"Mirroring {source} to JFrog: {target}")

    # Copy image
    success, stdout, stderr = await self._run_crane_command(
      'copy', source, target, '--platform', self.config.target_platform
    )

    if success:
      self.logger.debug(f"✅ Successfully mirrored to JFrog: {target}")
      return True
    else:
      self.logger.error(f"❌ Failed to mirror to JFrog: {target} - {stderr}")
      return False

  async def validate_access(self) -> ValidationResult:
    """Validate JFrog access"""
    if not all([self.config.jfrog_url, self.config.jfrog_user, self.config.jfrog_token]):
      return ValidationResult(
        success=False,
        message="Missing JFrog credentials (JFROG_URL, JFROG_USER, JFROG_TOKEN)"
      )

    # Test authentication by trying to list repositories
    jfrog_host = self.config.jfrog_url.replace('https://', '').replace('http://', '').split('/')[0]

    success, stdout, stderr = await self._run_crane_command('auth', 'login', 'test')

    return ValidationResult(success=True)
