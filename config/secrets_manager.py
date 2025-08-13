"""
Unified secrets management supporting both local .env files and Azure Key Vault
"""
import os
import logging
from typing import Optional, Dict, Any
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class SecretsManager:
    """
    Unified secrets manager that fetches from:
    1. Local development: .env file
    2. Azure Container Apps: Key Vault with Managed Identity
    """
    
    def __init__(self):
        self.key_vault_url = os.getenv('KEY_VAULT_URL')
        self.use_key_vault = bool(self.key_vault_url)
        self.secret_client = None
        self._cache = {}
        
        if self.use_key_vault:
            self._init_key_vault()
        else:
            self._init_local_env()
    
    def _init_key_vault(self):
        """Initialize Azure Key Vault client with Managed Identity"""
        try:
            # Use Managed Identity in Azure Container Apps
            credential = ManagedIdentityCredential()
            self.secret_client = SecretClient(
                vault_url=self.key_vault_url, 
                credential=credential
            )
            logger.info(f"Initialized Key Vault client: {self.key_vault_url}")
        except Exception as e:
            logger.warning(f"Key Vault initialization failed: {e}")
            # Fallback to DefaultAzureCredential for development
            try:
                credential = DefaultAzureCredential()
                self.secret_client = SecretClient(
                    vault_url=self.key_vault_url,
                    credential=credential
                )
                logger.info("Using DefaultAzureCredential for Key Vault")
            except Exception as e2:
                logger.error(f"All Key Vault authentication methods failed: {e2}")
                raise
    
    def _init_local_env(self):
        """Load environment variables from .env file"""
        load_dotenv()
        logger.info("Using local .env file for secrets")
    
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret from Key Vault or environment variables
        
        Args:
            secret_name: Name of the secret (will be normalized for Key Vault)
            default: Default value if secret not found
            
        Returns:
            Secret value or default
        """
        # Check cache first
        if secret_name in self._cache:
            return self._cache[secret_name]
        
        value = None
        
        if self.use_key_vault:
            value = self._get_from_key_vault(secret_name)
        
        # Fallback to environment variable
        if value is None:
            value = os.getenv(secret_name, default)
        
        # Cache the result
        if value is not None:
            self._cache[secret_name] = value
        
        return value
    
    def _get_from_key_vault(self, secret_name: str) -> Optional[str]:
        """Get secret from Azure Key Vault"""
        if not self.secret_client:
            return None
        
        try:
            # Key Vault secret names must be alphanumeric and hyphens only
            # Convert environment variable names to Key Vault format
            kv_secret_name = self._normalize_secret_name(secret_name)
            
            secret = self.secret_client.get_secret(kv_secret_name)
            logger.debug(f"Retrieved secret '{kv_secret_name}' from Key Vault")
            return secret.value
        except Exception as e:
            logger.warning(f"Failed to get secret '{secret_name}' from Key Vault: {e}")
            return None
    
    def _normalize_secret_name(self, name: str) -> str:
        """
        Convert environment variable name to Key Vault secret name
        Example: FABRIC_SQL_SERVER -> fabric-sql-server
        """
        return name.lower().replace('_', '-')
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all required configuration values"""
        config = {
            # Fabric Data Warehouse
            'FABRIC_SQL_SERVER': self.get_secret('FABRIC_SQL_SERVER'),
            'FABRIC_SQL_DATABASE': self.get_secret('FABRIC_SQL_DATABASE'),
            
            # Azure Authentication
            'AZURE_CLIENT_ID': self.get_secret('AZURE_CLIENT_ID'),
            'AZURE_CLIENT_SECRET': self.get_secret('AZURE_CLIENT_SECRET'),
            'AZURE_TENANT_ID': self.get_secret('AZURE_TENANT_ID'),
            
            # Azure OpenAI
            'AZURE_OPENAI_KEY': self.get_secret('AZURE_OPENAI_KEY'),
            'AZURE_OPENAI_ENDPOINT': self.get_secret('AZURE_OPENAI_ENDPOINT'),
            'AZURE_OPENAI_DEPLOYMENT': self.get_secret('AZURE_OPENAI_DEPLOYMENT'),
        }
        
        # Validate required secrets
        missing_secrets = [k for k, v in config.items() if v is None]
        if missing_secrets:
            logger.error(f"Missing required secrets: {missing_secrets}")
            raise ValueError(f"Missing required configuration: {missing_secrets}")
        
        # Set environment variables for backward compatibility
        for key, value in config.items():
            if value:
                os.environ[key] = value
        
        return config

# Global instance
secrets_manager = SecretsManager()

def get_secret(name: str, default: str = None) -> str:
    """Convenience function to get a secret"""
    return secrets_manager.get_secret(name, default)

def initialize_config() -> Dict[str, Any]:
    """Initialize all configuration and return config dict"""
    return secrets_manager.get_all_config()