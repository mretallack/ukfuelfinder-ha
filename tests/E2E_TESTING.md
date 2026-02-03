# End-to-End Testing with Docker and Playwright

This integration includes E2E tests that run against a real Home Assistant instance in Docker.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+
- Playwright browsers installed

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt
   playwright install chromium
   ```

2. Start the test environment:
   ```bash
   ./scripts/start_test_env.sh
   ```

   This will:
   - Start Home Assistant in Docker
   - Create a test configuration
   - Set up a test user
   - Save the access token

3. Set environment variables:
   ```bash
   export HA_URL=http://localhost:8123
   export HA_TOKEN=$(cat test_config/.token)
   ```

4. (Optional) For full setup flow test, set test API credentials:
   ```bash
   export HA_TEST_CLIENT_ID=your_test_client_id
   export HA_TEST_CLIENT_SECRET=your_test_client_secret
   ```

## Running Tests

### Run all E2E tests:
```bash
pytest tests/test_e2e.py -v
```

### Run specific test:
```bash
pytest tests/test_e2e.py::test_integration_appears_in_list -v
```

### Run with headed browser (see what's happening):
```bash
pytest tests/test_e2e.py --headed -v
```

### Run with slow motion (for debugging):
```bash
pytest tests/test_e2e.py --headed --slowmo 1000 -v
```

## Test Coverage

The E2E tests cover:

1. **Integration Discovery** - Verifies UK Fuel Finder appears in integrations list
2. **Config Flow Validation** - Tests form validation and error handling
3. **Full Setup Flow** - Complete integration setup with real API (requires credentials)
4. **Reconfigure Flow** - Tests changing settings via UI

## Cleanup

Stop and remove the test environment:
```bash
./scripts/stop_test_env.sh
```

## Troubleshooting

### Home Assistant won't start
- Check Docker logs: `docker-compose -f docker-compose.test.yml logs`
- Ensure port 8123 is not already in use
- Try: `docker-compose -f docker-compose.test.yml down -v` and restart

### Tests fail with timeout
- Increase timeout in test: `page.wait_for_selector("...", timeout=60000)`
- Check Home Assistant is accessible: `curl http://localhost:8123`

### Token not working
- Complete onboarding manually at http://localhost:8123
- Create a long-lived access token in HA UI
- Set it: `export HA_TOKEN=your_token`

### Integration not found
- Verify custom_components is mounted: `docker exec ha_test ls /config/custom_components`
- Check logs: `docker-compose -f docker-compose.test.yml logs | grep ukfuelfinder`

## CI/CD Integration

To run E2E tests in CI:

```yaml
- name: Start Home Assistant
  run: ./scripts/start_test_env.sh

- name: Run E2E tests
  env:
    HA_URL: http://localhost:8123
    HA_TOKEN: ${{ secrets.HA_TOKEN }}
  run: pytest tests/test_e2e.py -v

- name: Stop Home Assistant
  if: always()
  run: ./scripts/stop_test_env.sh
```
