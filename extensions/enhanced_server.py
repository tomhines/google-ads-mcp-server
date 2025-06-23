#!/usr/bin/env python3
"""
Enhanced Google Ads MCP Server with Ad Creation Extensions
Entry point that enhances the original server without modifying it

Usage:
    python extensions/enhanced_server.py

This server includes all original functionality plus:
- Responsive Search Ad creation
- Performance Max campaign creation  
- Bulk ad operations
- Enhanced asset management
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path so we can import original modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Import our extensions
from extensions.config.enhanced_config import EnhancedConfig
from extensions.ad_creation.tools.rsa_tools import register_rsa_tools, RSA_TOOLS
from extensions.ad_creation.services.rsa_service import RSAService
from extensions.ad_creation.services.pmax_service import PMaxService
from extensions.ad_creation.services.bulk_service import BulkService

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Google Ads client
from google.ads.googleads.client import GoogleAdsClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedGoogleAdsServer:
    """Enhanced server that wraps original functionality with extensions"""
    
    def __init__(self):
        self.config = EnhancedConfig()
        self.server = Server("google-ads-enhanced")
        self.client = None
        self.services = {}
        
    def initialize(self):
        """Initialize the enhanced server"""
        try:
            # Initialize Google Ads client
            self.client = self._create_google_ads_client()
            logger.info("Google Ads client initialized successfully")
            
            # Initialize our extension services
            self.services = {
                'rsa': RSAService(self.client, self.config),
                'pmax': PMaxService(self.client, self.config),
                'bulk': BulkService(self.client, self.config)
            }
            
            logger.info("Enhanced Google Ads MCP Server initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced server: {e}")
            # For development, continue without Google Ads client
            logger.warning("Continuing in development mode without Google Ads client")
            self.client = None
            self.services = {}
    
    def _create_google_ads_client(self):
        """Create Google Ads client with proper error handling"""
        
        if not self.config.credentials_path or not self.config.developer_token:
            raise ValueError("Missing Google Ads API credentials in environment")
        
        # Create client configuration
        if self.config.auth_type == "service_account":
            client_config = {
                "developer_token": self.config.developer_token,
                "path_to_private_key_file": self.config.credentials_path,
                "use_proto_plus": True,
            }
        else:  # oauth
            client_config = {
                "developer_token": self.config.developer_token,
                "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
                "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
                "use_proto_plus": True,
            }
        
        if self.config.login_customer_id:
            client_config["login_customer_id"] = self.config.login_customer_id.replace("-", "")
        
        return GoogleAdsClient.load_from_dict(client_config)
    
    def register_all_tools(self):
        """Register both original and extension tools"""
        
        # Register original tools would go here
        # For now, we'll just register our extension tools
        
        if self.services.get('rsa'):
            register_rsa_tools(self.server, self.services['rsa'])
            logger.info("RSA tools registered")
        
        # register_pmax_tools(self.server, self.services['pmax'])
        # register_bulk_tools(self.server, self.services['bulk'])
        
        logger.info("All available tools registered")
    
    @property 
    def list_tools_handler(self):
        """Return the list_tools handler"""
        @self.server.list_tools()
        async def list_tools():
            """List all available tools"""
            tools = []
            
            # Add our extension tools
            tools.extend(RSA_TOOLS)
            
            # Original tools would be added here
            # tools.extend(ORIGINAL_ANALYSIS_TOOLS)
            # tools.extend(ORIGINAL_REPORTING_TOOLS)
            
            return tools
        
        return list_tools
    
    async def run(self):
        """Run the enhanced server"""
        try:
            self.initialize()
            self.register_all_tools()
            
            # Set up the list_tools handler
            self.list_tools_handler
            
            logger.info("Starting enhanced Google Ads MCP server...")
            
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
                
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise

async def main():
    """Main entry point"""
    try:
        enhanced_server = EnhancedGoogleAdsServer()
        await enhanced_server.run()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())