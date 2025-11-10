# Contributing to Django Missive

Thank you for your interest in contributing to Django Missive! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git

### Quick Start (All Operating Systems)

```bash
# Clone the repository
git clone https://github.com/yourusername/django-missive.git
cd django-missive

# Create virtual environment and install dependencies
python dev.py install-dev

# Optional: make it executable on Linux/macOS
chmod +x dev.py
```

## Dev Tool Commands Reference

All commands work the same way on **Linux, macOS, and Windows**:

```bash
python dev.py <command>
```

On Linux/macOS with executable permissions:
```bash
./dev.py <command>
```

### Development Commands

| Command | Description |
|---------|-------------|
| `venv` | Create virtual environment |
| `install` | Install in production mode |
| `install-dev` | Install in development mode |

### Testing Commands

| Command | Description |
|---------|-------------|
| `test` | Run all tests |
| `test-verbose` | Run tests with verbose output |
| `coverage` | Run tests with coverage report |

### Code Quality Commands

| Command | Description |
|---------|-------------|
| `lint` | Run flake8 and mypy |
| `format` | Format code with black and isort |
| `check` | Run all checks |

### Build Commands

| Command | Description |
|---------|-------------|
| `clean` | Remove all artifacts |
| `build` | Build wheel and source dist |

### Publishing Commands

| Command | Description |
|---------|-------------|
| `upload-test` | Upload to TestPyPI |
| `upload` | Upload to PyPI |
| `release` | Full release workflow |

### Utility Commands

| Command | Description |
|---------|-------------|
| `show-version` | Display current version |
| `venv-clean` | Remove and recreate venv |
| `help` | Show all commands |

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

Edit the code, add tests, and ensure everything works.

### 3. Format Your Code

```bash
python dev.py format
```

### 4. Run Tests

```bash
python dev.py test
```

### 5. Check Code Quality

```bash
python dev.py check
```

### 6. Commit Your Changes

```bash
git add .
git commit -m "Add: your feature description"
```

### 7. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Coding Standards

### Python Style Guide

- Follow PEP 8
- Use Black for code formatting (line length: 88)
- Use isort for import sorting
- Type hints are encouraged but not required

### Commit Message Format

Use conventional commits format:

```
<type>: <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat: add email notification support
fix: resolve migration conflict in models
docs: update installation instructions
```

## Testing Guidelines

### Writing Tests

- Place tests in the `tests/` directory
- Use pytest for testing
- Aim for high code coverage (>80%)
- Test both success and failure cases

### Test Structure

```python
import pytest
from missive.models import YourModel

@pytest.mark.django_db
class TestYourModel:
    def test_create_instance(self, user):
        """Test creating a model instance"""
        instance = YourModel.objects.create(
            user=user,
            field="value"
        )
        assert instance.id is not None
        assert instance.field == "value"
```

### Running Specific Tests

```bash
# Run a specific test file
pytest tests/test_models.py

# Run a specific test class
pytest tests/test_models.py::TestExampleModel

# Run a specific test method
pytest tests/test_models.py::TestExampleModel::test_create_example_model
```

## Building and Publishing

### Test Your Build Locally

```bash
# Build the package
python dev.py build

# Install locally to test
pip install dist/django_missive-0.1.0-py3-none-any.whl
```

### Publish to TestPyPI

```bash
python dev.py upload-test
```

### Publish to PyPI

```bash
python dev.py upload
```

## Project Structure

```
django-missive/
├── missive/                # Main package
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── forms.py
│   ├── utils.py
│   ├── migrations/
│   └── templates/
│       └── missive/
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_views.py
│   ├── settings.py
│   └── urls.py
├── pyproject.toml          # Project configuration
├── setup.cfg               # Tool configuration
├── pytest.ini              # Pytest configuration
├── dev.py                  # Development tool (cross-platform)
├── README.md              # User documentation
├── CONTRIBUTING.md        # This file
├── LICENSE                # License file
└── MANIFEST.in            # Distribution manifest
```

## Troubleshooting

### Virtual Environment Issues

If you have issues with the virtual environment:

```bash
# Recreate the virtual environment
python dev.py venv-clean
python dev.py install-dev
```

### Import Errors

Make sure you've installed the package in development mode:

```bash
python dev.py install-dev
```

### Test Failures

Clean test artifacts and try again:

```bash
python dev.py clean-test
python dev.py test
```

## Getting Help

- Check the [README.md](README.md) for general documentation
- Review [existing issues](https://github.com/yourusername/django-missive/issues)
- Create a new issue if you find a bug
- Join our community discussions

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Give constructive feedback
- Focus on what is best for the community

Thank you for contributing to Django Missive! 🎉

