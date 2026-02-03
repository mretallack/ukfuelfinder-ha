"""Fixtures for UK Fuel Finder tests."""
import pytest
from unittest.mock import patch


@pytest.fixture
def mock_fuel_finder_client():
    """Mock FuelFinderClient."""
    with patch("custom_components.ukfuelfinder.config_flow.FuelFinderClient") as mock:
        yield mock


@pytest.fixture
def mock_setup_entry():
    """Mock setup entry."""
    with patch("custom_components.ukfuelfinder.async_setup_entry", return_value=True) as mock:
        yield mock
