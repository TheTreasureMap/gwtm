#!/bin/bash

# Remove namespace if it exists
kubectl delete namespace gwtm

# Create namespace if it doesn't exist
#kubectl create namespace gwtm 2>/dev/null || true

# Clean up any existing deployments
kubectl delete deployment -n gwtm --all 2>/dev/null || true

# Run skaffold with simple options
echo "Starting skaffold development environment..."
skaffold dev
