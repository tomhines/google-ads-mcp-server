#!/usr/bin/env python3
"""
Expanded Enhanced Google Ads MCP Server
Complete toolkit for ad creation and validation
"""

import asyncio
import json
import logging
from pathlib import Path
import sys
import random
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server
server = Server("google-ads-expanded")

# Define tools
TOOLS = [
    Tool(
        name="validate_rsa_copy",
        description="Validate RSA headlines and descriptions for character limits and requirements.",
        inputSchema={
            "type": "object",
            "properties": {
                "headlines": {
                    "type": "string",
                    "description": "JSON array of headlines to validate"
                },
                "descriptions": {
                    "type": "string", 
                    "description": "JSON array of descriptions to validate"
                },
                "auto_fix": {
                    "type": "boolean",
                    "description": "Whether to automatically fix character limit issues"
                }
            },
            "required": ["headlines", "descriptions"]
        }
    ),
    Tool(
        name="create_rsa_simulation",
        description="Simulate creating a Responsive Search Ad with validation and preview. Shows what the ad would look like when created.",
        inputSchema={
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Google Ads customer ID (format: 123-456-7890)"
                },
                "ad_group_id": {
                    "type": "string",
                    "description": "Ad group ID where ad would be created"
                },
                "headlines": {
                    "type": "string",
                    "description": "JSON array of headlines (3-15 required)"
                },
                "descriptions": {
                    "type": "string",
                    "description": "JSON array of descriptions (2-4 required)"
                },
                "final_urls": {
                    "type": "string",
                    "description": "JSON array of final URLs"
                },
                "path1": {
                    "type": "string",
                    "description": "Optional display URL path 1"
                },
                "path2": {
                    "type": "string",
                    "description": "Optional display URL path 2"
                }
            },
            "required": ["customer_id", "ad_group_id", "headlines", "descriptions", "final_urls"]
        }
    ),
    Tool(
        name="generate_ad_variations",
        description="Generate multiple variations of ad copy based on a business description and target keywords.",
        inputSchema={
            "type": "object",
            "properties": {
                "business_description": {
                    "type": "string",
                    "description": "Description of the business and its services"
                },
                "target_keywords": {
                    "type": "string",
                    "description": "JSON array of target keywords to include"
                },
                "tone": {
                    "type": "string",
                    "description": "Tone of voice: professional, casual, urgent, friendly"
                },
                "num_headlines": {
                    "type": "number",
                    "description": "Number of headlines to generate (3-15)"
                },
                "num_descriptions": {
                    "type": "number",
                    "description": "Number of descriptions to generate (2-4)"
                }
            },
            "required": ["business_description", "target_keywords"]
        }
    ),
    Tool(
        name="validate_pmax_assets",
        description="Validate assets for Performance Max campaigns including headlines, descriptions, and business info.",
        inputSchema={
            "type": "object",
            "properties": {
                "campaign_name": {
                    "type": "string",
                    "description": "Name for the Performance Max campaign"
                },
                "business_name": {
                    "type": "string",
                    "description": "Business name (max 25 characters)"
                },
                "headlines": {
                    "type": "string",
                    "description": "JSON array of headlines for asset group"
                },
                "descriptions": {
                    "type": "string",
                    "description": "JSON array of descriptions for asset group"
                },
                "final_urls": {
                    "type": "string",
                    "description": "JSON array of final URLs"
                },
                "daily_budget": {
                    "type": "number",
                    "description": "Daily budget in dollars"
                }
            },
            "required": ["campaign_name", "business_name", "headlines", "descriptions", "final_urls", "daily_budget"]
        }
    ),
    Tool(
        name="bulk_validate_campaigns",
        description="Validate multiple campaigns and ad groups at once. Perfect for account buildouts.",
        inputSchema={
            "type": "object",
            "properties": {
                "campaigns_data": {
                    "type": "string",
                    "description": "JSON array of campaign objects with headlines, descriptions, etc."
                }
            },
            "required": ["campaigns_data"]
        }
    ),
    Tool(
        name="analyze_ad_strength",
        description="Analyze ad strength and provide recommendations for improvement based on Google's ad strength criteria.",
        inputSchema={
            "type": "object",
            "properties": {
                "headlines": {
                    "type": "string",
                    "description": "JSON array of headlines to analyze"
                },
                "descriptions": {
                    "type": "string",
                    "description": "JSON array of descriptions to analyze"
                },
                "target_keywords": {
                    "type": "string",
                    "description": "JSON array of target keywords"
                }
            },
            "required": ["headlines", "descriptions"]
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
    
    if name == "validate_rsa_copy":
        return await handle_validate_rsa_copy(arguments)
    elif name == "create_rsa_simulation":
        return await handle_create_rsa_simulation(arguments)
    elif name == "generate_ad_variations":
        return await handle_generate_ad_variations(arguments)
    elif name == "validate_pmax_assets":
        return await handle_validate_pmax_assets(arguments)
    elif name == "bulk_validate_campaigns":
        return await handle_bulk_validate_campaigns(arguments)
    elif name == "analyze_ad_strength":
        return await handle_analyze_ad_strength(arguments)
    else:
        return [TextContent(
            type="text", 
            text=f"❌ Unknown tool: {name}"
        )]

async def handle_validate_rsa_copy(arguments: dict) -> list[TextContent]:
    """Handle RSA validation - keeping the working version"""
    
    try:
        # Extract arguments
        headlines = arguments.get("headlines", "")
        descriptions = arguments.get("descriptions", "")
        auto_fix = arguments.get("auto_fix", False)
        
        # Parse JSON inputs
        headlines_list = json.loads(headlines)
        descriptions_list = json.loads(descriptions)
        
        if not isinstance(headlines_list, list) or not isinstance(descriptions_list, list):
            raise ValueError("Headlines and descriptions must be JSON arrays")
        
        # Validation logic
        errors = []
        
        # Check headline count
        if len(headlines_list) < 3:
            errors.append("RSA requires at least 3 headlines")
        elif len(headlines_list) > 15:
            errors.append("RSA allows maximum 15 headlines")
        
        # Check description count  
        if len(descriptions_list) < 2:
            errors.append("RSA requires at least 2 descriptions")
        elif len(descriptions_list) > 4:
            errors.append("RSA allows maximum 4 descriptions")
        
        # Check character limits
        for i, headline in enumerate(headlines_list):
            if len(str(headline)) > 30:
                errors.append(f"Headline {i+1} exceeds 30 characters: '{headline}' ({len(str(headline))} chars)")
        
        for i, description in enumerate(descriptions_list):
            if len(str(description)) > 90:
                errors.append(f"Description {i+1} exceeds 90 characters ({len(str(description))} chars)")
        
        # Check for duplicates
        if len(set(headlines_list)) != len(headlines_list):
            errors.append("Headlines must be unique")
        if len(set(descriptions_list)) != len(descriptions_list):
            errors.append("Descriptions must be unique")
        
        # Build response
        if not errors:
            response = f"""✅ **RSA Copy Validation Passed!**

📊 **Summary:**
• Headlines: {len(headlines_list)}/15 provided
• Descriptions: {len(descriptions_list)}/4 provided
• All character limits met
• All content is unique

📝 **Headlines ({len(headlines_list)}):**
{chr(10).join(f"  {i+1}. {h} ({len(str(h))} chars)" for i, h in enumerate(headlines_list))}

📄 **Descriptions ({len(descriptions_list)}):**
{chr(10).join(f"  {i+1}. {d} ({len(str(d))} chars)" for i, d in enumerate(descriptions_list))}

🎯 **Ready to create your RSA!**

💡 **Optimization Tips:**
• Consider adding more headlines (up to 15 total) for better performance
• Google recommends at least 8-10 headlines for optimal results
• You could add 1-2 more descriptions for variety"""
        
        else:
            if auto_fix:
                # Auto-fix character limits
                fixed_headlines = [str(h)[:27] + "..." if len(str(h)) > 30 else str(h) for h in headlines_list]
                fixed_descriptions = [str(d)[:87] + "..." if len(str(d)) > 90 else str(d) for d in descriptions_list]
                
                response = f"""🔧 **RSA Copy Validation with Auto-Fix**

❌ **Original Issues:**
{chr(10).join(f"• {error}" for error in errors)}

✅ **Auto-Fixed Copy:**

📝 **Fixed Headlines:**
{chr(10).join(f"  {i+1}. {h} ({len(h)} chars)" for i, h in enumerate(fixed_headlines))}

📄 **Fixed Descriptions:**
{chr(10).join(f"  {i+1}. {d} ({len(d)} chars)" for i, d in enumerate(fixed_descriptions))}

💡 **Use this JSON for your RSA:**
Headlines: {json.dumps(fixed_headlines)}
Descriptions: {json.dumps(fixed_descriptions)}"""
            else:
                response = f"""❌ **RSA Copy Validation Failed**

🔍 **Issues Found ({len(errors)}):**
{chr(10).join(f"• {error}" for error in errors)}

💡 **Recommendations:**
• Shorten headlines to 30 characters or less
• Shorten descriptions to 90 characters or less  
• Make sure you have 3-15 unique headlines
• Make sure you have 2-4 unique descriptions
• Use auto_fix=true to automatically fix character limits"""
        
        return [TextContent(type="text", text=response)]
        
    except json.JSONDecodeError as e:
        error_response = f"""❌ **JSON Parsing Error**

Error: {str(e)}

💡 **Expected Format:**
• headlines: ["Headline 1", "Headline 2", "Headline 3"]
• descriptions: ["Description 1", "Description 2"]"""
        
        return [TextContent(type="text", text=error_response)]
    
    except Exception as e:
        logger.error(f"Validation error: {e}")
        error_response = f"❌ Validation error: {str(e)}"
        return [TextContent(type="text", text=error_response)]

async def handle_create_rsa_simulation(arguments: dict) -> list[TextContent]:
    """Simulate creating an RSA with preview"""
    
    try:
        customer_id = arguments.get("customer_id", "")
        ad_group_id = arguments.get("ad_group_id", "")
        headlines = json.loads(arguments.get("headlines", "[]"))
        descriptions = json.loads(arguments.get("descriptions", "[]"))
        final_urls = json.loads(arguments.get("final_urls", "[]"))
        path1 = arguments.get("path1", "")
        path2 = arguments.get("path2", "")
        
        # Validate first
        validation_errors = []
        
        if len(headlines) < 3 or len(headlines) > 15:
            validation_errors.append("Need 3-15 headlines")
        if len(descriptions) < 2 or len(descriptions) > 4:
            validation_errors.append("Need 2-4 descriptions")
        if not final_urls:
            validation_errors.append("Need at least one final URL")
        
        if validation_errors:
            response = f"""❌ **RSA Creation Failed**

🔍 **Validation Errors:**
{chr(10).join(f"• {error}" for error in validation_errors)}

💡 **Use the validate_rsa_copy tool first to fix these issues.**"""
        else:
            # Generate preview combinations
            preview_ads = []
            for i in range(3):  # Show 3 preview combinations
                selected_headlines = random.sample(headlines, min(3, len(headlines)))
                selected_descriptions = random.sample(descriptions, min(2, len(descriptions)))
                
                # Create display URL
                base_url = final_urls[0].replace("https://", "").replace("http://", "")
                if "/" in base_url:
                    base_url = base_url.split("/")[0]
                
                display_url = base_url
                if path1:
                    display_url += f"/{path1}"
                if path2:
                    display_url += f"/{path2}"
                
                preview_ads.append({
                    "headlines": selected_headlines,
                    "descriptions": selected_descriptions,
                    "display_url": display_url
                })
            
            # Generate mock ad ID
            mock_ad_id = f"ad_{random.randint(100000, 999999)}"
            
            response = f"""🎉 **RSA Created Successfully (Simulation)!**

📊 **Ad Details:**
• Customer ID: {customer_id}
• Ad Group ID: {ad_group_id}
• Ad ID: {mock_ad_id}
• Headlines: {len(headlines)} provided
• Descriptions: {len(descriptions)} provided
• Status: PAUSED (ready for review)

📝 **All Headlines:**
{chr(10).join(f"  {i+1}. {h}" for i, h in enumerate(headlines))}

📄 **All Descriptions:**
{chr(10).join(f"  {i+1}. {d}" for i, d in enumerate(descriptions))}

🎯 **Preview Ad Combinations:**
Google will automatically test different combinations. Here are 3 examples:

**Preview 1:**
{preview_ads[0]['headlines'][0]}
{preview_ads[0]['headlines'][1]}
{preview_ads[0]['headlines'][2]}
{preview_ads[0]['descriptions'][0]} {preview_ads[0]['descriptions'][1]}
{preview_ads[0]['display_url']}

**Preview 2:**
{preview_ads[1]['headlines'][0]}
{preview_ads[1]['headlines'][1]}
{preview_ads[1]['headlines'][2]}
{preview_ads[1]['descriptions'][0]} {preview_ads[1]['descriptions'][1]}
{preview_ads[1]['display_url']}

**Preview 3:**
{preview_ads[2]['headlines'][0]}
{preview_ads[2]['headlines'][1]}
{preview_ads[2]['headlines'][2]}
{preview_ads[2]['descriptions'][0]} {preview_ads[2]['descriptions'][1]}
{preview_ads[2]['display_url']}

⚠️ **Development Mode:** No actual ad was created. Connect real Google Ads API credentials to create live ads."""
        
        return [TextContent(type="text", text=response)]
        
    except Exception as e:
        logger.error(f"RSA simulation error: {e}")
        error_response = f"❌ RSA simulation error: {str(e)}"
        return [TextContent(type="text", text=error_response)]

async def handle_generate_ad_variations(arguments: dict) -> list[TextContent]:
    """Generate ad copy variations based on business info"""
    
    try:
        business_description = arguments.get("business_description", "")
        target_keywords = json.loads(arguments.get("target_keywords", "[]"))
        tone = arguments.get("tone", "professional")
        num_headlines = int(arguments.get("num_headlines", 8))
        num_descriptions = int(arguments.get("num_descriptions", 3))
        
        # Generate headlines based on patterns
        headline_templates = {
            "professional": [
                "Expert {service}",
                "Professional {service}",
                "Trusted {service}",
                "{service} Solutions",
                "Quality {service}",
                "Premium {service}",
                "Reliable {service}",
                "Top-Rated {service}",
                "Certified {service}",
                "Leading {service}"
            ],
            "urgent": [
                "Call Now - {service}",
                "Limited Time {service}",
                "Act Fast - {service}",
                "Don't Wait - {service}",
                "Urgent {service}",
                "Today Only {service}",
                "Quick {service}",
                "Fast {service}",
                "Immediate {service}",
                "Same Day {service}"
            ],
            "casual": [
                "Great {service}",
                "Amazing {service}",
                "Awesome {service}",
                "Your {service} Experts",
                "We Do {service}",
                "Best {service} Around",
                "Local {service}",
                "Friendly {service}",
                "Easy {service}",
                "Simple {service}"
            ]
        }
        
        description_templates = {
            "professional": [
                "Get expert {service} from our certified professionals. Contact us today for a consultation.",
                "Professional {service} with guaranteed results. Free estimates available.",
                "Trusted by businesses for quality {service}. Call now to get started.",
                "Expert {service} tailored to your needs. Professional service guaranteed."
            ],
            "urgent": [
                "Need {service} now? Call today for immediate service and fast results.",
                "Don't wait! Get {service} today. Limited time offer available.",
                "Quick {service} when you need it most. Call now for same-day service.",
                "Fast, reliable {service}. Contact us now for immediate assistance."
            ],
            "casual": [
                "Looking for great {service}? We've got you covered. Give us a call!",
                "Friendly, reliable {service} that you can trust. Get your free quote today.",
                "We make {service} easy and affordable. Contact us to learn more.",
                "Quality {service} without the hassle. Call us for a free consultation."
            ]
        }
        
        # Extract service type from business description or use first keyword
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
        desc_templates = description_templates.get(tone, description_templates["professional"])
        generated_descriptions = []
        
        for i in range(min(num_descriptions, len(desc_templates))):
            description = desc_templates[i].format(service=service_type)
            if len(description) <= 90:
                generated_descriptions.append(description)
        
        # Trim to requested counts
        generated_headlines = generated_headlines[:num_headlines]
        generated_descriptions = generated_descriptions[:num_descriptions]
        
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

💡 **Next Steps:**
• Use validate_rsa_copy to check these variations
• Use create_rsa_simulation to preview how they'll look
• Customize any headlines/descriptions as needed"""
        
        return [TextContent(type="text", text=response)]
        
    except Exception as e:
        logger.error(f"Ad generation error: {e}")
        error_response = f"❌ Ad generation error: {str(e)}"
        return [TextContent(type="text", text=error_response)]

async def handle_validate_pmax_assets(arguments: dict) -> list[TextContent]:
    """Validate Performance Max campaign assets"""
    
    try:
        campaign_name = arguments.get("campaign_name", "")
        business_name = arguments.get("business_name", "")
        headlines = json.loads(arguments.get("headlines", "[]"))
        descriptions = json.loads(arguments.get("descriptions", "[]"))
        final_urls = json.loads(arguments.get("final_urls", "[]"))
        daily_budget = float(arguments.get("daily_budget", 0))
        
        errors = []
        warnings = []
        
        # Validate campaign name
        if not campaign_name:
            errors.append("Campaign name is required")
        elif len(campaign_name) > 255:
            errors.append("Campaign name must be 255 characters or less")
        
        # Validate business name
        if not business_name:
            errors.append("Business name is required")
        elif len(business_name) > 25:
            errors.append("Business name must be 25 characters or less")
        
        # Validate budget
        if daily_budget <= 0:
            errors.append("Daily budget must be greater than $0")
        elif daily_budget < 10:
            warnings.append("Google recommends at least $10/day for Performance Max")
        
        # Validate assets
        if len(headlines) < 1:
            errors.append("Performance Max requires at least 1 headline")
        if len(descriptions) < 1:
            errors.append("Performance Max requires at least 1 description")
        if not final_urls:
            errors.append("At least one final URL is required")
        
        # Check character limits
        for i, headline in enumerate(headlines):
            if len(str(headline)) > 30:
                errors.append(f"Headline {i+1} exceeds 30 characters")
        
        for i, description in enumerate(descriptions):
            if len(str(description)) > 90:
                errors.append(f"Description {i+1} exceeds 90 characters")
        
        # Performance recommendations
        if len(headlines) < 5:
            warnings.append("Consider adding more headlines for better performance (5+ recommended)")
        if len(descriptions) < 3:
            warnings.append("Consider adding more descriptions for better performance (3+ recommended)")
        
        # Build response
        if not errors:
            response = f"""✅ **Performance Max Assets Validated!**

📊 **Campaign Summary:**
• Campaign Name: {campaign_name}
• Business Name: {business_name}
• Daily Budget: ${daily_budget:,.2f}

🎨 **Asset Group Details:**
• Headlines: {len(headlines)} provided
• Descriptions: {len(descriptions)} provided
• Final URLs: {len(final_urls)} provided

📝 **Headlines:**
{chr(10).join(f"  {i+1}. {h} ({len(str(h))} chars)" for i, h in enumerate(headlines))}

📄 **Descriptions:**
{chr(10).join(f"  {i+1}. {d} ({len(str(d))} chars)" for i, d in enumerate(descriptions))}

🌐 **Final URLs:**
{chr(10).join(f"  • {url}" for url in final_urls)}

🎯 **Performance Max Coverage:**
Your campaign will serve across:
• Google Search • YouTube • Display Network
• Gmail • Discover • Maps • Partner Sites

{f"⚠️ **Recommendations:**{chr(10)}{chr(10).join(f'• {w}' for w in warnings)}" if warnings else "🎉 **All assets look great!**"}"""
        else:
            response = f"""❌ **Performance Max Validation Failed**

🔍 **Issues Found ({len(errors)}):**
{chr(10).join(f"• {error}" for error in errors)}

{f"⚠️ **Warnings:**{chr(10)}{chr(10).join(f'• {w}' for w in warnings)}" if warnings else ""}

💡 **Fix these issues and try again.**"""
        
        return [TextContent(type="text", text=response)]
        
    except Exception as e:
        logger.error(f"PMax validation error: {e}")
        error_response = f"❌ Performance Max validation error: {str(e)}"
        return [TextContent(type="text", text=error_response)]

async def handle_bulk_validate_campaigns(arguments: dict) -> list[TextContent]:
    """Validate multiple campaigns at once"""
    
    try:
        campaigns_data = json.loads(arguments.get("campaigns_data", "[]"))
        
        if not isinstance(campaigns_data, list):
            raise ValueError("campaigns_data must be a JSON array")
        
        results = []
        total_campaigns = len(campaigns_data)
        valid_campaigns = 0
        
        for i, campaign in enumerate(campaigns_data):
            campaign_name = campaign.get("name", f"Campaign {i+1}")
            errors = []
            
            # Validate based on campaign type
            campaign_type = campaign.get("type", "search")
            
            if campaign_type == "search":
                headlines = campaign.get("headlines", [])
                descriptions = campaign.get("descriptions", [])
                
                if len(headlines) < 3:
                    errors.append("Need at least 3 headlines")
                if len(descriptions) < 2:
                    errors.append("Need at least 2 descriptions")
                
                for j, h in enumerate(headlines):
                    if len(str(h)) > 30:
                        errors.append(f"Headline {j+1} too long")
                
            elif campaign_type == "performance_max":
                business_name = campaign.get("business_name", "")
                if not business_name:
                    errors.append("Business name required")
                elif len(business_name) > 25:
                    errors.append("Business name too long")
            
            if not errors:
                valid_campaigns += 1
            
            results.append({
                "name": campaign_name,
                "type": campaign_type,
                "valid": len(errors) == 0,
                "errors": errors
            })
        
        # Build response
        response = f"""📊 **Bulk Campaign Validation Results**

📈 **Summary:**
• Total Campaigns: {total_campaigns}
• Valid Campaigns: {valid_campaigns}
• Invalid Campaigns: {total_campaigns - valid_campaigns}
• Success Rate: {(valid_campaigns/total_campaigns*100):.1f}%

📋 **Detailed Results:**

"""
        
        for result in results:
            status = "✅" if result["valid"] else "❌"
            response += f"{status} **{result['name']}** ({result['type']})\n"
            
            if result["errors"]:
                for error in result["errors"]:
                    response += f"  • {error}\n"
            response += "\n"
        
        if valid_campaigns == total_campaigns:
            response += "🎉 **All campaigns passed validation!**"
        else:
            response += "💡 **Fix the issues above and re-validate.**"
        
        return [TextContent(type="text", text=response)]
        
    except Exception as e:
        logger.error(f"Bulk validation error: {e}")
        error_response = f"❌ Bulk validation error: {str(e)}"
        return [TextContent(type="text", text=error_response)]

async def handle_analyze_ad_strength(arguments: dict) -> list[TextContent]:
    """Analyze ad strength and provide recommendations"""
    
    try:
        headlines = json.loads(arguments.get("headlines", "[]"))
        descriptions = json.loads(arguments.get("descriptions", "[]"))
        target_keywords = json.loads(arguments.get("target_keywords", "[]"))
        
        # Ad strength scoring
        score = 0
        max_score = 100
        feedback = []
        
        # Quantity scoring (40 points max)
        headline_score = min(len(headlines) * 5, 30)  # 5 points per headline, max 30
        description_score = min(len(descriptions) * 5, 10)  # 5 points per description, max 10
        score += headline_score + description_score
        
        if len(headlines) < 8:
            feedback.append(f"Add more headlines ({len(headlines)}/15) - Google recommends 8-15")
        if len(descriptions) < 3:
            feedback.append(f"Add more descriptions ({len(descriptions)}/4) - Recommend 3-4")
        
        # Diversity scoring (30 points max)
        unique_words = set()
        for h in headlines:
            unique_words.update(str(h).lower().split())
        for d in descriptions:
            unique_words.update(str(d).lower().split())
        
        diversity_score = min(len(unique_words) * 2, 30)
        score += diversity_score
        
        if diversity_score < 20:
            feedback.append("Increase word diversity - use more varied language")
        
        # Keyword relevance (30 points max)
        keyword_mentions = 0
        all_text = " ".join([str(h) for h in headlines] + [str(d) for d in descriptions]).lower()
        
        for keyword in target_keywords:
            if str(keyword).lower() in all_text:
                keyword_mentions += 1
        
        keyword_score = min(keyword_mentions * 10, 30)
        score += keyword_score
        
        if keyword_score < 20 and target_keywords:
            feedback.append("Include more target keywords in your ad copy")
        
        # Determine ad strength
        if score >= 80:
            strength = "Excellent"
            strength_emoji = "🟢"
        elif score >= 60:
            strength = "Good"
            strength_emoji = "🟡"
        elif score >= 40:
            strength = "Average"
            strength_emoji = "🟠"
        else:
            strength = "Poor"
            strength_emoji = "🔴"
        
        response = f"""{strength_emoji} **Ad Strength Analysis: {strength}**

📊 **Overall Score: {score}/100**

📈 **Scoring Breakdown:**
• Headline Quantity: {headline_score}/30 ({len(headlines)} headlines)
• Description Quantity: {description_score}/10 ({len(descriptions)} descriptions)
• Content Diversity: {diversity_score}/30 ({len(unique_words)} unique words)
• Keyword Relevance: {keyword_score}/30 ({keyword_mentions}/{len(target_keywords)} keywords used)

📝 **Current Assets:**

**Headlines ({len(headlines)}):**
{chr(10).join(f"  {i+1}. {h}" for i, h in enumerate(headlines))}

**Descriptions ({len(descriptions)}):**
{chr(10).join(f"  {i+1}. {d}" for i, d in enumerate(descriptions))}

{f"🎯 **Target Keywords:** {', '.join(target_keywords)}" if target_keywords else ""}

{"🔧 **Recommendations:**" + chr(10) + chr(10).join(f"• {rec}" for rec in feedback) if feedback else "🎉 **Your ad copy looks great!**"}

💡 **Additional Tips:**
• Use specific numbers and benefits in headlines
• Include strong calls-to-action in descriptions  
• Test different emotional appeals (urgency, trust, value)
• Ensure headlines can work in any combination"""
        
        return [TextContent(type="text", text=response)]
        
    except Exception as e:
        logger.error(f"Ad strength analysis error: {e}")
        error_response = f"❌ Ad strength analysis error: {str(e)}"
        return [TextContent(type="text", text=error_response)]

async def main():
    """Main entry point"""
    try:
        logger.info("Starting expanded Google Ads MCP server...")
        
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