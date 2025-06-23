"""
MCP Tools for Responsive Search Ad Creation
Provides Claude-friendly interface to RSA functionality
"""

import json
import logging
from typing import List
from mcp.server import Server
from mcp.types import Tool, TextContent

from ..utils.formatters import format_claude_response
from ..utils.validators import validate_json_input, validate_pinning_config
from ..services.rsa_service import RSAService

logger = logging.getLogger(__name__)

def register_rsa_tools(server: Server, rsa_service: RSAService):
    """Register all RSA-related MCP tools"""
    
    @server.call_tool()
    async def create_responsive_search_ad(
        customer_id: str,
        ad_group_id: str,
        headlines: str,  # JSON array
        descriptions: str,  # JSON array 
        final_urls: str,  # JSON array
        path1: str = "",
        path2: str = "",
        pinned_headlines: str = "",
        pinned_descriptions: str = ""
    ) -> List[TextContent]:
        """
        Create a Responsive Search Ad with multiple headlines and descriptions
        
        This tool creates a responsive search ad that automatically tests different
        combinations of your headlines and descriptions to find the best performing ones.
        """
        
        try:
            # Parse JSON inputs
            headlines_list = validate_json_input(headlines, "headlines")
            descriptions_list = validate_json_input(descriptions, "descriptions")
            final_urls_list = validate_json_input(final_urls, "final_urls")
            
            # Parse optional pinning configurations
            pinned_headlines_dict = None
            pinned_descriptions_dict = None
            
            if pinned_headlines.strip():
                pinned_headlines_dict = validate_pinning_config(
                    pinned_headlines, headlines_list, "headlines"
                )
            
            if pinned_descriptions.strip():
                pinned_descriptions_dict = validate_pinning_config(
                    pinned_descriptions, descriptions_list, "descriptions"
                )
            
            # Create the ad
            result = rsa_service.create_responsive_search_ad(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                headlines=headlines_list,
                descriptions=descriptions_list,
                final_urls=final_urls_list,
                path1=path1 if path1.strip() else None,
                path2=path2 if path2.strip() else None,
                pinned_headlines=pinned_headlines_dict,
                pinned_descriptions=pinned_descriptions_dict
            )
            
            # Format response for Claude
            response_text = format_claude_response(result, "rsa_creation")
            return [TextContent(type="text", text=response_text)]
            
        except ValueError as e:
            error_response = f"""
❌ **Input Validation Error**

{str(e)}

💡 **Expected Format Examples:**
• headlines: ["Headline 1", "Headline 2", "Headline 3"]
• descriptions: ["Description 1", "Description 2"]  
• final_urls: ["https://example.com"]
• pinned_headlines: {{"My Important Headline": "HEADLINE_1"}}
            """.strip()
            return [TextContent(type="text", text=error_response)]
            
        except Exception as e:
            logger.error(f"Unexpected error in create_responsive_search_ad: {str(e)}")
            error_response = f"❌ Unexpected error: {str(e)}"
            return [TextContent(type="text", text=error_response)]

    @server.call_tool()
    async def get_rsa_performance(
        customer_id: str,
        ad_id: str,
        date_range: str = "LAST_30_DAYS"
    ) -> List[TextContent]:
        """
        Get performance metrics for a specific Responsive Search Ad
        
        Shows impressions, clicks, CTR, conversions, and cost data for the specified
        time period. Useful for analyzing how well your RSA is performing.
        """
        
        try:
            result = rsa_service.get_rsa_performance(
                customer_id=customer_id,
                ad_id=ad_id,
                date_range=date_range
            )
            
            if result["success"]:
                from ..utils.formatters import format_performance_data
                response_text = format_performance_data(result["data"], date_range)
            else:
                response_text = format_claude_response(result, "performance_query")
            
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Error getting RSA performance: {str(e)}")
            error_response = f"❌ Failed to get performance data: {str(e)}"
            return [TextContent(type="text", text=error_response)]

    @server.call_tool()
    async def update_rsa_status(
        customer_id: str,
        ad_group_id: str,
        ad_id: str,
        new_status: str
    ) -> List[TextContent]:
        """
        Update the status of a Responsive Search Ad
        
        Change an RSA status to ENABLED (start serving), PAUSED (stop serving), 
        or REMOVED (permanently delete). Use with caution - REMOVED cannot be undone.
        """
        
        try:
            # Validate status
            valid_statuses = ["ENABLED", "PAUSED", "REMOVED"]
            if new_status.upper() not in valid_statuses:
                error_response = f"""
❌ **Invalid Status**

Status '{new_status}' is not valid.

✅ **Valid Options:**
• ENABLED - Start serving the ad
• PAUSED - Stop serving the ad (can be re-enabled)
• REMOVED - Permanently delete the ad (cannot be undone)
                """.strip()
                return [TextContent(type="text", text=error_response)]
            
            result = rsa_service.update_rsa_status(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                ad_id=ad_id,
                new_status=new_status.upper()
            )
            
            response_text = format_claude_response(result, "status_update")
            return [TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Error updating RSA status: {str(e)}")
            error_response = f"❌ Failed to update ad status: {str(e)}"
            return [TextContent(type="text", text=error_response)]

    @server.call_tool()
    async def validate_rsa_copy(
        headlines: str,  # JSON array
        descriptions: str,  # JSON array
        auto_fix: bool = False
    ) -> List[TextContent]:
        """
        Validate RSA copy before creating the ad
        
        Checks headlines and descriptions for character limits, uniqueness,
        and other requirements. Optionally auto-fixes issues like character limits.
        """
        
        try:
            # Parse inputs
            headlines_list = validate_json_input(headlines, "headlines")
            descriptions_list = validate_json_input(descriptions, "descriptions")
            
            # Get validation limits from service config
            limits = rsa_service.rsa_limits
            
            # Validate
            from ..utils.validators import validate_rsa_inputs
            dummy_urls = ["https://example.com"]  # Just for validation
            
            validation_result = validate_rsa_inputs(
                headlines_list, descriptions_list, dummy_urls, 
                None, None, limits
            )
            
            if validation_result["valid"]:
                response = f"""
✅ **RSA Copy Validation Passed!**

📊 **Summary:**
• Headlines: {len(headlines_list)}/15 provided
• Descriptions: {len(descriptions_list)}/4 provided
• All character limits met
• All content is unique

📝 **Headlines ({len(headlines_list)}):**
{chr(10).join(f"  {i+1}. {h} ({len(h)} chars)" for i, h in enumerate(headlines_list))}

📄 **Descriptions ({len(descriptions_list)}):**
{chr(10).join(f"  {i+1}. {d} ({len(d)} chars)" for i, d in enumerate(descriptions_list))}

🎯 **Ready to create your RSA!**
                """.strip()
            else:
                errors_text = "\n".join(f"• {error}" for error in validation_result["errors"])
                
                if auto_fix:
                    # Auto-fix character limit issues
                    from ..utils.validators import auto_fix_character_limits
                    
                    fixed_headlines = [
                        auto_fix_character_limits(h, limits["headline_char_limit"])
                        for h in headlines_list
                    ]
                    fixed_descriptions = [
                        auto_fix_character_limits(d, limits["description_char_limit"])
                        for d in descriptions_list
                    ]
                    
                    response = f"""
🔧 **RSA Copy Validation with Auto-Fix**

❌ **Original Issues Found:**
{errors_text}

✅ **Auto-Fixed Copy:**

📝 **Fixed Headlines:**
{chr(10).join(f"  {i+1}. {h} ({len(h)} chars)" for i, h in enumerate(fixed_headlines))}

📄 **Fixed Descriptions:**
{chr(10).join(f"  {i+1}. {d} ({len(d)} chars)" for i, d in enumerate(fixed_descriptions))}

💡 **Use this JSON for your RSA:**
Headlines: {json.dumps(fixed_headlines)}
Descriptions: {json.dumps(fixed_descriptions)}
                    """.strip()
                else:
                    response = f"""
❌ **RSA Copy Validation Failed**

🔍 **Issues Found ({len(validation_result['errors'])}):**
{errors_text}

💡 **Recommendations:**
• Shorten headlines to 30 characters or less
• Shorten descriptions to 90 characters or less
• Make sure you have 3-15 unique headlines
• Make sure you have 2-4 unique descriptions
• Use the auto_fix=true parameter to automatically fix character limits
                    """.strip()
            
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            logger.error(f"Error validating RSA copy: {str(e)}")
            error_response = f"❌ Validation error: {str(e)}"
            return [TextContent(type="text", text=error_response)]


# Tool definitions for MCP registration
RSA_TOOLS = [
    Tool(
        name="create_responsive_search_ad",
        description="Create a Responsive Search Ad with multiple headlines and descriptions. Requires 3-15 headlines (30 chars max) and 2-4 descriptions (90 chars max). Ads start paused for review.",
        inputSchema={
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Google Ads customer ID in format 123-456-7890"
                },
                "ad_group_id": {
                    "type": "string", 
                    "description": "Ad group ID where the ad will be created"
                },
                "headlines": {
                    "type": "string",
                    "description": "JSON array of headlines (3-15 required, max 30 characters each)"
                },
                "descriptions": {
                    "type": "string",
                    "description": "JSON array of descriptions (2-4 required, max 90 characters each)"
                },
                "final_urls": {
                    "type": "string",
                    "description": "JSON array of final URLs where users will land"
                },
                "path1": {
                    "type": "string",
                    "description": "Optional display URL path 1 (max 15 chars)"
                },
                "path2": {
                    "type": "string", 
                    "description": "Optional display URL path 2 (max 15 chars)"
                },
                "pinned_headlines": {
                    "type": "string",
                    "description": "Optional JSON object mapping headlines to positions like {\"headline text\": \"HEADLINE_1\"}"
                },
                "pinned_descriptions": {
                    "type": "string",
                    "description": "Optional JSON object mapping descriptions to positions like {\"description text\": \"DESCRIPTION_1\"}"
                }
            },
            "required": ["customer_id", "ad_group_id", "headlines", "descriptions", "final_urls"]
        }
    ),
    Tool(
        name="get_rsa_performance",
        description="Get performance metrics for a specific Responsive Search Ad including impressions, clicks, CTR, conversions and cost data.",
        inputSchema={
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Google Ads customer ID in format 123-456-7890"
                },
                "ad_id": {
                    "type": "string",
                    "description": "The ID of the responsive search ad"
                },
                "date_range": {
                    "type": "string",
                    "description": "Date range for performance data (LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS, etc.)"
                }
            },
            "required": ["customer_id", "ad_id"]
        }
    ),
    Tool(
        name="update_rsa_status",
        description="Update the status of a Responsive Search Ad (ENABLED, PAUSED, or REMOVED). Use REMOVED with caution as it cannot be undone.",
        inputSchema={
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Google Ads customer ID in format 123-456-7890"
                },
                "ad_group_id": {
                    "type": "string",
                    "description": "Ad group ID containing the ad"
                },
                "ad_id": {
                    "type": "string",
                    "description": "The ID of the responsive search ad to update"
                },
                "new_status": {
                    "type": "string",
                    "description": "New status: ENABLED, PAUSED, or REMOVED"
                }
            },
            "required": ["customer_id", "ad_group_id", "ad_id", "new_status"]
        }
    ),
    Tool(
        name="validate_rsa_copy",
        description="Validate RSA headlines and descriptions before creating the ad. Checks character limits, uniqueness, and other requirements. Can auto-fix common issues.",
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
    )
]