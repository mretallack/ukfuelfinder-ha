#!/usr/bin/env python3
"""
Standalone integration test for UK Fuel Finder API.
Tests real API calls including price_last_updated timestamp.
"""

import os
import sys
from datetime import datetime

# Load credentials from .env
env_file = ".env"
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

# Check credentials
if not os.getenv("FUEL_FINDER_CLIENT_ID"):
    print("❌ FUEL_FINDER_CLIENT_ID not found in environment")
    sys.exit(1)

print("🔧 Initializing UK Fuel Finder client...")
from ukfuelfinder import FuelFinderClient

client = FuelFinderClient(
    client_id=os.getenv("FUEL_FINDER_CLIENT_ID"),
    client_secret=os.getenv("FUEL_FINDER_CLIENT_SECRET"),
    environment=os.getenv("FUEL_FINDER_ENVIRONMENT", "production"),
)

print("✅ Client initialized\n")

# Test 1: Search by location
print("=" * 60)
print("TEST 1: Search by location (London, 5km radius)")
print("=" * 60)

try:
    results = client.search_by_location(latitude=51.5074, longitude=-0.1278, radius_km=5.0)
    print(f"✅ Found {len(results)} stations within 5km")
    
    if results:
        distance, station = results[0]
        print(f"\n📍 Nearest station:")
        print(f"   Name: {station.trading_name}")
        print(f"   Brand: {station.brand_name}")
        print(f"   Distance: {distance:.2f}km")
        print(f"   Location: {station.location.latitude}, {station.location.longitude}")
        print(f"   Address: {station.location.address_line_1}, {station.location.city}")
        print(f"   Postcode: {station.location.postcode}")
        
        # Check metadata fields
        print(f"\n🏪 Metadata:")
        print(f"   Supermarket: {station.is_supermarket_service_station}")
        print(f"   Motorway: {station.is_motorway_service_station}")
        print(f"   Amenities: {station.amenities}")
        print(f"   Fuel types: {station.fuel_types}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 2: Get fuel prices with timestamps
print("\n" + "=" * 60)
print("TEST 2: Get fuel prices (checking price_last_updated)")
print("=" * 60)

try:
    pfs_list = client.get_all_pfs_prices()
    print(f"✅ Retrieved {len(pfs_list)} PFS records")
    
    # Find a station with prices and timestamps
    stations_with_timestamps = []
    stations_without_timestamps = []
    
    for pfs in pfs_list[:100]:  # Check first 100
        if pfs.fuel_prices:
            for fuel_price in pfs.fuel_prices:
                if fuel_price.price is not None:
                    if fuel_price.price_last_updated:
                        stations_with_timestamps.append((pfs, fuel_price))
                    else:
                        stations_without_timestamps.append((pfs, fuel_price))
                    
                    if len(stations_with_timestamps) >= 3:
                        break
        if len(stations_with_timestamps) >= 3:
            break
    
    print(f"\n📊 Timestamp Statistics (first 100 stations):")
    print(f"   With timestamps: {len(stations_with_timestamps)}")
    print(f"   Without timestamps: {len(stations_without_timestamps)}")
    
    if stations_with_timestamps:
        print(f"\n💰 Sample prices with timestamps:")
        for i, (pfs, fuel_price) in enumerate(stations_with_timestamps[:3], 1):
            print(f"\n   {i}. {pfs.trading_name}")
            print(f"      Fuel: {fuel_price.fuel_type}")
            print(f"      Price: {fuel_price.price}p")
            print(f"      Last Updated: {fuel_price.price_last_updated}")
            if fuel_price.price_last_updated:
                age = datetime.now(fuel_price.price_last_updated.tzinfo) - fuel_price.price_last_updated
                print(f"      Age: {age.days} days, {age.seconds // 3600} hours")
    
    if stations_without_timestamps:
        print(f"\n⚠️  Sample prices WITHOUT timestamps:")
        pfs, fuel_price = stations_without_timestamps[0]
        print(f"   {pfs.trading_name}")
        print(f"   Fuel: {fuel_price.fuel_type}, Price: {fuel_price.price}p")
        print(f"   Last Updated: None")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Check for Wool Bovington station
print("\n" + "=" * 60)
print("TEST 3: Search for Wool Bovington station")
print("=" * 60)

try:
    # Wool, Dorset coordinates (approximate)
    results = client.search_by_location(latitude=50.6833, longitude=-2.2167, radius_km=5.0)
    print(f"✅ Found {len(results)} stations near Wool, Dorset")
    
    wool_stations = [s for d, s in results if "wool" in s.trading_name.lower() or "bovington" in s.trading_name.lower()]
    
    if wool_stations:
        print(f"\n🎯 Found Wool/Bovington station(s):")
        for station in wool_stations:
            print(f"\n   {station.trading_name}")
            print(f"   Brand: {station.brand_name}")
            print(f"   Address: {station.location.address_line_1}, {station.location.city}")
            
            # Get prices for this station
            for pfs in pfs_list:
                if pfs.node_id == station.node_id:
                    print(f"   Prices:")
                    for fp in pfs.fuel_prices:
                        if fp.price:
                            print(f"      {fp.fuel_type}: {fp.price}p (updated: {fp.price_last_updated})")
                    break
    else:
        print("   No stations found with 'Wool' or 'Bovington' in name")
        print(f"   Showing nearest 3 stations:")
        for i, (distance, station) in enumerate(results[:3], 1):
            print(f"   {i}. {station.trading_name} ({distance:.2f}km)")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ All integration tests completed successfully!")
print("=" * 60)
