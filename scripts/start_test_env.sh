#!/bin/bash
set -e

echo "Starting Home Assistant test environment..."

# Create test config directory
mkdir -p test_config

# Create minimal configuration.yaml
cat > test_config/configuration.yaml << EOF
default_config:

homeassistant:
  name: Test Home
  latitude: 51.5074
  longitude: -0.1278
  elevation: 0
  unit_system: metric
  time_zone: Europe/London

http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 172.16.0.0/12

logger:
  default: info
  logs:
    custom_components.ukfuelfinder: debug
EOF

# Start Home Assistant
echo "Starting Docker container..."
docker-compose -f docker-compose.test.yml up -d

# Wait for Home Assistant to be ready
echo "Waiting for Home Assistant to start..."
timeout=120
elapsed=0
while ! curl -s http://localhost:8123 > /dev/null; do
    if [ $elapsed -ge $timeout ]; then
        echo "Timeout waiting for Home Assistant"
        docker-compose -f docker-compose.test.yml logs
        exit 1
    fi
    echo "Waiting... ($elapsed/$timeout seconds)"
    sleep 5
    elapsed=$((elapsed + 5))
done

echo "Home Assistant is ready!"

# Create onboarding user and get token
echo "Creating test user..."
docker exec ha_test python3 -c "
import asyncio
from homeassistant.core import HomeAssistant
from homeassistant.auth.providers.homeassistant import HassAuthProvider

async def create_user():
    hass = HomeAssistant()
    await hass.async_start()
    
    auth = hass.auth
    provider = auth.get_auth_provider('homeassistant', None)
    
    # Create user
    user = await hass.auth.async_create_user('test_user')
    await provider.async_add_auth('test', 'test123')
    
    # Create token
    refresh_token = await hass.auth.async_create_refresh_token(user)
    token = hass.auth.async_create_access_token(refresh_token)
    
    print(f'TOKEN:{token}')
    
    await hass.async_stop()

asyncio.run(create_user())
" 2>/dev/null | grep "TOKEN:" | cut -d: -f2 > test_config/.token

if [ -f test_config/.token ]; then
    echo "Test user created successfully"
    echo "Token saved to test_config/.token"
else
    echo "Warning: Could not create test user automatically"
    echo "You may need to complete onboarding manually at http://localhost:8123"
fi

echo ""
echo "Home Assistant test environment is ready!"
echo "URL: http://localhost:8123"
echo ""
echo "To run E2E tests:"
echo "  export HA_URL=http://localhost:8123"
echo "  export HA_TOKEN=\$(cat test_config/.token)"
echo "  pytest tests/test_e2e.py"
echo ""
echo "To stop:"
echo "  ./scripts/stop_test_env.sh"
