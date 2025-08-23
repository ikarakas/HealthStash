#!/bin/bash
# HealthStash Test Runner
# This script runs tests from the tests directory

# Change to the script's directory
cd "$(dirname "$0")"

# Run the actual test script from tests directory
./tests/run-tests.sh "$@"