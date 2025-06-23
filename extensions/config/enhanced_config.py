"""
Enhanced Configuration for Google Ads MCP Server Extensions
Extends original configuration with ad creation settings
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class EnhancedConfig:
    """Configuration for enhanced Google Ads MCP server"""
    
    # Original config (inherited from base server)
    auth_type: str
    credentials_path: str
    developer_token: str
    login_customer_id: Optional[str]
    
    # Extension-specific config
    default_ad_status: str
    default_campaign_status: str
    max_headlines_per_rsa: int
    max_descriptions_per_rsa: int
    max_image_size_mb: int
    supported_image_formats: list
    default_business_name: str
    api_rate_limit_requests_per_minute: int
    bulk_operation_batch_size: int
    
    # Validation settings
    enable_strict_validation: bool
    auto_fix_character_limits: bool
    
    # Asset settings
    asset_upload_enabled: bool
    asset_cdn_base_url: Optional[str]
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        
        # Load original configuration
        self.auth_type = os.getenv("GOOGLE_ADS_AUTH_TYPE", "oauth")
        self.credentials_path = os.getenv("GOOGLE_ADS_CREDENTIALS_PATH", "")
        self.developer_token = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "")
        self.login_customer_id = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
        
        # Load extension configuration
        self.default_ad_status = os.getenv("DEFAULT_AD_STATUS", "PAUSED")
        self.default_campaign_status = os.getenv("DEFAULT_CAMPAIGN_STATUS", "PAUSED")
        self.max_headlines_per_rsa = int(os.getenv("MAX_HEADLINES_PER_RSA", "15"))
        self.max_descriptions_per_rsa = int(os.getenv("MAX_DESCRIPTIONS_PER_RSA", "4"))
        self.max_image_size_mb = int(os.getenv("MAX_IMAGE_SIZE_MB", "5"))
        
        # Parse image formats
        formats_str = os.getenv("SUPPORTED_IMAGE_FORMATS", "jpg,jpeg,png,gif")
        self.supported_image_formats = [f.strip() for f in formats_str.split(",")]
        
        self.default_business_name = os.getenv("DEFAULT_BUSINESS_NAME", "Your Business")
        self.api_rate_limit_requests_per_minute = int(os.getenv("API_RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
        self.bulk_operation_batch_size = int(os.getenv("BULK_OPERATION_BATCH_SIZE", "100"))
        
        # Validation settings
        self.enable_strict_validation = os.getenv("ENABLE_STRICT_VALIDATION", "true").lower() == "true"
        self.auto_fix_character_limits = os.getenv("AUTO_FIX_CHARACTER_LIMITS", "false").lower() == "true"
        
        # Asset settings
        self.asset_upload_enabled = os.getenv("ASSET_UPLOAD_ENABLED", "true").lower() == "true"
        self.asset_cdn_base_url = os.getenv("ASSET_CDN_BASE_URL")
        
        # Only validate if we have real credentials (not placeholder paths)
        if (self.credentials_path and 
            self.developer_token and 
            not self.credentials_path.startswith("/full/path/to/") and
            not self.developer_token.startswith("your_")):
            self._validate_config()
        else:
            print("⚠️  Running in development mode - no Google Ads API validation")
    
    def _validate_config(self):
        """Validate that required configuration is present"""
        if not self.credentials_path:
            raise ValueError("GOOGLE_ADS_CREDENTIALS_PATH is required")
        
        if not self.developer_token:
            raise ValueError("GOOGLE_ADS_DEVELOPER_TOKEN is required")
        
        if not Path(self.credentials_path).exists():
            raise ValueError(f"Credentials file not found: {self.credentials_path}")
        
        if self.auth_type not in ["oauth", "service_account"]:
            raise ValueError("GOOGLE_ADS_AUTH_TYPE must be 'oauth' or 'service_account'")
    
    def get_rsa_limits(self) -> Dict[str, int]:
        """Get RSA limits configuration"""
        return {
            "max_headlines": self.max_headlines_per_rsa,
            "max_descriptions": self.max_descriptions_per_rsa,
            "headline_char_limit": 30,
            "description_char_limit": 90
        }
    
    def get_asset_limits(self) -> Dict[str, Any]:
        """Get asset upload limits"""
        return {
            "max_size_mb": self.max_image_size_mb,
            "supported_formats": self.supported_image_formats,
            "upload_enabled": self.asset_upload_enabled
        }
    
    def get_rate_limits(self) -> Dict[str, int]:
        """Get API rate limit configuration"""
        return {
            "requests_per_minute": self.api_rate_limit_requests_per_minute,
            "batch_size": self.bulk_operation_batch_size
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for logging/debugging"""
        config_dict = {}
        for key, value in self.__dict__.items():
            # Don't log sensitive information
            if "token" in key.lower() or "secret" in key.lower():
                config_dict[key] = "***REDACTED***"
            elif "path" in key.lower():
                config_dict[key] = "***PATH***"
            else:
                config_dict[key] = value
        return config_dict

# Don't create global config instance at module level
# Let the server create it when needed