#!/bin/bash
set -e

echo "Stopping Home Assistant test environment..."

docker-compose -f docker-compose.test.yml down -v

echo "Cleaning up test config..."
rm -rf test_config

echo "Test environment stopped and cleaned up."
