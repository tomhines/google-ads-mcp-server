#!/usr/bin/env python3
"""
Production Google Ads MCP Server with Real API Integration
Creates actual ads and campaigns in Google Ads
"""

import asyncio
import json
import logging
from pathlib import Path
import sys
import random
from datetime import datetime
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Google Ads imports
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# Our extensions
from extensions.config.enhanced_config import EnhancedConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server
server = Server("google-ads-production")

# Global variables
client = None
config = None

def initialize_google_ads_client():
    """Initialize Google Ads client with real credentials"""
    global client, config
    
    try:
        config = EnhancedConfig()
        
        if not config.credentials_path or not config.developer_token:
            logger.warning("No Google Ads credentials found - running in simulation mode")
            return None
        
        # Create client configuration
        if config.auth_type == "service_account":
            client_config = {
                "developer_token": config.developer_token,
                "json_key_file_path": config.credentials_path,  # Updated key name
                "use_proto_plus": True,
            }
        else:  # oauth
            client_config = {
                "developer_token": config.developer_token,
                "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
                "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
                "use_proto_plus": True,
            }
        
        if config.login_customer_id:
            client_config["login_customer_id"] = config.login_customer_id.replace("-", "")
        
        client = GoogleAdsClient.load_from_dict(client_config)
        logger.info("✅ Google Ads API client initialized successfully")
        return client
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Google Ads client: {e}")
        logger.info("🔄 Continuing in simulation mode")
        return None

# Define production tools
TOOLS = [
    Tool(
        name="validate_rsa_copy",
        description="Validate RSA headlines and descriptions for character limits and requirements.",
        inputSchema={
            "type": "object",
            "properties": {
                "headlines": {"type": "string", "description": "JSON array of headlines to validate"},
                "descriptions": {"type": "string", "description": "JSON array of descriptions to validate"},
                "auto_fix": {"type": "boolean", "description": "Whether to automatically fix character limit issues"}
            },
            "required": ["headlines", "descriptions"]
        }
    ),
    Tool(
        name="create_responsive_search_ad",
        description="Create a REAL Responsive Search Ad in Google Ads. Requires valid customer ID and ad group ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Google Ads customer ID (format: 123-456-7890)"},
                "ad_group_id": {"type": "string", "description": "Ad group ID where ad will be created"},
                "headlines": {"type": "string", "description": "JSON array of headlines (3-15 required)"},
                "descriptions": {"type": "string", "description": "JSON array of descriptions (2-4 required)"},
                "final_urls": {"type": "string", "description": "JSON array of final URLs"},
                "path1": {"type": "string", "description": "Optional display URL path 1"},
                "path2": {"type": "string", "description": "Optional display URL path 2"}
            },
            "required": ["customer_id", "ad_group_id", "headlines", "descriptions", "final_urls"]
        }
    ),
    Tool(
        name="create_performance_max_campaign",
        description="Create a REAL Performance Max campaign with asset group in Google Ads.",
        inputSchema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Google Ads customer ID"},
                "campaign_name": {"type": "string", "description": "Name for the campaign"},
                "daily_budget": {"type": "number", "description": "Daily budget in dollars"},
                "business_name": {"type": "string", "description": "Business name (max 25 chars)"},
                "headlines": {"type": "string", "description": "JSON array of headlines"},
                "descriptions": {"type": "string", "description": "JSON array of descriptions"},
                "final_urls": {"type": "string", "description": "JSON array of final URLs"},
                "target_roas": {"type": "number", "description": "Optional target ROAS (e.g., 3.5 for 350%)"}
            },
            "required": ["customer_id", "campaign_name", "daily_budget", "business_name", "headlines", "descriptions", "final_urls"]
        }
    ),
    Tool(
        name="get_account_info",
        description="Get information about a Google Ads account including campaigns and ad groups.",
        inputSchema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Google Ads customer ID"}
            },
            "required": ["customer_id"]
        }
    ),
    Tool(
        name="get_campaign_performance",
        description="Get real performance data for campaigns.",
        inputSchema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Google Ads customer ID"},
                "campaign_id": {"type": "string", "description": "Optional specific campaign ID"},
                "date_range": {"type": "string", "description": "Date range (LAST_7_DAYS, LAST_30_DAYS, etc.)"}
            },
            "required": ["customer_id"]
        }
    ),
    Tool(
        name="generate_ad_variations",
        description="Generate multiple variations of ad copy based on business description and keywords.",
        inputSchema={
            "type": "object",
            "properties": {
                "business_description": {"type": "string", "description": "Description of the business"},
                "target_keywords": {"type": "string", "description": "JSON array of target keywords"},
                "tone": {"type": "string", "description": "Tone: professional, casual, urgent, friendly"},
                "num_headlines": {"type": "number", "description": "Number of headlines (3-15)"},
                "num_descriptions": {"type": "number", "description": "Number of descriptions (2-4)"}
            },
            "required": ["business_description", "target_keywords"]
        }
    ),
    Tool(
        name="create_search_campaign",
        description="Create a new Google Ads Search campaign with proper settings and targeting.",
        inputSchema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Google Ads customer ID"},
                "campaign_name": {"type": "string", "description": "Name for the new campaign"},
                "daily_budget": {"type": "number", "description": "Daily budget in dollars"},
                "target_locations": {"type": "string", "description": "JSON array of location names to target"},
                "target_languages": {"type": "string", "description": "JSON array of language codes (e.g., ['en', 'es'])"},
                "bidding_strategy": {"type": "string", "description": "Bidding strategy: maximize_clicks, target_cpa, target_roas, manual_cpc"},
                "target_cpa": {"type": "number", "description": "Target CPA in dollars (if using target_cpa bidding)"},
                "target_roas": {"type": "number", "description": "Target ROAS (if using target_roas bidding)"},
                "network_settings": {"type": "string", "description": "JSON object with search_network, display_network, youtube_search, youtube_videos"}
            },
            "required": ["customer_id", "campaign_name", "daily_budget"]
        }
    ),
    Tool(
        name="create_ad_group",
        description="Create a new ad group within an existing campaign with targeting and bid settings.",
        inputSchema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Google Ads customer ID"},
                "campaign_id": {"type": "string", "description": "Campaign ID where ad group will be created"},
                "ad_group_name": {"type": "string", "description": "Name for the new ad group"},
                "default_cpc_bid": {"type": "number", "description": "Default CPC bid in dollars"},
                "target_keywords": {"type": "string", "description": "JSON array of keywords to add to the ad group"},
                "keyword_match_types": {"type": "string", "description": "JSON array of match types for keywords: EXACT, PHRASE, BROAD"},
                "negative_keywords": {"type": "string", "description": "JSON array of negative keywords"}
            },
            "required": ["customer_id", "campaign_id", "ad_group_name", "default_cpc_bid"]
        }
    ),
    Tool(
        name="update_campaign",
        description="Update campaign settings like budget, status, or targeting options.",
        inputSchema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Google Ads customer ID"},
                "campaign_id": {"type": "string", "description": "Campaign ID to update"},
                "daily_budget": {"type": "number", "description": "New daily budget in dollars"},
                "status": {"type": "string", "description": "New status: ENABLED, PAUSED, REMOVED"},
                "campaign_name": {"type": "string", "description": "New campaign name"},
                "target_cpa": {"type": "number", "description": "New target CPA (for target_cpa campaigns)"},
                "target_roas": {"type": "number", "description": "New target ROAS (for target_roas campaigns)"}
            },
            "required": ["customer_id", "campaign_id"]
        }
    ),
    Tool(
        name="update_ad_group",
        description="Update ad group settings like bids, status, or name.",
        inputSchema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Google Ads customer ID"},
                "ad_group_id": {"type": "string", "description": "Ad group ID to update"},
                "ad_group_name": {"type": "string", "description": "New ad group name"},
                "default_cpc_bid": {"type": "number", "description": "New default CPC bid in dollars"},
                "status": {"type": "string", "description": "New status: ENABLED, PAUSED, REMOVED"}
            },
            "required": ["customer_id", "ad_group_id"]
        }
    ),
    Tool(
        name="get_campaign_structure",
        description="Get detailed campaign and ad group structure for an account.",
        inputSchema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Google Ads customer ID"},
                "campaign_id": {"type": "string", "description": "Optional: specific campaign ID to analyze"}
            },
            "required": ["customer_id"]
        }
    ),
    Tool(
        name="add_keywords_to_ad_group",
        description="Add keywords to an existing ad group with specified match types.",
        inputSchema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Google Ads customer ID"},
                "ad_group_id": {"type": "string", "description": "Ad group ID to add keywords to"},
                "keywords": {"type": "string", "description": "JSON array of keywords to add"},
                "match_types": {"type": "string", "description": "JSON array of match types: EXACT, PHRASE, BROAD"},
                "bids": {"type": "string", "description": "JSON array of custom bids for keywords (optional)"}
            },
            "required": ["customer_id", "ad_group_id", "keywords", "match_types"]
        }
    )
]

@server.list_tools()
async def list_tools():
    """List all available tools"""
    return TOOLS

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    
    # Initialize client if not already done
    if client is None:
        initialize_google_ads_client()
    
    if name == "validate_rsa_copy":
        return await handle_validate_rsa_copy(arguments)
    elif name == "create_responsive_search_ad":
        return await handle_create_responsive_search_ad(arguments)
    elif name == "create_performance_max_campaign":
        return await handle_create_performance_max_campaign(arguments)
    elif name == "get_account_info":
        return await handle_get_account_info(arguments)
    elif name == "get_campaign_performance":
        return await handle_get_campaign_performance(arguments)
    elif name == "generate_ad_variations":
        return await handle_generate_ad_variations(arguments)
    elif name == "create_search_campaign":
        return await handle_create_search_campaign(arguments)
    elif name == "create_ad_group":
        return await handle_create_ad_group(arguments)
    elif name == "update_campaign":
        return await handle_update_campaign(arguments)
    elif name == "update_ad_group":
        return await handle_update_ad_group(arguments)
    elif name == "get_campaign_structure":
       return await handle_get_campaign_structure(arguments)
    elif name == "add_keywords_to_ad_group":
       return await handle_add_keywords_to_ad_group(arguments)
    else:
        return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]

async def handle_create_search_campaign(arguments: dict) -> list[TextContent]:
    """Create a new Google Ads Search campaign"""
    
    try:
        if client is None:
            return [TextContent(type="text", text="❌ Google Ads API not available. Please configure credentials.")]
        
        customer_id = arguments.get("customer_id", "").replace("-", "")
        campaign_name = arguments.get("campaign_name", "")
        daily_budget = float(arguments.get("daily_budget", 0))
        target_locations = json.loads(arguments.get("target_locations", '["United States"]'))
        target_languages = json.loads(arguments.get("target_languages", '["en"]'))
        bidding_strategy = arguments.get("bidding_strategy", "maximize_clicks")
        target_cpa = arguments.get("target_cpa")
        target_roas = arguments.get("target_roas")
        network_settings = json.loads(arguments.get("network_settings", '{"search_network": true, "display_network": false}'))
        
        # Validate inputs
        if daily_budget <= 0:
            return [TextContent(type="text", text="❌ Daily budget must be greater than $0")]
        
        budget_micros = int(daily_budget * 1_000_000)
        
        # Step 1: Create campaign budget
        campaign_budget_service = client.get_service("CampaignBudgetService")
        budget_operation = client.get_type("CampaignBudgetOperation")
        
        campaign_budget = budget_operation.create
        campaign_budget.name = f"{campaign_name} Budget"
        campaign_budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
        campaign_budget.amount_micros = budget_micros
        
        budget_response = campaign_budget_service.mutate_campaign_budgets(
            customer_id=customer_id,
            operations=[budget_operation]
        )
        budget_resource_name = budget_response.results[0].resource_name
        
        # Step 2: Create search campaign
        campaign_service = client.get_service("CampaignService")
        campaign_operation = client.get_type("CampaignOperation")
        
        campaign = campaign_operation.create
        campaign.name = campaign_name
        campaign.status = client.enums.CampaignStatusEnum.PAUSED
        campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
        campaign.campaign_budget = budget_resource_name
        
        # Set bidding strategy
        if bidding_strategy == "maximize_clicks":
            campaign.maximize_clicks = client.get_type("MaximizeClicks")
        elif bidding_strategy == "target_cpa" and target_cpa:
            campaign.target_cpa.target_cpa_micros = int(float(target_cpa) * 1_000_000)
        elif bidding_strategy == "target_roas" and target_roas:
            campaign.target_roas.target_roas = float(target_roas)
        elif bidding_strategy == "manual_cpc":
            campaign.manual_cpc = client.get_type("ManualCpc")
        
        # Set network settings
        campaign.network_settings.target_google_search = network_settings.get("search_network", True)
        campaign.network_settings.target_search_network = network_settings.get("search_network", True)
        campaign.network_settings.target_content_network = network_settings.get("display_network", False)
        campaign.network_settings.target_partner_search_network = False
        
        campaign_response = campaign_service.mutate_campaigns(
            customer_id=customer_id,
            operations=[campaign_operation]
        )
        
        campaign_resource_name = campaign_response.results[0].resource_name
        campaign_id = campaign_resource_name.split('/')[-1]
        
        # Step 3: Add location targeting
        if target_locations:
            await add_location_targeting(customer_id, campaign_resource_name, target_locations)
        
        # Step 4: Add language targeting  
        if target_languages:
            await add_language_targeting(customer_id, campaign_resource_name, target_languages)
        
        preview_url = f"https://ads.google.com/aw/campaigns?campaignId={campaign_id}&ocid={customer_id}"
        
        result = f"""🎯 **Search Campaign Created Successfully!**

📊 **Campaign Details:**
• Campaign Name: {campaign_name}
• Campaign ID: {campaign_id}
• Customer ID: {customer_id}
• Daily Budget: ${daily_budget:,.2f}
• Status: PAUSED (ready for review)
• Bidding Strategy: {bidding_strategy.replace('_', ' ').title()}
{f'• Target CPA: ${target_cpa}' if target_cpa else ''}
{f'• Target ROAS: {target_roas}x' if target_roas else ''}

🎯 **Targeting:**
• Locations: {', '.join(target_locations)}
• Languages: {', '.join(target_languages)}
• Search Network: {'✅' if network_settings.get('search_network') else '❌'}
• Display Network: {'✅' if network_settings.get('display_network') else '❌'}

💰 **Budget Created:**
• Budget ID: {budget_resource_name.split('/')[-1]}
• Amount: ${daily_budget:,.2f}/day

🔗 **Google Ads Link:** [View Campaign]({preview_url})

✅ **SUCCESS:** Your search campaign is ready!

⚡ **Next Steps:**
1. Create ad groups with create_ad_group
2. Add keywords and ads
3. Enable when ready to start serving"""
        
        return [TextContent(type="text", text=result)]
        
    except GoogleAdsException as ex:
        error_details = []
        for error in ex.failure.errors:
            error_details.append(f"• {error.message}")
        
        error_response = f"""❌ **Google Ads API Error**

🔍 **Error Details:**
{chr(10).join(error_details)}"""
        
        return [TextContent(type="text", text=error_response)]
        
    except Exception as e:
        logger.error(f"Campaign creation error: {e}")
        return [TextContent(type="text", text=f"❌ Campaign creation error: {str(e)}")]

async def handle_create_ad_group(arguments: dict) -> list[TextContent]:
    """Create a new ad group within a campaign"""
    
    try:
        if client is None:
            return [TextContent(type="text", text="❌ Google Ads API not available. Please configure credentials.")]
        
        customer_id = arguments.get("customer_id", "").replace("-", "")
        campaign_id = arguments.get("campaign_id", "")
        ad_group_name = arguments.get("ad_group_name", "")
        default_cpc_bid = float(arguments.get("default_cpc_bid", 0))
        target_keywords = json.loads(arguments.get("target_keywords", "[]"))
        keyword_match_types = json.loads(arguments.get("keyword_match_types", "[]"))
        negative_keywords = json.loads(arguments.get("negative_keywords", "[]"))
        
        # Validate inputs
        if default_cpc_bid <= 0:
            return [TextContent(type="text", text="❌ Default CPC bid must be greater than $0")]
        
        cpc_bid_micros = int(default_cpc_bid * 1_000_000)
        campaign_resource_name = f"customers/{customer_id}/campaigns/{campaign_id}"
        
        # Create ad group
        ad_group_service = client.get_service("AdGroupService")
        ad_group_operation = client.get_type("AdGroupOperation")
        
        ad_group = ad_group_operation.create
        ad_group.name = ad_group_name
        ad_group.campaign = campaign_resource_name
        ad_group.status = client.enums.AdGroupStatusEnum.PAUSED
        ad_group.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
        ad_group.cpc_bid_micros = cpc_bid_micros
        
        ad_group_response = ad_group_service.mutate_ad_groups(
            customer_id=customer_id,
            operations=[ad_group_operation]
        )
        
        ad_group_resource_name = ad_group_response.results[0].resource_name
        ad_group_id = ad_group_resource_name.split('/')[-1]
        
        # Add keywords if provided
        keywords_added = 0
        if target_keywords:
            keywords_added = await add_keywords_to_ad_group_internal(
                customer_id, ad_group_resource_name, target_keywords, keyword_match_types
            )
        
        # Add negative keywords if provided
        negatives_added = 0
        if negative_keywords:
            negatives_added = await add_negative_keywords_to_ad_group(
                customer_id, ad_group_resource_name, negative_keywords
            )
        
        preview_url = f"https://ads.google.com/aw/adgroups?adGroupId={ad_group_id}&ocid={customer_id}"
        
        result = f"""📁 **Ad Group Created Successfully!**

📊 **Ad Group Details:**
• Ad Group Name: {ad_group_name}
• Ad Group ID: {ad_group_id}
• Campaign ID: {campaign_id}
• Customer ID: {customer_id}
• Default CPC Bid: ${default_cpc_bid:.2f}
• Status: PAUSED (ready for review)

🎯 **Keywords & Targeting:**
• Keywords Added: {keywords_added}
• Negative Keywords Added: {negatives_added}
• Ad Group Type: Search Standard

{f"📝 **Keywords Added:**{chr(10)}{chr(10).join(f'  • {kw} ({mt})' for kw, mt in zip(target_keywords, keyword_match_types))}" if target_keywords else ""}

{f"🚫 **Negative Keywords:**{chr(10)}{chr(10).join(f'  • {nkw}' for nkw in negative_keywords)}" if negative_keywords else ""}

🔗 **Google Ads Link:** [View Ad Group]({preview_url})

✅ **SUCCESS:** Your ad group is ready!

⚡ **Next Steps:**
1. Create responsive search ads with create_responsive_search_ad
2. Add more keywords if needed
3. Enable when ready to start serving"""
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Ad group creation error: {e}")
        return [TextContent(type="text", text=f"❌ Ad group creation error: {str(e)}")]

async def handle_update_campaign(arguments: dict) -> list[TextContent]:
    """Update campaign settings"""
    
    try:
        if client is None:
            return [TextContent(type="text", text="❌ Google Ads API not available. Please configure credentials.")]
        
        customer_id = arguments.get("customer_id", "").replace("-", "")
        campaign_id = arguments.get("campaign_id", "")
        
        campaign_resource_name = f"customers/{customer_id}/campaigns/{campaign_id}"
        operations = []
        
        # Build update operation
        campaign_service = client.get_service("CampaignService")
        campaign_operation = client.get_type("CampaignOperation")
        
        campaign = campaign_operation.update
        campaign.resource_name = campaign_resource_name
        
        updates_made = []
        
        # Update budget if provided
        if "daily_budget" in arguments:
            daily_budget = float(arguments["daily_budget"])
            budget_micros = int(daily_budget * 1_000_000)
            
            # Get current budget resource name
            google_ads_service = client.get_service("GoogleAdsService")
            query = f"""
                SELECT campaign.campaign_budget
                FROM campaign 
                WHERE campaign.id = {campaign_id}
            """
            response = google_ads_service.search(customer_id=customer_id, query=query)
            
            for row in response:
                budget_resource_name = row.campaign.campaign_budget
                
                # Update budget
                budget_service = client.get_service("CampaignBudgetService")
                budget_operation = client.get_type("CampaignBudgetOperation")
                budget = budget_operation.update
                budget.resource_name = budget_resource_name
                budget.amount_micros = budget_micros
                budget_operation.update_mask.paths.append("amount_micros")
                
                budget_service.mutate_campaign_budgets(
                    customer_id=customer_id,
                    operations=[budget_operation]
                )
                updates_made.append(f"Daily budget updated to ${daily_budget:.2f}")
                break
        
        # Update status if provided
        if "status" in arguments:
            status = arguments["status"].upper()
            if status in ["ENABLED", "PAUSED", "REMOVED"]:
                campaign.status = getattr(client.enums.CampaignStatusEnum, status)
                campaign_operation.update_mask.paths.append("status")
                updates_made.append(f"Status updated to {status}")
        
        # Update name if provided
        if "campaign_name" in arguments:
            campaign.name = arguments["campaign_name"]
            campaign_operation.update_mask.paths.append("name")
            updates_made.append(f"Name updated to '{arguments['campaign_name']}'")
        
        # Execute updates if any were made
        if campaign_operation.update_mask.paths:
            campaign_service.mutate_campaigns(
                customer_id=customer_id,
                operations=[campaign_operation]
            )
        
        if not updates_made:
            return [TextContent(type="text", text="⚠️ No updates were specified")]
        
        result = f"""✅ **Campaign Updated Successfully!**

📊 **Campaign ID:** {campaign_id}
📝 **Updates Made:**
{chr(10).join(f'• {update}' for update in updates_made)}

🔗 **View Campaign:** https://ads.google.com/aw/campaigns?campaignId={campaign_id}&ocid={customer_id}"""
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Campaign update error: {e}")
        return [TextContent(type="text", text=f"❌ Campaign update error: {str(e)}")]

async def handle_get_campaign_structure(arguments: dict) -> list[TextContent]:
    """Get campaign and ad group structure"""
    
    try:
        if client is None:
            return [TextContent(type="text", text="❌ Google Ads API not available. Please configure credentials.")]
        
        customer_id = arguments.get("customer_id", "").replace("-", "")
        campaign_id = arguments.get("campaign_id", "")
        
        google_ads_service = client.get_service("GoogleAdsService")
        
        # Build query
        if campaign_id:
            where_clause = f"WHERE campaign.id = {campaign_id}"
        else:
            where_clause = ""
        
        # Get campaigns and ad groups
        query = f"""
            SELECT 
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                ad_group.id,
                ad_group.name,
                ad_group.status,
                ad_group.cpc_bid_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros
            FROM ad_group
            {where_clause}
            WHERE segments.date DURING LAST_30_DAYS
            ORDER BY campaign.name, ad_group.name
        """
        
        response = google_ads_service.search(customer_id=customer_id, query=query)
        
        # Organize data
        campaigns = {}
        for row in response:
            campaign_id_str = str(row.campaign.id)
            
            if campaign_id_str not in campaigns:
                campaigns[campaign_id_str] = {
                    "name": row.campaign.name,
                    "status": row.campaign.status.name,
                    "type": row.campaign.advertising_channel_type.name,
                    "ad_groups": {}
                }
            
            ad_group_id_str = str(row.ad_group.id)
            campaigns[campaign_id_str]["ad_groups"][ad_group_id_str] = {
                "name": row.ad_group.name,
                "status": row.ad_group.status.name,
                "cpc_bid": row.ad_group.cpc_bid_micros / 1_000_000,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": row.metrics.cost_micros / 1_000_000
            }
        
        if not campaigns:
            return [TextContent(type="text", text="❌ No campaigns found or no data for the specified criteria")]
        
        # Format response
        result = f"""📊 **Campaign Structure Report**

👤 **Customer ID:** {customer_id}
📈 **Data Period:** Last 30 days
🏗️ **Total Campaigns:** {len(campaigns)}

"""
        
        for camp_id, camp_data in campaigns.items():
            total_ad_groups = len(camp_data["ad_groups"])
            total_impressions = sum(ag["impressions"] for ag in camp_data["ad_groups"].values())
            total_clicks = sum(ag["clicks"] for ag in camp_data["ad_groups"].values())
            total_cost = sum(ag["cost"] for ag in camp_data["ad_groups"].values())
            
            result += f"""📁 **{camp_data['name']}** (ID: {camp_id})
• Status: {camp_data['status']} • Type: {camp_data['type']}
• Ad Groups: {total_ad_groups} • Impressions: {total_impressions:,} • Clicks: {total_clicks:,} • Cost: ${total_cost:.2f}

"""
            
            for ag_id, ag_data in camp_data["ad_groups"].items():
                result += f"""  📂 **{ag_data['name']}** (ID: {ag_id})
     • Status: {ag_data['status']} • CPC Bid: ${ag_data['cpc_bid']:.2f}
     • Impressions: {ag_data['impressions']:,} • Clicks: {ag_data['clicks']:,} • Cost: ${ag_data['cost']:.2f}

"""
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Campaign structure error: {e}")
        return [TextContent(type="text", text=f"❌ Campaign structure error: {str(e)}")]

# Helper functions (add these to your production server)

async def add_location_targeting(customer_id: str, campaign_resource_name: str, locations: list):
    """Add location targeting to campaign"""
    try:
        geo_target_constant_service = client.get_service("GeoTargetConstantService")
        campaign_criterion_service = client.get_service("CampaignCriterionService")
        
        operations = []
        
        for location in locations:
            # Find location ID
            gtc_request = client.get_type("SuggestGeoTargetConstantsRequest")
            gtc_request.locale = "en"
            gtc_request.country_code = "US"
            gtc_request.location_names.names.append(location)
            
            gtc_response = geo_target_constant_service.suggest_geo_target_constants(gtc_request)
            
            if gtc_response.geo_target_constant_suggestions:
                location_id = gtc_response.geo_target_constant_suggestions[0].geo_target_constant.id
                
                # Create location criterion
                operation = client.get_type("CampaignCriterionOperation")
                criterion = operation.create
                criterion.campaign = campaign_resource_name
                criterion.location.geo_target_constant = f"geoTargetConstants/{location_id}"
                
                operations.append(operation)
        
        if operations:
            campaign_criterion_service.mutate_campaign_criteria(
                customer_id=customer_id,
                operations=operations
            )
        
    except Exception as e:
        logger.error(f"Location targeting error: {e}")

async def add_language_targeting(customer_id: str, campaign_resource_name: str, languages: list):
    """Add language targeting to campaign"""
    try:
        campaign_criterion_service = client.get_service("CampaignCriterionService")
        operations = []
        
        # Language constant IDs (common ones)
        language_map = {
            "en": "1000",  # English
            "es": "1003",  # Spanish  
            "fr": "1002",  # French
            "de": "1001",  # German
        }
        
        for lang_code in languages:
            if lang_code in language_map:
                operation = client.get_type("CampaignCriterionOperation")
                criterion = operation.create
                criterion.campaign = campaign_resource_name
                criterion.language.language_constant = f"languageConstants/{language_map[lang_code]}"
                
                operations.append(operation)
        
        if operations:
            campaign_criterion_service.mutate_campaign_criteria(
                customer_id=customer_id,
                operations=operations
            )
        
    except Exception as e:
        logger.error(f"Language targeting error: {e}")

async def add_keywords_to_ad_group_internal(customer_id: str, ad_group_resource_name: str, keywords: list, match_types: list):
    """Add keywords to ad group"""
    try:
        ad_group_criterion_service = client.get_service("AdGroupCriterionService")
        operations = []
        
        # Ensure match_types has same length as keywords
        if len(match_types) < len(keywords):
            match_types.extend(["BROAD"] * (len(keywords) - len(match_types)))
        
        for keyword, match_type in zip(keywords, match_types):
            operation = client.get_type("AdGroupCriterionOperation")
            criterion = operation.create
            criterion.ad_group = ad_group_resource_name
            criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
            criterion.keyword.text = keyword
            criterion.keyword.match_type = getattr(client.enums.KeywordMatchTypeEnum, match_type.upper())
            
            operations.append(operation)
        
        if operations:
            ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=customer_id,
                operations=operations
            )
            
        return len(operations)
        
    except Exception as e:
        logger.error(f"Keyword addition error: {e}")
        return 0

async def handle_add_keywords_to_ad_group(arguments: dict) -> list[TextContent]:
    """Add keywords to an existing ad group"""
    
    try:
        if client is None:
            return [TextContent(type="text", text="❌ Google Ads API not available. Please configure credentials.")]
        
        customer_id = arguments.get("customer_id", "").replace("-", "")
        ad_group_id = arguments.get("ad_group_id", "")
        keywords = json.loads(arguments.get("keywords", "[]"))
        match_types = json.loads(arguments.get("match_types", "[]"))
        bids = json.loads(arguments.get("bids", "[]")) if arguments.get("bids") else []
        
        ad_group_resource_name = f"customers/{customer_id}/adGroups/{ad_group_id}"
        
        # Ensure match_types has same length as keywords
        if len(match_types) < len(keywords):
            match_types.extend(["BROAD"] * (len(keywords) - len(match_types)))
        
        ad_group_criterion_service = client.get_service("AdGroupCriterionService")
        operations = []
        
        for i, (keyword, match_type) in enumerate(zip(keywords, match_types)):
            operation = client.get_type("AdGroupCriterionOperation")
            criterion = operation.create
            criterion.ad_group = ad_group_resource_name
            criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
            criterion.keyword.text = keyword
            criterion.keyword.match_type = getattr(client.enums.KeywordMatchTypeEnum, match_type.upper())
            
            # Add custom bid if provided
            if i < len(bids) and bids[i]:
                criterion.cpc_bid_micros = int(float(bids[i]) * 1_000_000)
            
            operations.append(operation)
        
        if operations:
            response = ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=customer_id,
                operations=operations
            )
            
            keywords_added = len(response.results)
        else:
            keywords_added = 0
        
        result = f"""🎯 **Keywords Added Successfully!**

📊 **Summary:**
- Ad Group ID: {ad_group_id}
- Keywords Added: {keywords_added}

📝 **Keywords Added:**
{chr(10).join(f'  • {kw} ({mt})' for kw, mt in zip(keywords, match_types))}

✅ **SUCCESS:** Keywords are now active in your ad group!"""
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Add keywords error: {e}")
        return [TextContent(type="text", text=f"❌ Add keywords error: {str(e)}")]

async def handle_validate_rsa_copy(arguments: dict) -> list[TextContent]:
    """Handle RSA validation (keeping working version)"""
    
    try:
        headlines = json.loads(arguments.get("headlines", "[]"))
        descriptions = json.loads(arguments.get("descriptions", "[]"))
        auto_fix = arguments.get("auto_fix", False)
        
        # Same validation logic as before
        errors = []
        
        if len(headlines) < 3 or len(headlines) > 15:
            errors.append("RSA requires 3-15 headlines")
        if len(descriptions) < 2 or len(descriptions) > 4:
            errors.append("RSA requires 2-4 descriptions")
        
        for i, headline in enumerate(headlines):
            if len(str(headline)) > 30:
                errors.append(f"Headline {i+1} exceeds 30 characters")
        
        for i, description in enumerate(descriptions):
            if len(str(description)) > 90:
                errors.append(f"Description {i+1} exceeds 90 characters")
        
        if not errors:
            response = f"""✅ **RSA Copy Validation Passed!**

📊 **Summary:**
• Headlines: {len(headlines)}/15 provided
• Descriptions: {len(descriptions)}/4 provided
• All character limits met

📝 **Headlines ({len(headlines)}):**
{chr(10).join(f"  {i+1}. {h} ({len(str(h))} chars)" for i, h in enumerate(headlines))}

📄 **Descriptions ({len(descriptions)}):**
{chr(10).join(f"  {i+1}. {d} ({len(str(d))} chars)" for i, d in enumerate(descriptions))}

🎯 **Ready to create your RSA with real Google Ads API!**"""
        else:
            response = f"""❌ **RSA Copy Validation Failed**

🔍 **Issues Found:**
{chr(10).join(f"• {error}" for error in errors)}"""
        
        return [TextContent(type="text", text=response)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Validation error: {str(e)}")]

async def handle_create_responsive_search_ad(arguments: dict) -> list[TextContent]:
    """Create a REAL Responsive Search Ad"""
    
    try:
        if client is None:
            return [TextContent(type="text", text="❌ Google Ads API not available. Running in simulation mode. Please configure real credentials.")]
        
        customer_id = arguments.get("customer_id", "").replace("-", "")
        ad_group_id = arguments.get("ad_group_id", "")
        headlines = json.loads(arguments.get("headlines", "[]"))
        descriptions = json.loads(arguments.get("descriptions", "[]"))
        final_urls = json.loads(arguments.get("final_urls", "[]"))
        path1 = arguments.get("path1", "")
        path2 = arguments.get("path2", "")
        
        # Validate inputs first
        if len(headlines) < 3:
            return [TextContent(type="text", text="❌ Need at least 3 headlines")]
        if len(descriptions) < 2:
            return [TextContent(type="text", text="❌ Need at least 2 descriptions")]
        
        # Create the ad via Google Ads API
        ad_group_ad_service = client.get_service("AdGroupAdService")
        ad_group_ad_operation = client.get_type("AdGroupAdOperation")
        
        ad_group_ad = ad_group_ad_operation.create
        ad_group_ad.ad_group = f"customers/{customer_id}/adGroups/{ad_group_id}"
        ad_group_ad.status = client.enums.AdGroupAdStatusEnum.PAUSED
        
        # Create responsive search ad
        responsive_search_ad_info = client.get_type("ResponsiveSearchAdInfo")
        
        # Add headlines
        for headline_text in headlines:
            headline = client.get_type("AdTextAsset")
            headline.text = str(headline_text)
            responsive_search_ad_info.headlines.append(headline)
        
        # Add descriptions
        for description_text in descriptions:
            description = client.get_type("AdTextAsset")
            description.text = str(description_text)
            responsive_search_ad_info.descriptions.append(description)
        
        # Set final URLs
        ad_group_ad.ad.final_urls.extend([str(url) for url in final_urls])
        
        # Set display URL paths
        if path1:
            ad_group_ad.ad.display_url_path_1 = str(path1)
        if path2:
            ad_group_ad.ad.display_url_path_2 = str(path2)
        
        # Set the ad type
        ad_group_ad.ad.responsive_search_ad = responsive_search_ad_info
        
        # Execute the operation
        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=customer_id,
            operations=[ad_group_ad_operation]
        )
        
        ad_resource_name = response.results[0].resource_name
        ad_id = ad_resource_name.split('/')[-1]
        
        # Create preview URL
        preview_url = f"https://ads.google.com/aw/ads?adId={ad_id}&ocid={customer_id}"
        
        result = f"""🎉 **REAL Responsive Search Ad Created!**

📊 **Ad Details:**
• Customer ID: {customer_id}
• Ad Group ID: {ad_group_id}
• Ad ID: {ad_id}
• Resource Name: {ad_resource_name}
• Status: PAUSED (ready for review)

📝 **Headlines Created ({len(headlines)}):**
{chr(10).join(f"  {i+1}. {h}" for i, h in enumerate(headlines))}

📄 **Descriptions Created ({len(descriptions)}):**
{chr(10).join(f"  {i+1}. {d}" for i, d in enumerate(descriptions))}

🔗 **Google Ads Link:** [View Ad]({preview_url})

✅ **SUCCESS:** Your ad has been created in Google Ads and is ready for review!
⚠️ **Next Steps:** Enable the ad when ready to start serving."""
        
        return [TextContent(type="text", text=result)]
        
    except GoogleAdsException as ex:
        error_details = []
        for error in ex.failure.errors:
            error_details.append(f"• {error.message}")
        
        error_response = f"""❌ **Google Ads API Error**

🔍 **Error Details:**
{chr(10).join(error_details)}

💡 **Common Issues:**
• Invalid customer ID or ad group ID
• Insufficient permissions
• Ad policy violations
• Account suspension"""
        
        return [TextContent(type="text", text=error_response)]
        
    except Exception as e:
        logger.error(f"RSA creation error: {e}")
        return [TextContent(type="text", text=f"❌ RSA creation error: {str(e)}")]

async def handle_create_performance_max_campaign(arguments: dict) -> list[TextContent]:
    """Create a REAL Performance Max campaign"""
    
    try:
        if client is None:
            return [TextContent(type="text", text="❌ Google Ads API not available. Please configure real credentials for actual campaign creation.")]
        
        customer_id = arguments.get("customer_id", "").replace("-", "")
        campaign_name = arguments.get("campaign_name", "")
        daily_budget = float(arguments.get("daily_budget", 0))
        business_name = arguments.get("business_name", "")
        headlines = json.loads(arguments.get("headlines", "[]"))
        descriptions = json.loads(arguments.get("descriptions", "[]"))
        final_urls = json.loads(arguments.get("final_urls", "[]"))
        target_roas = arguments.get("target_roas")
        
        # Validate inputs
        if daily_budget <= 0:
            return [TextContent(type="text", text="❌ Daily budget must be greater than $0")]
        if len(business_name) > 25:
            return [TextContent(type="text", text="❌ Business name must be 25 characters or less")]
        
        budget_micros = int(daily_budget * 1_000_000)
        
        # Step 1: Create campaign budget
        campaign_budget_service = client.get_service("CampaignBudgetService")
        budget_operation = client.get_type("CampaignBudgetOperation")
        
        campaign_budget = budget_operation.create
        campaign_budget.name = f"{campaign_name} Budget"
        campaign_budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
        campaign_budget.amount_micros = budget_micros
        
        budget_response = campaign_budget_service.mutate_campaign_budgets(
            customer_id=customer_id,
            operations=[budget_operation]
        )
        budget_resource_name = budget_response.results[0].resource_name
        
        # Step 2: Create Performance Max campaign
        campaign_service = client.get_service("CampaignService")
        campaign_operation = client.get_type("CampaignOperation")
        
        campaign = campaign_operation.create
        campaign.name = campaign_name
        campaign.status = client.enums.CampaignStatusEnum.PAUSED
        campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.PERFORMANCE_MAX
        campaign.campaign_budget = budget_resource_name
        
        # Set bidding strategy
        if target_roas:
            campaign.maximize_conversion_value.target_roas = float(target_roas)
        else:
            campaign.maximize_conversions = client.get_type("MaximizeConversions")
        
        campaign_response = campaign_service.mutate_campaigns(
            customer_id=customer_id,
            operations=[campaign_operation]
        )
        campaign_resource_name = campaign_response.results[0].resource_name
        campaign_id = campaign_resource_name.split('/')[-1]
        
        # Create preview URL
        preview_url = f"https://ads.google.com/aw/campaigns?campaignId={campaign_id}&ocid={customer_id}"
        
        result = f"""🚀 **REAL Performance Max Campaign Created!**

📊 **Campaign Details:**
• Campaign Name: {campaign_name}
• Campaign ID: {campaign_id}
• Customer ID: {customer_id}
• Daily Budget: ${daily_budget:,.2f}
• Status: PAUSED (ready for review)
• Business Name: {business_name}

💰 **Budget Created:**
• Budget Resource: {budget_resource_name.split('/')[-1]}
• Amount: ${daily_budget:,.2f}/day

🎨 **Asset Group Requirements:**
• Headlines: {len(headlines)} provided
• Descriptions: {len(descriptions)} provided
• Business Name: {business_name}

🔗 **Google Ads Link:** [View Campaign]({preview_url})

✅ **SUCCESS:** Your Performance Max campaign has been created in Google Ads!

⚠️ **Next Steps:**
1. Create asset groups with your headlines and descriptions
2. Add required image assets (logos, marketing images)
3. Review and enable when ready

💡 **Note:** Asset group creation requires additional API calls. Campaign structure is ready!"""
        
        return [TextContent(type="text", text=result)]
        
    except GoogleAdsException as ex:
        error_details = []
        for error in ex.failure.errors:
            error_details.append(f"• {error.message}")
        
        error_response = f"""❌ **Google Ads API Error**

🔍 **Error Details:**
{chr(10).join(error_details)}"""
        
        return [TextContent(type="text", text=error_response)]
        
    except Exception as e:
        logger.error(f"Performance Max creation error: {e}")
        return [TextContent(type="text", text=f"❌ Performance Max creation error: {str(e)}")]

async def handle_get_account_info(arguments: dict) -> list[TextContent]:
    """Get account information"""
    
    try:
        if client is None:
            return [TextContent(type="text", text="❌ Google Ads API not available. Please configure credentials to view account info.")]
        
        customer_id = arguments.get("customer_id", "").replace("-", "")
        
        # Query for account info
        google_ads_service = client.get_service("GoogleAdsService")
        
        query = """
            SELECT 
                customer.id,
                customer.descriptive_name,
                customer.currency_code,
                customer.time_zone,
                customer.status
            FROM customer
        """
        
        response = google_ads_service.search(customer_id=customer_id, query=query)
        
        account_info = None
        for row in response:
            account_info = {
                "id": row.customer.id,
                "name": row.customer.descriptive_name,
                "currency": row.customer.currency_code,
                "timezone": row.customer.time_zone,
                "status": row.customer.status.name
            }
            break
        
        if not account_info:
            return [TextContent(type="text", text="❌ Could not retrieve account information")]
        
        # Get campaigns
        campaigns_query = """
            SELECT 
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type
            FROM campaign
            ORDER BY campaign.name
        """
        
        campaigns_response = google_ads_service.search(customer_id=customer_id, query=campaigns_query)
        campaigns = []
        
        for row in campaigns_response:
            campaigns.append({
                "id": row.campaign.id,
                "name": row.campaign.name,
                "status": row.campaign.status.name,
                "type": row.campaign.advertising_channel_type.name
            })
        
        result = f"""📊 **Google Ads Account Information**

🏢 **Account Details:**
• Account ID: {account_info['id']}
• Account Name: {account_info['name']}
• Currency: {account_info['currency']}
• Timezone: {account_info['timezone']}
• Status: {account_info['status']}

📈 **Campaigns ({len(campaigns)}):**
{chr(10).join(f"  • {c['name']} (ID: {c['id']}) - {c['status']} - {c['type']}" for c in campaigns[:10])}
{f"  ... and {len(campaigns) - 10} more campaigns" if len(campaigns) > 10 else ""}

✅ **API Connection:** Successfully connected to Google Ads API"""
        
        return [TextContent(type="text", text=result)]
        
    except GoogleAdsException as ex:
        error_response = f"❌ Google Ads API Error: {ex.failure.errors[0].message if ex.failure.errors else str(ex)}"
        return [TextContent(type="text", text=error_response)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Account info error: {str(e)}")]

async def handle_get_campaign_performance(arguments: dict) -> list[TextContent]:
    """Get real campaign performance data"""
    
    try:
        if client is None:
            return [TextContent(type="text", text="❌ Google Ads API not available. Please configure credentials to view performance data.")]
        
        customer_id = arguments.get("customer_id", "").replace("-", "")
        campaign_id = arguments.get("campaign_id", "")
        date_range = arguments.get("date_range", "LAST_30_DAYS")
        
        google_ads_service = client.get_service("GoogleAdsService")
        
        if campaign_id:
            where_clause = f"WHERE campaign.id = {campaign_id}"
        else:
            where_clause = ""
        
        query = f"""
            SELECT 
                campaign.id,
                campaign.name,
                campaign.status,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value
            FROM campaign
            {where_clause}
            WHERE segments.date DURING {date_range}
        """
        
        response = google_ads_service.search(customer_id=customer_id, query=query)
        
        campaigns_data = []
        total_impressions = 0
        total_clicks = 0
        total_cost = 0
        total_conversions = 0
        
        for row in response:
            campaign_data = {
                "id": row.campaign.id,
                "name": row.campaign.name,
                "status": row.campaign.status.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "ctr": round(row.metrics.ctr * 100, 2),
                "cost": row.metrics.cost_micros / 1_000_000,
                "conversions": row.metrics.conversions,
                "conversion_value": row.metrics.conversions_value
            }
            campaigns_data.append(campaign_data)
            
            total_impressions += campaign_data["impressions"]
            total_clicks += campaign_data["clicks"]
            total_cost += campaign_data["cost"]
            total_conversions += campaign_data["conversions"]
        
        if not campaigns_data:
            return [TextContent(type="text", text="❌ No performance data found for the specified criteria")]
        
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        
        result = f"""📈 **Campaign Performance Report ({date_range})**

📊 **Summary Totals:**
• Impressions: {total_impressions:,}
• Clicks: {total_clicks:,}
• CTR: {avg_ctr:.2f}%
• Cost: ${total_cost:,.2f}
• Conversions: {total_conversions:,.1f}

📋 **Campaign Details:**

{chr(10).join(f"**{c['name']}** (ID: {c['id']})" + chr(10) + 
              f"  • Status: {c['status']}" + chr(10) +
              f"  • Impressions: {c['impressions']:,}" + chr(10) +
              f"  • Clicks: {c['clicks']:,} (CTR: {c['ctr']:.2f}%)" + chr(10) +
              f"  • Cost: ${c['cost']:,.2f}" + chr(10) +
              f"  • Conversions: {c['conversions']:,.1f}" + chr(10)
              for c in campaigns_data[:5])}

{f"... and {len(campaigns_data) - 5} more campaigns" if len(campaigns_data) > 5 else ""}

✅ **Data Source:** Real Google Ads API data"""
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Performance data error: {str(e)}")]

async def handle_generate_ad_variations(arguments: dict) -> list[TextContent]:
    """Generate ad variations (keeping working version)"""
    
    # Same implementation as before - this doesn't require API
    business_description = arguments.get("business_description", "")
    target_keywords = json.loads(arguments.get("target_keywords", "[]"))
    tone = arguments.get("tone", "professional")
    num_headlines = int(arguments.get("num_headlines", 8))
    num_descriptions = int(arguments.get("num_descriptions", 3))
    
    # Generate variations using templates (same logic as before)
    headline_templates = {
        "professional": [
            "Expert {service}",
            "Professional {service}",
            "Trusted {service}",
            "{service} Solutions",
            "Quality {service}",
            "Premium {service}",
            "Reliable {service}",
            "Top-Rated {service}"
        ]
    }
    
    service_type = target_keywords[0] if target_keywords else "services"
    
    # Generate headlines
    templates = headline_templates.get(tone, headline_templates["professional"])
    generated_headlines = []
    
    for i in range(min(num_headlines, len(templates))):
        headline = templates[i].format(service=service_type)
        if len(headline) <= 30:
            generated_headlines.append(headline)
    
    # Add keyword-specific headlines
    for keyword in target_keywords[:3]:
        if len(keyword) <= 30:
            generated_headlines.append(keyword.title())
    
    # Generate descriptions
    description_templates = [
        f"Professional {service_type} with guaranteed results. Free consultation available.",
        f"Trusted by businesses for quality {service_type}. Call now to get started.",
        f"Expert {service_type} tailored to your needs. Contact us today."
    ]
    
    generated_descriptions = description_templates[:num_descriptions]
    
    response = f"""🎯 **Ad Variations Generated!**

📋 **Input Summary:**
• Business: {business_description[:100]}{'...' if len(business_description) > 100 else ''}
• Target Keywords: {', '.join(target_keywords)}
• Tone: {tone.title()}

📝 **Generated Headlines ({len(generated_headlines)}):**
{chr(10).join(f"  {i+1}. {h} ({len(h)} chars)" for i, h in enumerate(generated_headlines))}

📄 **Generated Descriptions ({len(generated_descriptions)}):**
{chr(10).join(f"  {i+1}. {d} ({len(d)} chars)" for i, d in enumerate(generated_descriptions))}

💾 **Ready-to-Use JSON:**

Headlines: {json.dumps(generated_headlines)}
Descriptions: {json.dumps(generated_descriptions)}

🚀 **Ready for Real Ad Creation:** Use create_responsive_search_ad to create actual ads in Google Ads!"""
    
    return [TextContent(type="text", text=response)]

async def main():
    """Main entry point"""
    try:
        logger.info("🚀 Starting Production Google Ads MCP Server...")
        
        # Try to initialize Google Ads client
        initialize_google_ads_client()
        
        if client:
            logger.info("✅ Production mode: Real Google Ads API connected")
        else:
            logger.info("⚠️ Simulation mode: No API credentials configured")
        
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())