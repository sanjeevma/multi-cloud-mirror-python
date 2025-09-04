# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial Python implementation
- Multi-cloud registry support
- Async parallel processing
- Retry logic with exponential backoff
- Colored logging output
- Comprehensive validation system

## [1.0.0] - 2025-09-04

### Added
- **Registry Support**
  - AWS Elastic Container Registry (ECR)
  - Google Cloud Artifact Registry (GAR)
  - Azure Container Registry (ACR)
  - JFrog Artifactory
  - DigitalOcean Container Registry (DOCR)

- **Core Features**
  - Parallel image mirroring with configurable concurrency
  - Automatic retry mechanism with configurable attempts and delays
  - Multi-platform image support (linux/amd64, linux/arm64, etc.)
  - Comprehensive pre-flight validation
  - Progress tracking and detailed logging

- **Configuration**
  - Environment variable configuration via .env files
  - Command-line argument overrides
  - Region-specific deployment support
  - Flexible authentication methods

- **CLI Interface**
  - Click-based command line interface
  - Debug mode for troubleshooting
  - Validation-only mode for testing setup
  - Customizable parallel job limits

- **Development Tools**
  - Type hints throughout codebase
  - Async/await pattern implementation
  - Abstract base classes for registry extensibility
  - Comprehensive error handling

- **Documentation**
  - Complete README with examples
  - Configuration templates
  - Docker Compose demo setup
  - Contributing guidelines

### Technical Details
- **Language**: Python 3.8+
- **Architecture**: Class-based async design
- **Dependencies**: click, python-dotenv, asyncio-throttle, aiofiles
- **External Tools**: crane (go-containerregistry)
- **Testing**: pytest with async support

### Migration from Bash Version
- Converted from bash scripts to Python classes
- Improved error handling and logging
- Better parallel processing with asyncio
- Enhanced configuration management
- Type safety with dataclasses

---

## Template for Future Releases

## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing functionality

### Deprecated
- Features that will be removed

### Removed
- Features that were removed

### Fixed
- Bug fixes

### Security
- Security improvements
