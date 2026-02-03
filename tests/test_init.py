"""Test UK Fuel Finder init."""
from unittest.mock import MagicMock, patch

import pytest

from custom_components.ukfuelfinder import async_setup_entry, async_unload_entry
from custom_components.ukfuelfinder.const import DOMAIN


async def test_setup_entry(hass):
    """Test setup entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.data = {
        "client_id": "test_id",
        "client_secret": "test_secret",
        "environment": "test",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "radius": 5.0,
        "update_interval": 30,
    }
    
    with patch("custom_components.ukfuelfinder.UKFuelFinderCoordinator") as mock_coord:
        mock_instance = mock_coord.return_value
        mock_instance.async_config_entry_first_refresh = MagicMock()
        
        with patch.object(hass.config_entries, "async_forward_entry_setups") as mock_forward:
            result = await async_setup_entry(hass, entry)
            
            assert result is True
            assert DOMAIN in hass.data
            assert entry.entry_id in hass.data[DOMAIN]
            mock_forward.assert_called_once()


async def test_unload_entry(hass):
    """Test unload entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    
    hass.data[DOMAIN] = {entry.entry_id: MagicMock()}
    
    with patch.object(hass.config_entries, "async_unload_platforms", return_value=True):
        result = await async_unload_entry(hass, entry)
        
        assert result is True
        assert entry.entry_id not in hass.data[DOMAIN]
