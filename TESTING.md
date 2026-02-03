# Testing Guide

## Overview

The UK Fuel Finder integration includes comprehensive test coverage with unit tests and integration tests.

## Test Structure

```
tests/
├── conftest.py                    # Pytest fixtures and configuration
├── test_config_flow.py           # Config flow tests (2 tests)
├── test_coordinator.py           # Data coordinator tests (3 tests)
├── test_init.py                  # Integration setup tests (2 tests)
├── test_sensor.py                # Sensor platform tests (4 tests)
└── test_integration_simple.py    # Real API tests (2 tests)
```

## Running Tests

### Install Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run All Unit Tests

```bash
PYTHONPATH=. pytest tests/ -v -k "not integration"
```

Expected output: **11 passed**

### Run Specific Test Files

```bash
PYTHONPATH=. pytest tests/test_config_flow.py -v
PYTHONPATH=. pytest tests/test_coordinator.py -v
PYTHONPATH=. pytest tests/test_sensor.py -v
PYTHONPATH=. pytest tests/test_init.py -v
```

### Run Integration Tests

Requires API credentials:

```bash
export FUEL_FINDER_CLIENT_ID="your_client_id"
export FUEL_FINDER_CLIENT_SECRET="your_client_secret"
PYTHONPATH=. pytest tests/test_integration_simple.py -v
```

Expected output: **2 passed** (or 2 skipped if credentials not set)

## Test Coverage

### Config Flow Tests (test_config_flow.py)
- User setup flow with valid credentials
- Form validation and error handling

### Coordinator Tests (test_coordinator.py)
- Successful data updates from API
- Authentication failure handling
- Network error handling and retries

### Init Tests (test_init.py)
- Integration setup and entry loading
- Integration unload and cleanup

### Sensor Tests (test_sensor.py)
- Sensor entity creation and setup
- State updates with fuel prices
- Attribute population (station details)
- Unavailable state when no data

### Integration Tests (test_integration_simple.py)
- Real API connectivity
- Station search by location
- Fuel price retrieval
- Data structure validation

## Test Configuration

Configuration is in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "enable_socket: marks tests that require network access",
]
```

## Mocking

Unit tests use mocks to isolate components:
- `unittest.mock.patch` for API client
- `pytest-homeassistant-custom-component` for Home Assistant fixtures
- Mock config entries and coordinators

Integration tests use real API calls (marked with `enable_socket`).

## Continuous Integration

Tests can be run in CI/CD pipelines:

```yaml
- name: Run tests
  run: |
    pip install -r requirements-dev.txt
    PYTHONPATH=. pytest tests/ -v -k "not integration"
```

## Troubleshooting

### ModuleNotFoundError: No module named 'custom_components'

Always use `PYTHONPATH=.` when running tests:
```bash
PYTHONPATH=. pytest tests/ -v
```

### Integration tests skipped

Set API credentials in environment:
```bash
export FUEL_FINDER_CLIENT_ID="..."
export FUEL_FINDER_CLIENT_SECRET="..."
```

### Async warnings

Tests use `asyncio_mode = "auto"` in `pyproject.toml` to handle async properly.
