"""Simple integration test with real API."""

import os

import pytest

# Disable socket blocking for these tests
pytestmark = pytest.mark.enable_socket


@pytest.mark.skipif(not os.getenv("FUEL_FINDER_CLIENT_ID"), reason="API credentials not provided")
def test_ukfuelfinder_library():
    """Test that ukfuelfinder library works."""
    from ukfuelfinder import FuelFinderClient

    client = FuelFinderClient(
        client_id=os.getenv("FUEL_FINDER_CLIENT_ID"),
        client_secret=os.getenv("FUEL_FINDER_CLIENT_SECRET"),
        environment=os.getenv("FUEL_FINDER_ENVIRONMENT", "production"),
    )

    # Test search by location
    results = client.search_by_location(latitude=51.5074, longitude=-0.1278, radius_km=5.0)

    assert isinstance(results, list)
    print(f"\nFound {len(results)} stations within 5km of London")

    if results:
        distance, station = results[0]
        print(f"Nearest station: {station.trading_name} at {distance:.2f}km")
        assert hasattr(station, "pfs_id")
        assert hasattr(station, "trading_name")
        assert hasattr(station, "latitude")
        assert hasattr(station, "longitude")


@pytest.mark.skipif(not os.getenv("FUEL_FINDER_CLIENT_ID"), reason="API credentials not provided")
def test_get_prices():
    """Test getting fuel prices."""
    from ukfuelfinder import FuelFinderClient

    client = FuelFinderClient(
        client_id=os.getenv("FUEL_FINDER_CLIENT_ID"),
        client_secret=os.getenv("FUEL_FINDER_CLIENT_SECRET"),
        environment=os.getenv("FUEL_FINDER_ENVIRONMENT", "production"),
    )

    prices = client.get_all_pfs_prices()

    assert isinstance(prices, list)
    print(f"\nFound {len(prices)} price records")

    if prices:
        price = prices[0]
        print(f"Sample: {price.fuel_type} at {price.price}p")
        assert hasattr(price, "pfs_id")
        assert hasattr(price, "fuel_type")
        assert hasattr(price, "price")
