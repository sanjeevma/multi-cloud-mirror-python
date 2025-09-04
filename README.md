# Multi-Cloud Container Mirror

🚀 A Python tool for mirroring container images across multiple cloud registries simultaneously.

## Features

- **Multi-cloud support**: AWS ECR, Google GAR, Azure ACR, JFrog Artifactory, DigitalOcean CR
- **Parallel processing**: Configure concurrent image transfers
- **Retry logic**: Automatic retry with configurable attempts and delays
- **Platform targeting**: Support for multi-architecture images
- **Validation**: Pre-flight checks for tools, auth, and access
- **Colored logging**: Clear visual feedback during operations

## Quick Start

```bash
# Clone repository
git clone https://github.com/sanjeevma/multi-cloud-mirror-python
cd multi-cloud-mirror-python

# Install dependencies
pip install -r requirements.txt

# Setup configuration
cp examples/.env.example .env
# Edit .env with your credentials

# Validate setup
python main.py --validate

# Run mirroring
python main.py
```

## Installation

### Prerequisites

- Python 3.8+
- [crane](https://github.com/google/go-containerregistry/tree/main/cmd/crane) container tool
- Cloud CLI tools for your target registries

### Install crane

```bash
# Linux/macOS
VERSION=$(curl -s https://api.github.com/repos/google/go-containerregistry/releases/latest | grep '"tag_name"' | cut -d'"' -f4)
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m | sed 's/x86_64/amd64/')
curl -sL "https://github.com/google/go-containerregistry/releases/download/${VERSION}/go-containerregistry_${OS}_${ARCH}.tar.gz" | tar xz crane
sudo mv crane /usr/local/bin/
```

### Install cloud CLIs

```bash
# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Google Cloud CLI
curl https://sdk.cloud.google.com | bash

# Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# DigitalOcean CLI
wget https://github.com/digitalocean/doctl/releases/download/v1.100.0/doctl-1.100.0-linux-amd64.tar.gz
tar xf doctl-1.100.0-linux-amd64.tar.gz && sudo mv doctl /usr/local/bin/
```

## Configuration

### Environment Variables

Create `.env` file with your registry credentials:

```bash
# AWS ECR
ECR_MIRROR_AWS_REGIONS=us-east-1,eu-west-1
AWS_ACCOUNT_ID=123456789012

# Google GAR
GCR_GCP_REGIONS=us-central1,europe-west1
GCP_PROJECT_ID=my-gcp-project
GCP_SERVICE_ACCOUNT=mirror@my-project.iam.gserviceaccount.com

# Azure ACR
ACR_AZURE_REGIONS=eastus,westeurope
AZURE_RESOURCE_GROUP=my-resource-group
AZURE_ACR_NAME_PREFIX=myorg
AZURE_CLIENT_ID=client-id
AZURE_CLIENT_SECRET=client-secret
AZURE_TENANT_ID=tenant-id

# JFrog Artifactory
JFROG_URL=https://myorg.jfrog.io
JFROG_USER=username
JFROG_TOKEN=token
JFROG_REPOSITORY=docker-local

# DigitalOcean Container Registry
DOCR_REGIONS=nyc3,sfo3
DOCR_TOKEN=dop_v1_token
DOCR_REGISTRY_NAME=my-registry
```

### Image List Format

Create `config/example-list.txt`:

```
ECR,GAR     docker.io/library/nginx:1.21
ACR         docker.io/library/redis:7
JFROG,DOCR  ghcr.io/prometheus/prometheus:latest
ECR         quay.io/coreos/etcd:v3.5.0
```

Format: `DESTINATIONS SOURCE_IMAGE`
- Destinations: Comma-separated list (ECR, GAR, ACR, JFROG, DOCR)
- Source: Full image reference with registry, repo, and tag

## Usage

### Basic Commands

```bash
# Mirror with defaults
python main.py

# Custom image list and parallel jobs
python main.py -f custom-list.txt -j 5

# Validation only
python main.py --validate

# Debug mode with retries
python main.py -d -r 5

# Custom platform
python main.py -p linux/arm64
```

### Command Line Options

```
-f, --file FILE          Image list file (default: config/example-list.txt)
-j, --jobs N            Max parallel jobs (default: 3)
-r, --retries N         Max retries per image (default: 3)
-p, --platform PLATFORM Target platform (default: linux/amd64)
-d, --debug             Enable debug output
-v, --validate          Run validation only
-h, --help              Show help
```

## Authentication

### AWS ECR

```bash
aws configure
# OR
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

### Google GAR

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Azure ACR

```bash
az login
# OR service principal
az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID
```

### JFrog Artifactory

Set `JFROG_URL`, `JFROG_USER`, and `JFROG_TOKEN` in `.env`

### DigitalOcean CR

```bash
doctl auth init
# OR set DOCR_TOKEN in .env
```

## Examples

### Basic Mirroring

```bash
# Mirror to AWS ECR only
echo "ECR docker.io/library/nginx:latest" > my-images.txt
python main.py -f my-images.txt

# Mirror to multiple registries
echo "ECR,GAR,ACR docker.io/library/redis:6" > multi-registry.txt
python main.py -f multi-registry.txt
```

### Advanced Usage

```bash
# High-throughput mirroring
python main.py -j 10 -r 5 -d

# ARM64 images
python main.py -p linux/arm64

# Validate before mirroring
python main.py --validate && python main.py
```

## Troubleshooting

### Common Issues

**crane not found**
```bash
# Install crane tool
go install github.com/google/go-containerregistry/cmd/crane@latest
```

**Authentication failures**
```bash
# Test individual cloud CLI authentication
aws sts get-caller-identity
gcloud auth list
az account show
```

**Permission errors**
- ECR: Ensure `ecr:*` permissions
- GAR: Ensure `artifactregistry.repositories.*` roles
- ACR: Ensure `AcrPush` role

### Debug Mode

Enable debug logging to see detailed execution:

```bash
python main.py -d
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes with tests
4. Submit pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) file.

## Author

**Sanjeev Maharjan**
Email: me@sanjeev.au
GitHub: [@sanjeevma](https://github.com/sanjeevma)
