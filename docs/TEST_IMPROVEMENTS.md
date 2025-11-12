# Test Infrastructure Improvements

This document outlines the test infrastructure improvements implemented for QuantChain to address test coverage, dependency management, and resource monitoring requirements.

## Overview

The following improvements have been implemented:

1. **Minimal test requirements**: Created a lightweight requirements file for fast unit testing
2. **Docker containers for testing**: Set up dedicated Docker containers for consistent test environments
3. **Separated ML tests**: Moved heavy ML tests to a separate workflow job to optimize CI resources
4. **Resource monitoring**: Added disk and memory usage logging for monitoring and optimization

## 1. Minimal Test Requirements

### File: `requirements-test.txt`

This file contains only essential packages required for running unit tests without ML dependencies:

```bash
# Core testing framework
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
pytest-timeout>=2.1.0

# Essential project dependencies for testing
PyYAML>=6.0.0
numpy>=1.21.0
pandas>=1.3.0
python-dotenv>=1.0.0

# Resource monitoring
psutil>=5.9.0

# Type checking
types-requests
types-PyYAML

# Code quality tools (minimal)
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0

# Mock dependencies
requests-mock>=1.10.0
```

### Usage:

For fast unit testing without ML dependencies:

```bash
pip install -r requirements-test.txt
pip install -e .
pytest tests/unit -v -m "not requires_ml and not slow"
```

## 2. Docker Containers for Testing

### File: `docker-compose.test.yml`

Docker configuration for running tests in isolated environments:

```yaml
version: '3.8'

services:
  quantchain-test:
    build: 
      context: .
      dockerfile: Dockerfile
    image: anchapin/quantchain:test
    container_name: quantchain-test
    volumes:
      - .:/app
      - test_cache:/root/.cache
      - test_pip:/root/.local/pip
    environment:
      - PYTHONPATH=/app
      - PYTHONDONTWRITEBYTECODE=1
      - TEST_MODE=1
      - COVERAGE_THRESHOLD=80
      - TESTING=true
      - DATABASE_URL=sqlite:///:memory:
    command: bash -c "
      pip install -r requirements-test.txt &&
      pytest tests/unit -v --cov=quantchain --cov-fail-under=80 --cov-report=term-missing"
    restart: "no"
    mem_limit: 2g
    cpus: 2

  quantchain-ml-test:
    # ... (see full file for details)
    profiles: ["ml"]
```

### Usage:

Run lightweight unit tests:

```bash
docker-compose -f docker-compose.test.yml up
```

Run ML tests (using profile):

```bash
docker-compose -f docker-compose.test.yml --profile ml up
```

## 3. Separated ML Tests

### CI/CD Improvements

The GitHub Actions workflow has been restructured to separate ML tests into a dedicated job:

- **unit-tests**: Runs on Python 3.9-3.12 with minimal dependencies
- **ml-tests**: Runs only on Python 3.13 with full ML dependencies
- **integration-tests**: Runs integration tests with appropriate dependencies

### Test Markers

New test markers have been added to categorize tests:

```python
@pytest.mark.requires_ml  # Tests requiring ML dependencies
@pytest.mark.slow        # Slow-running tests
@pytest.mark.unit        # Unit tests
@pytest.mark.integration # Integration tests
```

### Running Tests Locally:

```bash
# Run only non-ML unit tests
pytest tests/unit -v -m "not requires_ml and not slow"

# Run only ML tests
pytest tests/unit -v -m "requires_ml or slow"

# Run all tests
pytest tests/unit -v
```

## 4. Resource Monitoring

### Monitoring Scripts

Two scripts have been added for resource monitoring:

#### `scripts/monitor_resources.py`

Standalone script to monitor system resources:

```bash
# One-time monitoring
python scripts/monitor_resources.py

# Continuous monitoring (every 30 seconds)
python scripts/monitor_resources.py --interval 30

# Custom output file
python scripts/monitor_resources.py --output custom_logs.jsonl
```

#### `scripts/run_tests_with_monitoring.py`

Test runner with integrated resource monitoring:

```bash
# Run unit tests with monitoring
python scripts/run_tests_with_monitoring.py --type unit --coverage

# Run ML tests with monitoring
python scripts/run_tests_with_monitoring.py --type ml --coverage

# Run integration tests with monitoring
python scripts/run_tests_with_monitoring.py --type integration --coverage
```

### Automatic Monitoring in CI/CD

Resource monitoring is automatically enabled in CI environments:
- Logs are created before and after dependency installation
- Logs are created before and after test execution
- All logs are saved to `logs/` directory

### Pytest Integration

Updated `conftest.py` to include automatic resource logging:
- Logs resources at session start and end
- Logs resources after each test (in CI or when monitoring is enabled)
- Requires `psutil` package (included in `requirements-test.txt`)

### Viewing Resource Logs

Resource logs are saved in JSON lines format:
```bash
# View latest resource log
tail -n 1 logs/test_resources.jsonl | jq

# Monitor resource usage during a test run
tail -f logs/test_resources.jsonl | jq '.'
```

## Benefits

1. **Faster CI Pipeline**: By separating ML tests and using minimal dependencies for most test jobs
2. **Resource Optimization**: Better resource utilization in CI with separate jobs for different test types
3. **Consistent Testing Environments**: Docker containers ensure consistent testing across different machines
4. **Resource Visibility**: Monitoring helps identify resource-intensive tests and optimize test performance
5. **Scalability**: The modular approach allows easy addition of new test categories

## Future Improvements

1. **Parallel Test Execution**: Further optimize by running test categories in parallel
2. **Test Sharding**: Split large test suites into smaller chunks for faster execution
3. **Smart Caching**: Implement more sophisticated dependency caching strategies
4. **Resource Thresholds**: Add warnings and failures for tests exceeding resource limits
