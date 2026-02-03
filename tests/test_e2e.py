"""End-to-end tests using Docker Home Assistant and Playwright."""
import asyncio
import os
import time
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def ha_url():
    """Home Assistant URL."""
    return os.getenv("HA_URL", "http://localhost:8123")


@pytest.fixture(scope="session")
def ha_token():
    """Home Assistant long-lived access token."""
    token = os.getenv("HA_TOKEN")
    if not token:
        pytest.skip("HA_TOKEN environment variable not set")
    return token


def test_integration_appears_in_list(page: Page, ha_url: str, ha_token: str):
    """Test that UK Fuel Finder appears in integrations list."""
    # Login
    page.goto(f"{ha_url}/?auth_callback=1")
    page.evaluate(f"localStorage.setItem('hassTokens', '{ha_token}')")
    page.goto(ha_url)
    
    # Wait for Home Assistant to load
    page.wait_for_selector("home-assistant", timeout=30000)
    
    # Navigate to integrations
    page.goto(f"{ha_url}/config/integrations")
    page.wait_for_load_state("networkidle")
    
    # Click Add Integration
    page.click("text=Add Integration")
    page.wait_for_selector("ha-dialog")
    
    # Search for UK Fuel Finder
    search_input = page.locator("ha-dialog input[type='search']")
    search_input.fill("UK Fuel Finder")
    
    # Verify integration appears
    expect(page.locator("text=UK Fuel Finder")).to_be_visible(timeout=5000)


def test_config_flow_validation(page: Page, ha_url: str, ha_token: str):
    """Test config flow shows validation errors."""
    # Login
    page.goto(f"{ha_url}/?auth_callback=1")
    page.evaluate(f"localStorage.setItem('hassTokens', '{ha_token}')")
    page.goto(ha_url)
    
    page.wait_for_selector("home-assistant", timeout=30000)
    
    # Navigate to integrations
    page.goto(f"{ha_url}/config/integrations")
    page.wait_for_load_state("networkidle")
    
    # Add integration
    page.click("text=Add Integration")
    page.wait_for_selector("ha-dialog")
    
    search_input = page.locator("ha-dialog input[type='search']")
    search_input.fill("UK Fuel Finder")
    
    page.click("text=UK Fuel Finder")
    page.wait_for_selector("ha-dialog")
    
    # Try to submit without credentials
    page.click("button:has-text('Submit')")
    
    # Should show validation error
    expect(page.locator("text=cannot_connect, text=invalid")).to_be_visible(timeout=5000)


@pytest.mark.skipif(
    not os.getenv("HA_TEST_CLIENT_ID") or not os.getenv("HA_TEST_CLIENT_SECRET"),
    reason="Test API credentials not provided"
)
def test_full_setup_flow(page: Page, ha_url: str, ha_token: str):
    """Test complete setup flow with valid credentials."""
    client_id = os.getenv("HA_TEST_CLIENT_ID")
    client_secret = os.getenv("HA_TEST_CLIENT_SECRET")
    
    # Login
    page.goto(f"{ha_url}/?auth_callback=1")
    page.evaluate(f"localStorage.setItem('hassTokens', '{ha_token}')")
    page.goto(ha_url)
    
    page.wait_for_selector("home-assistant", timeout=30000)
    
    # Navigate to integrations
    page.goto(f"{ha_url}/config/integrations")
    page.wait_for_load_state("networkidle")
    
    # Add integration
    page.click("text=Add Integration")
    page.wait_for_selector("ha-dialog")
    
    search_input = page.locator("ha-dialog input[type='search']")
    search_input.fill("UK Fuel Finder")
    page.click("text=UK Fuel Finder")
    
    page.wait_for_selector("ha-dialog")
    
    # Fill in form
    page.fill("input[name='client_id']", client_id)
    page.fill("input[name='client_secret']", client_secret)
    page.select_option("select[name='environment']", "test")
    page.fill("input[name='latitude']", "51.5074")
    page.fill("input[name='longitude']", "-0.1278")
    page.fill("input[name='radius']", "5")
    page.fill("input[name='update_interval']", "30")
    
    # Submit
    page.click("button:has-text('Submit')")
    
    # Wait for success
    page.wait_for_selector("text=Success", timeout=30000)
    
    # Verify integration card appears
    expect(page.locator("text=UK Fuel Finder")).to_be_visible()
    
    # Navigate to entities
    page.goto(f"{ha_url}/config/entities")
    page.wait_for_load_state("networkidle")
    
    # Search for ukfuelfinder entities
    search = page.locator("input[type='search']")
    search.fill("ukfuelfinder")
    
    # Should have at least one entity
    expect(page.locator("text=sensor.ukfuelfinder")).to_be_visible(timeout=10000)


def test_reconfigure_flow(page: Page, ha_url: str, ha_token: str):
    """Test reconfigure flow."""
    # Assumes integration is already set up
    page.goto(f"{ha_url}/?auth_callback=1")
    page.evaluate(f"localStorage.setItem('hassTokens', '{ha_token}')")
    page.goto(ha_url)
    
    page.wait_for_selector("home-assistant", timeout=30000)
    
    # Navigate to integrations
    page.goto(f"{ha_url}/config/integrations")
    page.wait_for_load_state("networkidle")
    
    # Find UK Fuel Finder integration
    integration_card = page.locator("text=UK Fuel Finder").locator("..")
    
    # Click options menu
    integration_card.locator("button[aria-label='Options']").click()
    
    # Click Configure
    page.click("text=Configure")
    page.wait_for_selector("ha-dialog")
    
    # Change radius
    page.fill("input[name='radius']", "10")
    
    # Submit
    page.click("button:has-text('Submit')")
    
    # Wait for success
    page.wait_for_selector("text=Success", timeout=10000)
