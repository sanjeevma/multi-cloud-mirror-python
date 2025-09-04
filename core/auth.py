# core/auth.py
# Author: Sanjeev Maharjan <me@sanjeev.au>

import asyncio
import subprocess
from typing import Optional

from core.config import Config
from utils.logger import Logger
from utils.types import ValidationResult


class RegistryAuthenticator:
  def __init__(self, config: Config, logger: Logger):
    self.config = config
    self.logger = logger

  async def authenticate_all(self) -> ValidationResult:
    """Authenticate to all configured registries"""
    self.logger.info("Authenticating to registries...")

    auth_tasks = []

    if self.config.ecr_regions:
      auth_tasks.append(self._authenticate_ecr())

    if self.config.gcp_regions:
      auth_tasks.append(self._authenticate_gar())

    if self.config.azure_regions:
      auth_tasks.append(self._authenticate_acr())

    if self.config.jfrog_url:
      auth_tasks.append(self._authenticate_jfrog())

    if self.config.docr_token:
      auth_tasks.append(self._authenticate_docr())

    # Execute all authentications
    results = await asyncio.gather(*auth_tasks, return_exceptions=True)

    # Check for failures
    failures = [r for r in results if isinstance(r, Exception) or (isinstance(r, ValidationResult) and not r.success)]

    if failures:
      return ValidationResult(
        success=False,
        message=f"Authentication failed for {len(failures)} registries"
      )

    self.logger.success("Authentication complete")
    return ValidationResult(success=True)

  async def _authenticate_ecr(self) -> ValidationResult:
    """Authenticate to AWS ECR"""
    self.logger.debug("Authenticating to AWS ECR regions...")

    try:
      for region in self.config.ecr_regions:
        # Get ECR login token
        proc = await asyncio.create_subprocess_exec(
          'aws', 'ecr', 'get-login-password', '--region', region,
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
          self.logger.warning(f"ECR authentication failed for {region}: {stderr.decode()}")
          continue

        token = stdout.decode().strip()

        # Get AWS account ID
        proc = await asyncio.create_subprocess_exec(
          'aws', 'sts', 'get-caller-identity', '--query', 'Account', '--output', 'text',
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
          continue

        account_id = stdout.decode().strip()
        ecr_url = f"{account_id}.dkr.ecr.{region}.amazonaws.com"

        # Login with crane
        proc = await asyncio.create_subprocess_exec(
          'crane', 'auth', 'login', '-u', 'AWS', '-p', token, ecr_url,
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

        if proc.returncode == 0:
          self.logger.debug(f"Authenticated to ECR region: {region}")

    except Exception as e:
      return ValidationResult(success=False, message=f"ECR auth error: {e}")

    return ValidationResult(success=True)

  async def _authenticate_gar(self) -> ValidationResult:
    """Authenticate to Google Artifact Registry"""
    self.logger.debug("Authenticating to Google GAR...")

    try:
      # Set service account impersonation if specified
      if self.config.gcp_service_account:
        proc = await asyncio.create_subprocess_exec(
          'gcloud', 'config', 'set', 'auth/impersonate_service_account',
          self.config.gcp_service_account, '--quiet',
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

      # Configure Docker auth for each GAR region
      for region in self.config.gcp_regions:
        gar_host = f"{region}-docker.pkg.dev"

        proc = await asyncio.create_subprocess_exec(
          'gcloud', 'auth', 'configure-docker', gar_host, '--quiet',
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

        if proc.returncode == 0:
          self.logger.debug(f"Configured Docker auth for GAR region: {region}")

    except Exception as e:
      return ValidationResult(success=False, message=f"GAR auth error: {e}")

    return ValidationResult(success=True)

  async def _authenticate_acr(self) -> ValidationResult:
    """Authenticate to Azure Container Registry"""
    self.logger.debug("Authenticating to Azure ACR...")

    try:
      # Service principal login if credentials provided
      if all([self.config.azure_client_id, self.config.azure_client_secret, self.config.azure_tenant_id]):
        proc = await asyncio.create_subprocess_exec(
          'az', 'login', '--service-principal',
          '-u', self.config.azure_client_id,
          '-p', self.config.azure_client_secret,
          '--tenant', self.config.azure_tenant_id,
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

        if proc.returncode != 0:
          return ValidationResult(success=False, message="Azure service principal login failed")

    except Exception as e:
      return ValidationResult(success=False, message=f"ACR auth error: {e}")

    return ValidationResult(success=True)

  async def _authenticate_jfrog(self) -> ValidationResult:
    """Authenticate to JFrog Artifactory"""
    self.logger.debug("Authenticating to JFrog Artifactory...")

    try:
      if not all([self.config.jfrog_url, self.config.jfrog_user, self.config.jfrog_token]):
        return ValidationResult(success=False, message="Missing JFrog credentials")

      # Extract hostname from URL
      jfrog_host = self.config.jfrog_url.replace('https://', '').replace('http://', '').split('/')[0]

      proc = await asyncio.create_subprocess_exec(
        'crane', 'auth', 'login',
        '-u', self.config.jfrog_user,
        '-p', self.config.jfrog_token,
        jfrog_host,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
      )
      await proc.communicate()

      if proc.returncode != 0:
        return ValidationResult(success=False, message="JFrog authentication failed")

      self.logger.debug(f"Authenticated to JFrog: {jfrog_host}")

    except Exception as e:
      return ValidationResult(success=False, message=f"JFrog auth error: {e}")

    return ValidationResult(success=True)

  async def _authenticate_docr(self) -> ValidationResult:
    """Authenticate to DigitalOcean Container Registry"""
    self.logger.debug("Authenticating to DigitalOcean Container Registry...")

    try:
      if not self.config.docr_token:
        return ValidationResult(success=False, message="DOCR_TOKEN not set")

      # Login with crane
      proc = await asyncio.create_subprocess_exec(
        'crane', 'auth', 'login',
        '-u', 'unused',
        '-p', self.config.docr_token,
        'registry.digitalocean.com',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
      )
      await proc.communicate()

      if proc.returncode != 0:
        return ValidationResult(success=False, message="DOCR authentication failed")

      self.logger.debug("Authenticated to DigitalOcean Container Registry")

    except Exception as e:
      return ValidationResult(success=False, message=f"DOCR auth error: {e}")

    return ValidationResult(success=True)
