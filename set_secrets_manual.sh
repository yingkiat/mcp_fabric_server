#!/bin/bash

# Manual script to set Key Vault secrets in existing Container App
# Run this when you just want to update secrets without full deployment

set -euo pipefail

# Set up logging
LOG_FILE="set_secrets_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo "📝 Logging to: $LOG_FILE"
echo "🕐 Started at: $(date)"

# Configuration
CONTAINER_APP_NAME="fabric-mcp-agent"
RESOURCE_GROUP="M3-RG-ALZ-DWHS-ALYTICS-D-1"
KEY_VAULT_NAME="itapackeyvault"
KEY_VAULT_URL="https://itapackeyvault.vault.azure.net/"

echo "🔐 Setting up Key Vault secrets for Container App..."
echo "Container App: $CONTAINER_APP_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo "Key Vault: $KEY_VAULT_NAME"

# Check if Container App exists
if ! az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  echo "❌ Container App '$CONTAINER_APP_NAME' not found"
  exit 1
fi

# Get Container App's managed identity
APP_PRINCIPAL_ID=$(az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" --query "identity.principalId" -o tsv)
if [[ -z "$APP_PRINCIPAL_ID" || "$APP_PRINCIPAL_ID" == "null" ]]; then
  echo "❌ Container App doesn't have managed identity enabled"
  echo "Enable it with: az containerapp identity assign --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --system-assigned"
  exit 1
fi

echo "✅ Container App Principal ID: $APP_PRINCIPAL_ID"

# Grant Key Vault access
echo "🔑 Granting Key Vault access..."
az role assignment create \
  --assignee "$APP_PRINCIPAL_ID" \
  --role "Key Vault Secrets User" \
  --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$KEY_VAULT_NAME" \
  --output none 2>/dev/null || echo "Role assignment may already exist"

echo "⏱️ Waiting for permissions to propagate..."
sleep 30

# Verify Key Vault access
echo "🔍 Verifying Key Vault access..."
for i in {1..10}; do
  if az keyvault secret show --vault-name "$KEY_VAULT_NAME" --name "azureopenaikey" --query "value" -o tsv >/dev/null 2>&1; then
    echo "✅ Key Vault access verified"
    break
  fi
  echo "Waiting for Key Vault access... ($i/10)"
  sleep 10
done

# Get secrets directly from Key Vault and set as static values
echo "🔐 Retrieving secrets from Key Vault and setting as static values..."

# Retrieve secrets using your existing service principal access
AZURE_OPENAI_KEY=$(az keyvault secret show --vault-name "$KEY_VAULT_NAME" --name "azureopenaikey" --query "value" -o tsv)
AZURE_OPENAI_ENDPOINT=$(az keyvault secret show --vault-name "$KEY_VAULT_NAME" --name "azureopenaiendpoint" --query "value" -o tsv)
AZURE_CLIENT_ID=$(az keyvault secret show --vault-name "$KEY_VAULT_NAME" --name "azureclientid" --query "value" -o tsv)
AZURE_CLIENT_SECRET=$(az keyvault secret show --vault-name "$KEY_VAULT_NAME" --name "azureclientsecret" --query "value" -o tsv)
AZURE_TENANT_ID=$(az keyvault secret show --vault-name "$KEY_VAULT_NAME" --name "azuretenantid" --query "value" -o tsv)
AZURE_OPENAI_DEPLOYMENT=$(az keyvault secret show --vault-name "$KEY_VAULT_NAME" --name "azureopenaideployment" --query "value" -o tsv)

echo "✅ Retrieved all secrets from Key Vault"

# Set secrets as static values in Container App
az containerapp secret set \
  --name "$CONTAINER_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --secrets \
    azure-openai-key="$AZURE_OPENAI_KEY" \
    azure-openai-endpoint="$AZURE_OPENAI_ENDPOINT" \
    azure-client-id="$AZURE_CLIENT_ID" \
    azure-client-secret="$AZURE_CLIENT_SECRET" \
    azure-tenant-id="$AZURE_TENANT_ID" \
    azure-openai-deployment="$AZURE_OPENAI_DEPLOYMENT"

echo "✅ Secrets configured successfully"

# Set environment variables to reference the secrets
echo "🌍 Setting environment variables..."
az containerapp update \
  --name "$CONTAINER_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --set-env-vars \
    KEY_VAULT_URL="$KEY_VAULT_URL" \
    AZURE_OPENAI_KEY="secretref:azure-openai-key" \
    AZURE_OPENAI_ENDPOINT="secretref:azure-openai-endpoint" \
    AZURE_OPENAI_DEPLOYMENT="secretref:azure-openai-deployment" \
    AZURE_CLIENT_ID="secretref:azure-client-id" \
    AZURE_CLIENT_SECRET="secretref:azure-client-secret" \
    AZURE_TENANT_ID="secretref:azure-tenant-id"

echo "✅ Environment variables configured"

# Get app URL
APP_URL=$(az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv)
echo "🌐 Container App URL: https://$APP_URL"
echo "🎉 Secret configuration complete!"

# Test the app
echo "🧪 Testing app..."
sleep 10
if curl -f "https://$APP_URL/list_tools" > /dev/null 2>&1; then
  echo "✅ App is responding successfully"
else
  echo "⚠️ App may still be starting up - check logs if issues persist"
fi

echo "🕐 Completed at: $(date)"
echo "📝 Full log saved to: $LOG_FILE"