# tests/test_mirror.py
# Author: Sanjeev Maharjan <me@sanjeev.au>

import pytest
from unittest.mock import AsyncMock, Mock, patch, mock_open
from pathlib import Path
import tempfile

from core.mirror import ContainerMirror
from core.config import Config
from utils.logger import Logger
from utils.types import ValidationResult, MirrorResult


@pytest.fixture
def mock_config():
  return Config(
    image_list_file='test-list.txt',
    max_parallel_jobs=2,
    max_retries=2,
    retry_delay=1,
    target_platform='linux/amd64',
    debug=True,
    ecr_regions=['us-east-1'],
    aws_account_id='123456789012',
    gcp_regions=None,
    gcp_project_id=None,
    gcp_service_account=None,
    azure_regions=None,
    azure_resource_group=None,
    azure_acr_name=None,
    azure_acr_name_prefix=None,
    azure_client_id=None,
    azure_client_secret=None,
    azure_tenant_id=None,
    jfrog_url=None,
    jfrog_user=None,
    jfrog_token=None,
    jfrog_repository=None,
    docr_regions=None,
    docr_token=None,
    docr_registry_name=None
  )


@pytest.fixture
def mock_logger():
  return Mock(spec=Logger)


@pytest.fixture
def container_mirror(mock_config, mock_logger):
  return ContainerMirror(mock_config, mock_logger)


class TestContainerMirror:

  @pytest.mark.asyncio
  async def test_validate_setup_success(self, container_mirror):
    with patch('asyncio.create_subprocess_exec') as mock_subprocess, \
         patch('pathlib.Path.exists', return_value=True):

      mock_proc = AsyncMock()
      mock_proc.returncode = 0
      mock_proc.communicate.return_value = (b'crane version', b'')
      mock_subprocess.return_value = mock_proc

      container_mirror.authenticator.authenticate_all = AsyncMock(
        return_value=ValidationResult(success=True)
      )

      result = await container_mirror.validate_setup()
      assert result.success is True

  @pytest.mark.asyncio
  async def test_validate_setup_crane_missing(self, container_mirror):
    with patch('asyncio.create_subprocess_exec', side_effect=FileNotFoundError):
      result = await container_mirror.validate_setup()
      assert result.success is False
      assert 'crane tool not installed' in result.message

  @pytest.mark.asyncio
  async def test_validate_setup_file_missing(self, container_mirror):
    with patch('asyncio.create_subprocess_exec') as mock_subprocess, \
         patch('pathlib.Path.exists', return_value=False):

      mock_proc = AsyncMock()
      mock_proc.returncode = 0
      mock_subprocess.return_value = mock_proc

      result = await container_mirror.validate_setup()
      assert result.success is False
      assert 'Image list file not found' in result.message

  def test_load_image_list_valid(self, container_mirror):
    test_content = """# Test images
ECR docker.io/library/nginx:latest
GAR,ACR docker.io/library/redis:6
# Comment line
JFROG quay.io/prometheus/prometheus:v2.40.0

-- Section separator --
DOCR ghcr.io/grafana/grafana:9.0.0
"""

    with patch('builtins.open', mock_open(read_data=test_content)):
      images = container_mirror._load_image_list()

      assert len(images) == 4
      assert images[0]['destinations'] == ['ECR']
      assert images[0]['source'] == 'docker.io/library/nginx:latest'
      assert images[1]['destinations'] == ['GAR', 'ACR']
      assert images[1]['source'] == 'docker.io/library/redis:6'

  def test_load_image_list_invalid_format(self, container_mirror, mock_logger):
    test_content = """ECR
GAR invalid-format
INVALID docker.io/nginx:latest
"""

    with patch('builtins.open', mock_open(read_data=test_content)):
      images = container_mirror._load_image_list()

      assert len(images) == 0
      assert mock_logger.warning.call_count >= 2

  def test_load_image_list_invalid_destination(self, container_mirror, mock_logger):
    test_content = """UNKNOWN docker.io/nginx:latest"""

    with patch('builtins.open', mock_open(read_data=test_content)):
      images = container_mirror._load_image_list()

      assert len(images) == 0
      mock_logger.warning.assert_called()

  @pytest.mark.asyncio
  async def test_run_success(self, container_mirror):
    test_content = """ECR docker.io/library/nginx:latest"""

    with patch('builtins.open', mock_open(read_data=test_content)):
      container_mirror.authenticator.authenticate_all = AsyncMock(
        return_value=ValidationResult(success=True)
      )

      container_mirror.processor.process_images = AsyncMock(
        return_value=MirrorResult(
          total_images=1,
          successful_images=1,
          failed_images=0
        )
      )

      result = await container_mirror.run()

      assert result.total_images == 1
      assert result.successful_images == 1
      assert result.failed_images == 0

  @pytest.mark.asyncio
  async def test_run_auth_failure(self, container_mirror):
    container_mirror.authenticator.authenticate_all = AsyncMock(
      return_value=ValidationResult(success=False, message="Auth failed")
    )

    with pytest.raises(RuntimeError, match="Authentication failed"):
      await container_mirror.run()

  def test_initialize_registries_ecr_only(self, mock_config, mock_logger):
    mock_config.ecr_regions = ['us-east-1']
    mock_config.gcp_regions = None

    mirror = ContainerMirror(mock_config, mock_logger)

    assert 'ECR' in mirror.registries
    assert 'GAR' not in mirror.registries
    assert len(mirror.registries) == 1

  def test_initialize_registries_multiple(self, mock_config, mock_logger):
    mock_config.ecr_regions = ['us-east-1']
    mock_config.gcp_regions = ['us-central1']
    mock_config.gcp_project_id = 'test-project'
    mock_config.jfrog_url = 'https://test.jfrog.io'

    mirror = ContainerMirror(mock_config, mock_logger)

    assert 'ECR' in mirror.registries
    assert 'GAR' in mirror.registries
    assert 'JFROG' in mirror.registries
    assert len(mirror.registries) == 3
