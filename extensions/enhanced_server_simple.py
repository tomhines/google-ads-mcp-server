#!/usr/bin/env python3
"""
Simplified Enhanced Google Ads MCP Server
Working version with just RSA validation tools
"""

import asyncio
import json
import logging
from pathlib import Path
import sys

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
server = Server("google-ads-enhanced-simple")

@server.list_tools()
async def list_tools():
    """List all available tools"""
    return [
        Tool(
            name="validate_rsa_copy",
            description="Validate RSA headlines and descriptions for character limits and requirements. Perfect for checking ad copy before creation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "headlines": {
                        "type": "string",
                        "description": "JSON array of headlines to validate (e.g., [\"Headline 1\", \"Headline 2\"])"
                    },
                    "descriptions": {
                        "type": "string", 
                        "description": "JSON array of descriptions to validate (e.g., [\"Description 1\", \"Description 2\"])"
                    },
                    "auto_fix": {
                        "type": "boolean",
                        "description": "Whether to automatically fix character limit issues by truncating"
                    }
                },
                "required": ["headlines", "descriptions"]
            }
        ),
        Tool(
            name="create_responsive_search_ad",
            description="Create a Responsive Search Ad with multiple headlines and descriptions. Requires 3-15 headlines (30 chars max) and 2-4 descriptions (90 chars max). Currently in development mode - validates but doesn't create real ads.",
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
                    }
                },
                "required": ["customer_id", "ad_group_id", "headlines", "descriptions", "final_urls"]
            }
        )
    ]

@server.call_tool()
async def validate_rsa_copy(arguments) -> list[TextContent]:
    """Validate RSA copy for character limits and requirements"""
    
    try:
        # Extract arguments
        headlines = arguments.get("headlines", "")
        descriptions = arguments.get("descriptions", "")
        auto_fix = arguments.get("auto_fix", False)
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

🎯 **Ready to create your RSA!**"""
        
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

The headlines or descriptions parameter contains invalid JSON.

Error: {str(e)}

💡 **Expected Format:**
• headlines: ["Headline 1", "Headline 2", "Headline 3"]
• descriptions: ["Description 1", "Description 2"]"""
        
        return [TextContent(type="text", text=error_response)]
    
    except Exception as e:
        error_response = f"❌ Validation error: {str(e)}"
        return [TextContent(type="text", text=error_response)]

@server.call_tool()
async def create_responsive_search_ad(arguments) -> list[TextContent]:
    """Create a Responsive Search Ad (development mode)"""
    
    try:
        # Extract arguments
        customer_id = arguments.get("customer_id", "")
        ad_group_id = arguments.get("ad_group_id", "")
        headlines = arguments.get("headlines", "")
        descriptions = arguments.get("descriptions", "")
        final_urls = arguments.get("final_urls", "")
        headlines_list = json.loads(headlines)
        descriptions_list = json.loads(descriptions)
        urls_list = json.loads(final_urls)
        
        # Validate first
        validation_errors = []
        
        if len(headlines_list) < 3 or len(headlines_list) > 15:
            validation_errors.append("Need 3-15 headlines")
        if len(descriptions_list) < 2 or len(descriptions_list) > 4:
            validation_errors.append("Need 2-4 descriptions")
        if not urls_list:
            validation_errors.append("Need at least one final URL")
        
        for i, h in enumerate(headlines_list):
            if len(str(h)) > 30:
                validation_errors.append(f"Headline {i+1} too long ({len(str(h))} chars)")
        
        for i, d in enumerate(descriptions_list):
            if len(str(d)) > 90:
                validation_errors.append(f"Description {i+1} too long ({len(str(d))} chars)")
        
        if validation_errors:
            response = f"""❌ **RSA Creation Failed - Validation Errors**

🔍 **Issues:**
{chr(10).join(f"• {error}" for error in validation_errors)}

💡 **Fix these issues and try again, or use the validate_rsa_copy tool first.**"""
        else:
            # Simulate successful creation (development mode)
            response = f"""🎉 **RSA Created Successfully (Development Mode)!**

📊 **Ad Details:**
• Customer ID: {customer_id}
• Ad Group ID: {ad_group_id}
• Headlines: {len(headlines_list)} provided
• Descriptions: {len(descriptions_list)} provided
• Status: PAUSED (ready for review)

📝 **Headlines Used:**
{chr(10).join(f"  {i+1}. {h}" for i, h in enumerate(headlines_list))}

📄 **Descriptions Used:**
{chr(10).join(f"  {i+1}. {d}" for i, d in enumerate(descriptions_list))}

🌐 **Final URLs:**
{chr(10).join(f"  • {url}" for url in urls_list)}

⚠️ **Note:** This is development mode. No actual ad was created in Google Ads. 
Connect real Google Ads API credentials to create live ads."""
        
        return [TextContent(type="text", text=response)]
        
    except json.JSONDecodeError as e:
        error_response = f"❌ JSON parsing error: {str(e)}"
        return [TextContent(type="text", text=error_response)]
    
    except Exception as e:
        error_response = f"❌ RSA creation error: {str(e)}"
        return [TextContent(type="text", text=error_response)]

async def main():
    """Main entry point"""
    try:
        logger.info("Starting simplified Google Ads MCP server...")
        
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