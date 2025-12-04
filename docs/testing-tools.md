# Testing Tools Guide

This document describes the testing tools available in the django-missive project and how to use them.

## Core Testing Framework

### pytest
The main testing framework. Run tests with:
```bash
python dev.py test
# or
pytest
```

### pytest-django
Django integration for pytest. Automatically configured via `pytest.ini`.

### pytest-cov
Coverage reporting. Already configured in `pytest.ini`:
```bash
pytest --cov=missive --cov-report=html
```

## Test Execution Tools

### pytest-xdist - Parallel Execution
Run tests in parallel to speed up execution:
```bash
# Use all available CPU cores
pytest -n auto

# Use specific number of workers
pytest -n 4

# Combine with coverage (requires pytest-cov>=2.6)
pytest -n auto --cov=missive
```

**Benefits:**
- Significantly faster test execution on multi-core systems
- Detects test isolation issues (shared state between tests)

### pytest-timeout - Detect Hanging Tests
Automatically fail tests that take too long:
```bash
# Set timeout for all tests (default: 300 seconds)
pytest --timeout=60

# Set timeout per test
pytest --timeout=10
```

**Configuration in `pytest.ini`:**
```ini
[pytest]
timeout = 60
timeout_method = thread
```

### pytest-randomly - Random Test Order
Run tests in random order to detect test dependencies:
```bash
pytest --randomly
```

**Benefits:**
- Detects hidden dependencies between tests
- Ensures tests are truly isolated
- Can be configured to use a seed for reproducibility

### pytest-repeat - Find Flaky Tests
Repeat tests multiple times to find intermittent failures:
```bash
# Repeat each test 3 times
pytest --count=3

# Repeat only failed tests
pytest --count=3 --repeat-scope=function
```

## Test Output & Reporting

### pytest-sugar - Better Output
Improves test output with colors and progress indicators. Automatically enabled when installed.

**Features:**
- Colored output
- Progress indicators
- Better failure summaries

### pytest-html - HTML Reports
Generate HTML test reports:
```bash
pytest --html=report.html --self-contained-html
```

**Benefits:**
- Visual test results
- Easy to share with team
- Includes coverage information

## Mocking & Test Data

### pytest-mock - Better Mocking
Simpler mocking API than `unittest.mock`:
```python
def test_something(mocker):
    # mocker is automatically available
    mock_send = mocker.patch('djmissive.helpers.send_missive')
    mock_send.return_value = True
    
    result = my_function()
    assert result is True
    mock_send.assert_called_once()
```

**Benefits:**
- Cleaner API
- Automatic cleanup
- Better integration with pytest fixtures

### factory-boy - Django Model Factories
Generate test data for Django models:
```python
# In tests/factories.py
import factory
from missive.models import Recipient, Missive

class RecipientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Recipient
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Faker('name')

# In tests
def test_missive_creation():
    recipient = RecipientFactory()
    missive = MissiveFactory(recipient=recipient)
    assert missive.recipient == recipient
```

**Benefits:**
- Reusable test data factories
- Automatic handling of ForeignKey relationships
- Supports sequences and Faker integration

### faker - Realistic Fake Data
Generate realistic fake data:
```python
from faker import Faker

fake = Faker()

# Generate fake data
email = fake.email()
name = fake.name()
phone = fake.phone_number()
address = fake.address()
```

**Integration with factory-boy:**
```python
class RecipientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Recipient
    
    email = factory.Faker('email')
    name = factory.Faker('name')
    phone = factory.Faker('phone_number')
```

### hypothesis - Property-Based Testing
Generate test cases automatically:
```python
from hypothesis import given, strategies as st

@given(
    email=st.emails(),
    name=st.text(min_size=1, max_size=100)
)
def test_recipient_validation(email, name):
    recipient = Recipient(email=email, name=name)
    recipient.full_clean()  # Django validation
```

**Benefits:**
- Tests many edge cases automatically
- Finds bugs that manual tests miss
- Shrinks failing examples to minimal cases

## Usage Examples

### Run tests in parallel with coverage
```bash
pytest -n auto --cov=missive --cov-report=html
```

### Find flaky tests
```bash
# Run tests 5 times in random order
pytest --count=5 --randomly
```

### Generate HTML report
```bash
pytest --html=test_report.html --self-contained-html
```

### Run with timeout
```bash
pytest --timeout=30
```

## Configuration

All tools can be configured in `pytest.ini`:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = tests.settings
python_files = tests.py test_*.py *_tests.py
addopts = 
    --verbose
    --strict-markers
    --tb=short
    --cov=missive
    --cov-report=term-missing
    --cov-report=html
    --randomly  # Enable random test order
    --timeout=60  # Set default timeout
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
```

## Best Practices

1. **Use factory-boy for model creation** - More maintainable than manual object creation
2. **Run tests randomly in CI** - Catches test dependencies early
3. **Use parallel execution** - Speeds up test suite significantly
4. **Set timeouts** - Prevents hanging tests from blocking CI
5. **Use hypothesis for complex logic** - Finds edge cases automatically
6. **Generate HTML reports** - Easy to share test results with team

## Installation

All tools are included in the `dev` dependencies:

```bash
pip install -e ".[dev]"
# or
pip install -r requirements-dev.txt
```

