#!/bin/bash
# Azure Container Apps Deployment Script
# Usage: ./deploy/azure-container-app.sh <app-name> <registry-name> <resource-group> [image-tag]

# Enhanced error handling
set -x  # Show all commands being executed

exec > >(tee -a deploy-debug.log) 2>&1  # Log everything

echo "=== DEPLOYMENT DEBUG LOG ==="
echo "Timestamp: $(date)"
echo "Current directory: $(pwd)"
echo "User: $(whoami)"

# Configuration
REGISTRY_NAME=${1:-"itapacdataacr"}
RESOURCE_GROUP=${2:-"M3-RG-ALZ-DWHS-ALYTICS-D-1"}
IMAGE_TAG=${3:-"latest"}
IMAGE_NAME="fabric-mcp-agent"

echo "Registry: $REGISTRY_NAME"
echo "Resource Group: $RESOURCE_GROUP"

# Test Azure CLI
echo "=== Testing Azure CLI ==="
az --version || { echo "Azure CLI failed"; exit 1; }

# Test Azure login
echo "=== Testing Azure Login ==="
az account show || { echo "Not logged in to Azure"; exit 1; }

# Test network connectivity
echo "=== Testing Network ==="
curl -I https://management.azure.com/ || echo "Network connectivity issue"

# Check if ACR exists
echo "=== Checking ACR ==="
az acr show --name "$REGISTRY_NAME" --resource-group "$RESOURCE_GROUP" || {
    echo "ACR doesn't exist or access denied"
    exit 1
}

# Try the build
echo "=== Starting Build ==="
az acr build --registry "$REGISTRY_NAME" --image "$IMAGE_NAME:$IMAGE_TAG" . --verbose

echo "=== Script completed ==="
echo "Check deploy-debug.log for full details"

# Keep window open if running in popup
if [ -t 0 ]; then
    read -p "Press Enter to continue..."
fi