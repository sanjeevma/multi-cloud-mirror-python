#!/usr/bin/env python3
# scripts/setup.py
# Author: Sanjeev Maharjan <me@sanjeev.au>

import asyncio
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path


class CloudMirrorSetup:
  def __init__(self):
    self.system = platform.system().lower()
    self.arch = self._get_arch()
    self.script_dir = Path(__file__).parent.parent

  def _get_arch(self) -> str:
    """Get normalized architecture"""
    arch = platform.machine().lower()
    if arch in ('x86_64', 'amd64'):
      return 'amd64'
    elif arch in ('aarch64', 'arm64'):
      return 'arm64'
    return arch

  def _check_permissions(self):
    """Check if running with appropriate permissions"""
    if os.geteuid() == 0:
      print("⚠️  Warning: Running as root. Consider using a non-root user.")

  def _run_command(self, cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run shell command"""
    try:
      return subprocess.run(cmd, check=check, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
      print(f"❌ Command failed: {' '.join(cmd)}")
      print(f"   Error: {e.stderr}")
      if check:
        sys.exit(1)
      return e

  def _download_file(self, url: str, target_path: Path):
    """Download file from URL"""
    print(f"Downloading {url}...")
    urllib.request.urlretrieve(url, target_path)

  def install_crane(self):
    """Install crane tool"""
    if shutil.which('crane'):
      print("Crane already installed")
      return

    print("Installing crane...")

    # Get latest version
    result = self._run_command([
      'curl', '-s',
      'https://api.github.com/repos/google/go-containerregistry/releases/latest'
    ])

    import json
    release_data = json.loads(result.stdout)
    version = release_data['tag_name']

    # Download and install
    with tempfile.TemporaryDirectory() as temp_dir:
      temp_path = Path(temp_dir)
      archive_name = f"go-containerregistry_{self.system}_{self.arch}.tar.gz"
      download_url = f"https://github.com/google/go-containerregistry/releases/download/{version}/{archive_name}"

      archive_path = temp_path / archive_name
      self._download_file(download_url, archive_path)

      # Extract
      self._run_command(['tar', 'xzf', str(archive_path), '-C', str(temp_path)])

      # Install to /usr/local/bin
      crane_path = temp_path / 'crane'
      if crane_path.exists():
        self._run_command(['sudo', 'mv', str(crane_path), '/usr/local/bin/crane'])
        self._run_command(['sudo', 'chmod', '+x', '/usr/local/bin/crane'])
        print("Crane installed")
      else:
        print("Failed to find crane binary in archive")
        sys.exit(1)

  def install_aws_cli(self):
    """Install AWS CLI"""
    if shutil.which('aws'):
      print("✅ AWS CLI already installed")
      return

    print("📦 Installing AWS CLI...")

    with tempfile.TemporaryDirectory() as temp_dir:
      temp_path = Path(temp_dir)

      if self.system == 'linux':
        zip_path = temp_path / 'awscliv2.zip'
        self._download_file(
          'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip',
          zip_path
        )

        self._run_command(['unzip', str(zip_path), '-d', str(temp_path)])
        self._run_command(['sudo', str(temp_path / 'aws' / 'install')])
        print("✅ AWS CLI installed")

      elif self.system == 'darwin':
        pkg_path = temp_path / 'AWSCLIV2.pkg'
        self._download_file(
          'https://awscli.amazonaws.com/AWSCLIV2.pkg',
          pkg_path
        )

        self._run_command(['sudo', 'installer', '-pkg', str(pkg_path), '-target', '/'])
        print("✅ AWS CLI installed")

  def install_gcloud_cli(self):
    """Install Google Cloud CLI"""
    if shutil.which('gcloud'):
      print("✅ Google Cloud CLI already installed")
      return

    print("📦 Installing Google Cloud CLI...")

    if self.system == 'linux':
      # Add repository
      self._run_command([
        'sudo', 'apt-get', 'update'
      ], check=False)

      self._run_command([
        'curl', 'https://packages.cloud.google.com/apt/doc/apt-key.gpg',
        '|', 'sudo', 'apt-key', 'add', '-'
      ], check=False)

      # Install
      install_script = 'curl https://sdk.cloud.google.com | bash'
      self._run_command(['bash', '-c', install_script])
      print("✅ Google Cloud CLI installed")

  def install_azure_cli(self):
    """Install Azure CLI"""
    if shutil.which('az'):
      print("✅ Azure CLI already installed")
      return

    print("📦 Installing Azure CLI...")

    if self.system == 'linux':
      install_script = 'curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash'
      self._run_command(['bash', '-c', install_script])
      print("✅ Azure CLI installed")

  def install_doctl(self):
    """Install DigitalOcean CLI"""
    if shutil.which('doctl'):
      print("✅ DigitalOcean CLI already installed")
      return

    print("📦 Installing DigitalOcean CLI...")

    # Get latest version
    result = self._run_command([
      'curl', '-s',
      'https://api.github.com/repos/digitalocean/doctl/releases/latest'
    ])

    import json
    release_data = json.loads(result.stdout)
    version = release_data['tag_name']

    with tempfile.TemporaryDirectory() as temp_dir:
      temp_path = Path(temp_dir)
      archive_name = f"doctl-{version.lstrip('v')}-{self.system}-{self.arch}.tar.gz"
      download_url = f"https://github.com/digitalocean/doctl/releases/download/{version}/{archive_name}"

      archive_path = temp_path / archive_name
      self._download_file(download_url, archive_path)

      self._run_command(['tar', 'xzf', str(archive_path), '-C', str(temp_path)])

      doctl_path = temp_path / 'doctl'
      if doctl_path.exists():
        self._run_command(['sudo', 'mv', str(doctl_path), '/usr/local/bin/doctl'])
        self._run_command(['sudo', 'chmod', '+x', '/usr/local/bin/doctl'])
        print("✅ DigitalOcean CLI installed")

  def setup_config(self):
    """Setup configuration files"""
    print("🔧 Setting up configuration...")

    env_file = self.script_dir / '.env'
    env_example = self.script_dir / 'examples' / '.env.example'

    if not env_file.exists() and env_example.exists():
      shutil.copy(env_example, env_file)
      print("✅ Created .env file from template")
      print("⚠️  Please edit .env with your actual credentials")
    else:
      print("✅ .env file already exists")

  def install_python_deps(self):
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")

    requirements_file = self.script_dir / 'requirements.txt'
    if requirements_file.exists():
      self._run_command([
        sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
      ])
      print("✅ Python dependencies installed")

  def run_setup(self):
    """Run complete setup"""
    print("🚀 Multi-Cloud Mirror Setup")
    print("============================")

    self._check_permissions()
    self.install_python_deps()
    self.install_crane()
    self.install_aws_cli()
    self.install_gcloud_cli()
    self.install_azure_cli()
    self.install_doctl()
    self.setup_config()

    print("")
    print("✅ Setup complete!")
    print("Next steps:")
    print("1. Edit .env with your credentials")
    print("2. Run 'python main.py --validate' to test connections")
    print("3. Update examples/example-list.txt with your images")
    print("4. Run 'python main.py' to start mirroring")


def main():
  setup = CloudMirrorSetup()
  setup.run_setup()


if __name__ == '__main__':
  main()
