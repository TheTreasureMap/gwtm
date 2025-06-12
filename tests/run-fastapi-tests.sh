#!/bin/bash
# Run tests for a specific module
# Test data is loaded automatically by conftest.py
set -e

# Default value
MODULE=${1:-all}

if [ "$MODULE" == "all" ]; then
  # Run all test modules
  echo "===== Running all FastAPI tests ====="
  pytest tests/fastapi/ -v --disable-warnings
else
  # Run a specific module
  if [ -f "tests/fastapi/test_${MODULE}.py" ]; then
    echo "===== Running tests for module: $MODULE ====="
    pytest tests/fastapi/test_${MODULE}.py -v --disable-warnings
  else
    echo "Module test file not found: tests/fastapi/test_${MODULE}.py"
    exit 1
  fi
fi

echo "All tests completed successfully!"