# Contributing to Multi-Cloud Mirror

Thank you for considering contributing to Multi-Cloud Mirror! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.8+
- crane tool
- Cloud CLI tools (AWS, GCP, Azure, etc.)
- Git

### Local Setup

```bash
# Clone repository
git clone https://github.com/sanjeevma/multi-cloud-mirror-python.git
cd multi-cloud-mirror-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -e .[dev]

# Copy example environment
cp examples/.env.example .env
# Edit .env with test credentials
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test
pytest tests/test_mirror.py -v

# Run async tests
pytest tests/test_processor.py::TestImageProcessor::test_parallel_processing -v
```

## Code Style

### Python Standards

- Follow PEP 8
- Use 2-space indentation (project preference)
- Maximum line length: 100 characters
- Use type hints for all functions
- Use async/await for I/O operations

### Formatting

```bash
# Auto-format code
make format

# Check formatting
make lint

# Type checking
make typecheck
```

### Example Code Style

```python
async def push_image(self, source: str) -> bool:
  """Push image to registry with proper error handling"""
  repo, tag = self._parse_image(source)

  try:
    success, stdout, stderr = await self._run_crane_command(
      'copy', source, target, '--platform', self.config.target_platform
    )

    if success:
      self.logger.success(f"Mirrored: {source}")
      return True

  except Exception as e:
    self.logger.error(f"Failed to mirror {source}: {e}")

  return False
```

## Adding New Registries

### Step 1: Create Registry Class

Create `registries/newregistry.py`:

```python
from registries.base import BaseRegistry

class NewRegistry(BaseRegistry):
  async def push_image(self, source: str) -> bool:
    # Implementation here
    pass

  async def validate_access(self) -> ValidationResult:
    # Validation here
    pass
```

### Step 2: Add Configuration

Update `core/config.py`:

```python
@dataclass
class Config:
  # ... existing fields ...
  newregistry_url: Optional[str]
  newregistry_token: Optional[str]
```

### Step 3: Update Main Mirror

Add to `core/mirror.py`:

```python
from registries.newregistry import NewRegistry

def _initialize_registries(self):
  # ... existing registries ...
  if self.config.newregistry_url:
    registries['NEWREGISTRY'] = NewRegistry(self.config, self.logger)
```

### Step 4: Add Tests

Create `tests/test_newregistry.py` with comprehensive test coverage.

## Testing Guidelines

### Test Structure

```python
import pytest
from unittest.mock import AsyncMock, patch

class TestNewRegistry:
  @pytest.fixture
  def registry(self, mock_config, mock_logger):
    return NewRegistry(mock_config, mock_logger)

  @pytest.mark.asyncio
  async def test_push_image_success(self, registry):
    # Test implementation
    pass

  @pytest.mark.asyncio
  async def test_push_image_failure(self, registry):
    # Test failure scenarios
    pass
```

### Test Categories

- **Unit tests**: Individual class/function testing
- **Integration tests**: Multi-component interactions
- **E2E tests**: Full workflow testing (optional)

### Mocking External Dependencies

Mock all external calls (crane, cloud CLIs):

```python
@patch('registries.base.BaseRegistry._run_crane_command')
async def test_push_image(self, mock_crane, registry):
  mock_crane.return_value = (True, '', '')
  result = await registry.push_image('nginx:latest')
  assert result is True
```

## Pull Request Process

### Before Submitting

1. Create feature branch: `git checkout -b feature/new-registry`
2. Write tests for new functionality
3. Ensure all tests pass: `make test`
4. Format code: `make format`
5. Update documentation if needed
6. Update CHANGELOG.md

### PR Guidelines

- **Title**: Clear, descriptive summary
- **Description**: Explain what and why
- **Testing**: Describe test coverage
- **Breaking changes**: Highlight any breaking changes

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests added for new functionality
- [ ] Documentation updated
```

## Release Process

### Version Numbering

Follow semantic versioning (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Release Steps

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release PR
4. Tag release: `git tag v1.2.3`
5. Push tags: `git push origin --tags`
6. GitHub Actions handles PyPI publishing

## Issue Guidelines

### Bug Reports

Include:
- Python version
- Operating system
- Cloud providers used
- Full error traceback
- Steps to reproduce

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Additional context

## Code Review Standards

### Reviewers Look For

- **Correctness**: Logic errors, edge cases
- **Performance**: Async usage, resource efficiency
- **Security**: Credential handling, input validation
- **Maintainability**: Code clarity, documentation
- **Testing**: Adequate test coverage

### Review Checklist

- [ ] Code follows project conventions
- [ ] Tests cover new functionality
- [ ] Documentation updated
- [ ] No hardcoded credentials
- [ ] Error handling implemented
- [ ] Async patterns used correctly

## Getting Help

- **Questions**: Open GitHub Discussion
- **Bugs**: Create GitHub Issue
- **Security**: Email me@sanjeev.au privately
- **Chat**: Join project Discord (if available)

## Recognition

Contributors will be:
- Added to README.md contributors section
- Mentioned in CHANGELOG.md
- Credited in release notes

Thank you for contributing! 🚀
