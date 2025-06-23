#!/usr/bin/env python3
"""
Clean Enhanced Google Ads MCP Server
Fixed version with explicit tool registration
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
server = Server("google-ads-clean")

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
    else:
        return [TextContent(
            type="text", 
            text=f"❌ Unknown tool: {name}"
        )]

async def handle_validate_rsa_copy(arguments: dict) -> list[TextContent]:
    """Handle RSA validation"""
    
    try:
        # Extract arguments
        headlines = arguments.get("headlines", "")
        descriptions = arguments.get("descriptions", "")
        auto_fix = arguments.get("auto_fix", False)
        
        logger.info(f"Validating RSA copy - Headlines: {headlines}, Descriptions: {descriptions}")
        
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

The headlines or descriptions parameter contains invalid JSON.

Error: {str(e)}

💡 **Expected Format:**
• headlines: ["Headline 1", "Headline 2", "Headline 3"]
• descriptions: ["Description 1", "Description 2"]"""
        
        return [TextContent(type="text", text=error_response)]
    
    except Exception as e:
        logger.error(f"Validation error: {e}")
        error_response = f"❌ Validation error: {str(e)}"
        return [TextContent(type="text", text=error_response)]

async def main():
    """Main entry point"""
    try:
        logger.info("Starting clean Google Ads MCP server...")
        
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