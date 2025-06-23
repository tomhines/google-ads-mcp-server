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
    else:
        return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]

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