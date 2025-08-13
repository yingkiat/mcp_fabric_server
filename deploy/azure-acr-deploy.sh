#!/bin/bash
# Azure Container Registry Deployment Script with Logging
# Usage: ./deploy/azure-acr-deploy.sh <registry-name> <resource-group> [tag]

set -euo pipefail

# ---- Setup Logging ----
LOGFILE="deploy_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOGFILE") 2>&1

REGISTRY_NAME=${1:-"your-registry"}
RESOURCE_GROUP=${2:-"your-resource-group"}
IMAGE_TAG=${3:-"latest"}
IMAGE_NAME="fabric-mcp-agent"

echo "=========================================="
echo "🚀 Starting Azure Container Registry deployment"
echo "Timestamp: $(date)"
echo "Log File: $LOGFILE"
echo "Registry Name: $REGISTRY_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo "Image Tag: $IMAGE_TAG"
echo "=========================================="

# ---- Check Azure Login ----
echo "🔐 Checking Azure login..."
if ! az account show &>/dev/null; then
    echo "❌ Not logged in to Azure CLI. Please run: az login"
    exit 1
fi
echo "✅ Azure CLI authenticated"

# ---- ACR Check/Create ----
echo "📦 Checking Azure Container Registry existence..."
ACR_INFO=$(az acr show --name "$REGISTRY_NAME" --resource-group "$RESOURCE_GROUP" 2>&1) || {
    echo "❌ Failed to retrieve ACR. Output:"
    echo "$ACR_INFO"
    
    if echo "$ACR_INFO" | grep -qi 'AuthorizationFailed'; then
        echo "🔒 You may not have permission to access the ACR or resource group."
    elif echo "$ACR_INFO" | grep -qi 'ResourceNotFound'; then
        echo "❌ ACR does not exist in the specified resource group: $RESOURCE_GROUP"
    else
        echo "⚠️ Unknown error occurred while checking ACR."
    fi
    exit 1
}

echo "✅ ACR exists: $REGISTRY_NAME"

# ---- TLS: use combined corp+certifi CA bundle ----
# Optional: set AZURE_CA_BUNDLE_WIN to override the default Windows path
AZURE_CA_BUNDLE_WIN="${AZURE_CA_BUNDLE_WIN:-C:\\Users\\yingkiat.gan\\Downloads\\corp-plus-certifi.pem}"

resolve_win_to_unix() {
  local win="$1"
  # If caller already provided a unix path, just return it if it exists
  if [[ -f "$win" ]]; then echo "$win"; return; fi

  # Prefer cygpath (Git Bash/MSYS)
  if command -v cygpath >/dev/null 2>&1; then
    local p; p="$(cygpath -u "$win" 2>/dev/null || true)"
     [[ -n "$p" ]] && echo "$p" && return
  fi

  # WSL path conversion
  if command -v wslpath >/dev/null 2>&1; then
    local p; p="$(wslpath -a "$win" 2>/dev/null || true)"
     [[ -n "$p" ]] && echo "$p" && return
  fi

  # Fallback heuristics (drive letter → /c or /mnt/c)
  local drive rest
  drive="$(printf '%s' "$win" | sed -E 's/^([A-Za-z]):.*$/\1/' | tr '[:upper:]' '[:lower:]')"
  rest="$(printf '%s' "$win" | sed -E 's/^[A-Za-z]:(.*)$/\1/' | tr '\\' '/')"

  if [[ -f "/$drive$rest" ]]; then echo "/$drive$rest" && return; fi
  if [[ -f "/mnt/$drive$rest" ]]; then echo "/mnt/$drive$rest" && return; fi

  # Give back empty so caller can error out cleanly
  echo ""
}

# If AZURE_CA_BUNDLE already points to a valid unix file, use it verbatim
if [[ -n "${AZURE_CA_BUNDLE:-}" && -f "$AZURE_CA_BUNDLE" ]]; then
  CA_PATH="$AZURE_CA_BUNDLE"
else
  CA_PATH="$(resolve_win_to_unix "$AZURE_CA_BUNDLE_WIN")"
fi

if [[ -z "$CA_PATH" || ! -f "$CA_PATH" ]]; then
  echo "❌ CA bundle not found."
  echo "   Windows path tried: $AZURE_CA_BUNDLE_WIN"
  echo "   Resolved unix path: ${CA_PATH:-<none>}"
  echo "   Tip: If you are in WSL, the path is usually /mnt/c/Users/yingkiat.gan/Downloads/corp-plus-certifi.pem"
  exit 1
fi

export AZURE_CA_BUNDLE="$CA_PATH"
export REQUESTS_CA_BUNDLE="$CA_PATH"
echo "🔏 Using CA bundle: $AZURE_CA_BUNDLE"

# ---- Build Image ----
echo "🔨 Starting ACR image build..."
az acr build --registry "$REGISTRY_NAME" --image "$IMAGE_NAME:$IMAGE_TAG" . \
    || { echo "❌ ACR build failed"; exit 1; }

# ---- Done ----
echo "✅ Deployment complete!"
echo "Image URL: $REGISTRY_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG"

# ---- Hold Window ----
echo ""
echo "📄 Full log saved to: $LOGFILE"
echo "Press any key to close this window..."
read -n 1 -s
