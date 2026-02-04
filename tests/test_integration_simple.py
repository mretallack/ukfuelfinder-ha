"""Simple integration test with real API."""

import os

import pytest

# Disable socket blocking for these tests
pytestmark = pytest.mark.enable_socket


@pytest.mark.skipif(not os.getenv("FUEL_FINDER_CLIENT_ID"), reason="API credentials not provided")
def test_ukfuelfinder_library():
    """Test that ukfuelfinder library works with correct API structure."""
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
        
        # Check correct attributes
        assert hasattr(station, "node_id"), "Station should have node_id"
        assert hasattr(station, "trading_name"), "Station should have trading_name"
        assert hasattr(station, "brand_name"), "Station should have brand_name"
        assert hasattr(station, "public_phone_number"), "Station should have public_phone_number"
        assert hasattr(station, "location"), "Station should have location object"
        
        # Check location attributes
        if station.location:
            assert hasattr(station.location, "latitude"), "Location should have latitude"
            assert hasattr(station.location, "longitude"), "Location should have longitude"
            assert hasattr(station.location, "address_line_1"), "Location should have address_line_1"
            assert hasattr(station.location, "city"), "Location should have city"
            assert hasattr(station.location, "postcode"), "Location should have postcode"
            
            print(f"  ID: {station.node_id}")
            print(f"  Brand: {station.brand_name}")
            print(f"  Location: {station.location.latitude}, {station.location.longitude}")
            print(f"  Address: {station.location.address_line_1}, {station.location.city}")


@pytest.mark.skipif(not os.getenv("FUEL_FINDER_CLIENT_ID"), reason="API credentials not provided")
def test_get_prices():
    """Test getting fuel prices with correct API structure."""
    from ukfuelfinder import FuelFinderClient

    client = FuelFinderClient(
        client_id=os.getenv("FUEL_FINDER_CLIENT_ID"),
        client_secret=os.getenv("FUEL_FINDER_CLIENT_SECRET"),
        environment=os.getenv("FUEL_FINDER_ENVIRONMENT", "production"),
    )

    pfs_list = client.get_all_pfs_prices()

    assert isinstance(pfs_list, list)
    print(f"\nFound {len(pfs_list)} PFS records")

    if pfs_list:
        pfs = pfs_list[0]
        
        # Check PFS attributes
        assert hasattr(pfs, "node_id"), "PFS should have node_id"
        assert hasattr(pfs, "trading_name"), "PFS should have trading_name"
        assert hasattr(pfs, "fuel_prices"), "PFS should have fuel_prices list"
        
        print(f"PFS: {pfs.trading_name} (ID: {pfs.node_id})")
        print(f"  Fuel prices count: {len(pfs.fuel_prices)}")
        
        # Check fuel price structure
        if pfs.fuel_prices:
            fuel_price = pfs.fuel_prices[0]
            assert hasattr(fuel_price, "fuel_type"), "FuelPrice should have fuel_type"
            assert hasattr(fuel_price, "price"), "FuelPrice should have price"
            print(f"  Sample: {fuel_price.fuel_type} at {fuel_price.price}p")
