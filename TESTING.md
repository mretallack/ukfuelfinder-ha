# Testing Guide

## Overview

The UK Fuel Finder integration includes comprehensive test coverage with unit tests, integration tests, and real API testing.

## Test Structure

```
tests/
├── conftest.py                    # Pytest fixtures and configuration
├── test_config_flow.py           # Config flow tests (2 tests)
├── test_coordinator.py           # Data coordinator tests (3 tests)
├── test_coordinator_metadata.py  # Coordinator metadata tests (6 tests)
├── test_cheapest_sensor.py       # Cheapest sensor tests (7 tests)
├── test_init.py                  # Integration setup tests (2 tests)
├── test_sensor.py                # Sensor platform tests (8 tests)
├── test_stale_devices.py         # Stale device removal tests (2 tests)
├── test_integration_simple.py    # Real API tests (2 tests, skipped in CI)
└── test_api_integration.py       # Standalone API integration test
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

Expected output: **30 passed, 2 deselected**

### Run Specific Test Files

```bash
PYTHONPATH=. pytest tests/test_config_flow.py -v
PYTHONPATH=. pytest tests/test_coordinator.py -v
PYTHONPATH=. pytest tests/test_coordinator_metadata.py -v
PYTHONPATH=. pytest tests/test_cheapest_sensor.py -v
PYTHONPATH=. pytest tests/test_sensor.py -v
PYTHONPATH=. pytest tests/test_init.py -v
PYTHONPATH=. pytest tests/test_stale_devices.py -v
```

### Run Integration Tests (Pytest)

Requires API credentials. These tests are blocked by pytest-socket in normal runs:

```bash
export FUEL_FINDER_CLIENT_ID="your_client_id"
export FUEL_FINDER_CLIENT_SECRET="your_client_secret"
PYTHONPATH=. pytest tests/test_integration_simple.py -v -p no:socket
```

Expected output: **2 passed** (or 2 skipped if credentials not set)

### Run Standalone API Integration Test

For real API testing without pytest-socket blocking:

```bash
# Credentials loaded from .env file automatically
python3.12 tests/test_api_integration.py
```

This test:
- Searches for stations by location
- Retrieves fuel prices with timestamps
- Checks for specific stations (e.g., Wool Bovington)
- Shows price age and identifies stale prices
- Tests all metadata fields

**Note:** Requires `.env` file with credentials (see Setup section below).

## Test Coverage

### Config Flow Tests (test_config_flow.py)
- User setup flow with valid credentials
- Form validation and error handling

### Coordinator Tests (test_coordinator.py)
- Successful data updates from API
- Authentication failure handling
- Network error handling and retries

### Coordinator Metadata Tests (test_coordinator_metadata.py)
- Cheapest fuel calculation with multiple stations
- Metadata field population (supermarket, motorway, amenities, etc.)
- Price timestamp storage and handling
- None/empty value handling with defaults

### Cheapest Sensor Tests (test_cheapest_sensor.py)
- Cheapest price calculation across stations
- Station switching when cheaper price found
- Attribute population with full metadata
- Price timestamp inclusion
- Device info and unique IDs
- Unavailable state handling

### Init Tests (test_init.py)
- Integration setup and entry loading
- Integration unload and cleanup

### Sensor Tests (test_sensor.py)
- Sensor entity creation and setup with fuel type filtering
- State updates with fuel prices
- Attribute population (station details + metadata + timestamps)
- Price timestamp attributes
- Unavailable state when no data
- Dynamic station addition

### Stale Device Tests (test_stale_devices.py)
- Grace period for missing stations (2 update cycles)
- Device removal after grace period
- Station reappearance handling

### Integration Tests (test_integration_simple.py)
- Real API connectivity
- Station search by location
- Fuel price retrieval
- Data structure validation
- **Note:** Blocked by pytest-socket in normal runs, use standalone test instead

### Standalone API Test (test_api_integration.py)
- Real API calls without pytest-socket blocking
- Location search with metadata verification
- Price timestamp verification and age calculation
- Specific station lookup (e.g., Wool Bovington)
- Stale price identification
- Rate limit testing

## API Credentials Setup

Create a `.env` file in the project root (already gitignored):

```bash
# UK Fuel Finder API Credentials
FUEL_FINDER_CLIENT_ID=your_client_id_here
FUEL_FINDER_CLIENT_SECRET=your_client_secret_here
FUEL_FINDER_ENVIRONMENT=production
```

**Security:** The `.env` file is in `.gitignore` and will NOT be committed to git.

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

GitHub Actions workflow runs on push to dev/main branches:

```yaml
- name: Run black
  run: black --check custom_components tests

- name: Run isort
  run: isort --check-only custom_components tests

- name: Run tests
  run: PYTHONPATH=. pytest tests/ -v -k "not integration"
```

Expected: **30 passed, 2 deselected**

Integration tests are excluded from CI as they require API credentials and make real network calls.

## Troubleshooting

### ModuleNotFoundError: No module named 'custom_components'

Always use `PYTHONPATH=.` when running tests:
```bash
PYTHONPATH=. pytest tests/ -v
```

### Integration tests skipped

Set API credentials in `.env` file or environment:
```bash
# In .env file (recommended)
FUEL_FINDER_CLIENT_ID=your_client_id
FUEL_FINDER_CLIENT_SECRET=your_client_secret
FUEL_FINDER_ENVIRONMENT=production

# Or export in shell
export FUEL_FINDER_CLIENT_ID="..."
export FUEL_FINDER_CLIENT_SECRET="..."
```

Then run standalone test:
```bash
python3.12 tests/test_api_integration.py
```

### Async warnings

Tests use `asyncio_mode = "auto"` in `pyproject.toml` to handle async properly.
