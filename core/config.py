# core/config.py
# Author: Sanjeev Maharjan <me@sanjeev.au>

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
from dotenv import load_dotenv


@dataclass
class Config:
  # Core settings
  image_list_file: str
  max_parallel_jobs: int
  max_retries: int
  retry_delay: int
  target_platform: str
  debug: bool

  # AWS ECR
  ecr_regions: Optional[List[str]]
  aws_account_id: Optional[str]

  # Google GAR
  gcp_regions: Optional[List[str]]
  gcp_project_id: Optional[str]
  gcp_service_account: Optional[str]

  # Azure ACR
  azure_regions: Optional[List[str]]
  azure_resource_group: Optional[str]
  azure_acr_name: Optional[str]
  azure_acr_name_prefix: Optional[str]
  azure_client_id: Optional[str]
  azure_client_secret: Optional[str]
  azure_tenant_id: Optional[str]

  # JFrog
  jfrog_url: Optional[str]
  jfrog_user: Optional[str]
  jfrog_token: Optional[str]
  jfrog_repository: Optional[str]

  # DigitalOcean
  docr_regions: Optional[List[str]]
  docr_token: Optional[str]
  docr_registry_name: Optional[str]


class ConfigManager:
  def __init__(self, image_list_file: str, max_parallel_jobs: int,
               max_retries: int, target_platform: str, debug: bool):
    self.image_list_file = image_list_file
    self.max_parallel_jobs = max_parallel_jobs
    self.max_retries = max_retries
    self.target_platform = target_platform
    self.debug = debug

    # Load environment variables
    self._load_env()

  def _load_env(self):
    """Load environment variables from .env file"""
    script_dir = Path(__file__).parent.parent
    env_file = script_dir / '.env'

    if env_file.exists():
      load_dotenv(env_file)

    # Also check for regions.conf
    regions_conf = script_dir / 'config' / 'regions.conf'
    if regions_conf.exists():
      self._load_regions_conf(regions_conf)

  def _load_regions_conf(self, config_file: Path):
    """Load additional config from regions.conf"""
    with open(config_file, 'r') as f:
      for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
          if '=' in line:
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip().strip('"\'')

  def _parse_regions(self, env_var: str) -> Optional[List[str]]:
    """Parse comma-separated regions from environment variable"""
    value = os.getenv(env_var)
    if value:
      return [region.strip() for region in value.split(',')]
    return None

  def load_config(self) -> Config:
    """Load and validate configuration"""
    return Config(
      # Core settings
      image_list_file=self.image_list_file,
      max_parallel_jobs=self.max_parallel_jobs,
      max_retries=self.max_retries,
      retry_delay=int(os.getenv('RETRY_DELAY', '5')),
      target_platform=self.target_platform,
      debug=self.debug,

      # AWS ECR
      ecr_regions=self._parse_regions('ECR_MIRROR_AWS_REGIONS'),
      aws_account_id=os.getenv('AWS_ACCOUNT_ID'),

      # Google GAR
      gcp_regions=self._parse_regions('GCR_GCP_REGIONS'),
      gcp_project_id=os.getenv('GCP_PROJECT_ID'),
      gcp_service_account=os.getenv('GCP_SERVICE_ACCOUNT'),

      # Azure ACR
      azure_regions=self._parse_regions('ACR_AZURE_REGIONS'),
      azure_resource_group=os.getenv('AZURE_RESOURCE_GROUP'),
      azure_acr_name=os.getenv('AZURE_ACR_NAME'),
      azure_acr_name_prefix=os.getenv('AZURE_ACR_NAME_PREFIX'),
      azure_client_id=os.getenv('AZURE_CLIENT_ID'),
      azure_client_secret=os.getenv('AZURE_CLIENT_SECRET'),
      azure_tenant_id=os.getenv('AZURE_TENANT_ID'),

      # JFrog
      jfrog_url=os.getenv('JFROG_URL'),
      jfrog_user=os.getenv('JFROG_USER'),
      jfrog_token=os.getenv('JFROG_TOKEN'),
      jfrog_repository=os.getenv('JFROG_REPOSITORY'),

      # DigitalOcean
      docr_regions=self._parse_regions('DOCR_REGIONS'),
      docr_token=os.getenv('DOCR_TOKEN'),
      docr_registry_name=os.getenv('DOCR_REGISTRY_NAME')
    )
