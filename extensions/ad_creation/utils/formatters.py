"""
Response formatting utilities for Claude interactions
Creates user-friendly, informative responses
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

def format_rsa_response(
    success: bool,
    ad_resource_name: str,
    ad_id: str,
    customer_id: str,
    headlines: List[str],
    descriptions: List[str],
    status: str,
    **kwargs
) -> Dict[str, Any]:
    """Format successful RSA creation response"""
    
    preview_url = f"https://ads.google.com/aw/ads?adId={ad_id}&ocid={customer_id}"
    
    return {
        "success": success,
        "ad_resource_name": ad_resource_name,
        "ad_id": ad_id,
        "status": status,
        "headlines_count": len(headlines),
        "descriptions_count": len(descriptions),
        "preview_url": preview_url,
        "headlines": headlines,
        "descriptions": descriptions,
        "created_at": datetime.now().isoformat(),
        "message": f"Responsive Search Ad created successfully with {len(headlines)} headlines and {len(descriptions)} descriptions"
    }

def format_pmax_response(
    success: bool,
    campaign_resource_name: str,
    campaign_id: str,
    campaign_name: str,
    budget_amount_dollars: float,
    asset_group_data: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """Format successful Performance Max campaign creation response"""
    
    customer_id = campaign_resource_name.split('/')[1]
    preview_url = f"https://ads.google.com/aw/campaigns?campaignId={campaign_id}&ocid={customer_id}"
    
    return {
        "success": success,
        "campaign_resource_name": campaign_resource_name,
        "campaign_id": campaign_id,
        "campaign_name": campaign_name,
        "daily_budget": budget_amount_dollars,
        "asset_group": asset_group_data,
        "preview_url": preview_url,
        "created_at": datetime.now().isoformat(),
        "message": f"Performance Max campaign '{campaign_name}' created successfully"
    }

def format_error_response(
    error_type: str,
    errors: List[Any],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format error response with detailed information"""
    
    # Convert errors to consistent format
    formatted_errors = []
    for error in errors:
        if isinstance(error, str):
            formatted_errors.append({"message": error})
        elif isinstance(error, dict):
            formatted_errors.append(error)
        else:
            formatted_errors.append({"message": str(error)})
    
    response = {
        "success": False,
        "error_type": error_type,
        "errors": formatted_errors,
        "error_count": len(formatted_errors),
        "timestamp": datetime.now().isoformat()
    }
    
    if metadata:
        response["metadata"] = metadata
    
    return response

def format_claude_response(result: Dict[str, Any], operation_type: str) -> str:
    """
    Format API response into Claude-friendly text
    
    Args:
        result: API response dictionary
        operation_type: Type of operation (rsa_creation, pmax_creation, etc.)
        
    Returns:
        Formatted text response for Claude
    """
    
    if result["success"]:
        return _format_success_response(result, operation_type)
    else:
        return _format_error_response_text(result, operation_type)

def _format_success_response(result: Dict[str, Any], operation_type: str) -> str:
    """Format successful operation response"""
    
    if operation_type == "rsa_creation":
        return f"""
🎉 **Responsive Search Ad Created Successfully!**

📊 **Ad Details:**
• Ad ID: `{result['ad_id']}`
• Status: {result['status']} (ready to enable)
• Headlines: {result['headlines_count']} provided
• Descriptions: {result['descriptions_count']} provided

🔗 **Preview Link:** [View in Google Ads]({result['preview_url']})

📝 **Headlines Used:**
{_format_text_list(result['headlines'])}

📄 **Descriptions Used:**
{_format_text_list(result['descriptions'])}

⚡ **Next Steps:**
1. Review the ad in Google Ads interface
2. Enable the ad when ready to start serving  
3. Monitor performance and optimize as needed

✅ {result['message']}
        """.strip()
    
    elif operation_type == "pmax_creation":
        asset_group = result['asset_group']
        return f"""
🚀 **Performance Max Campaign Created Successfully!**

📊 **Campaign Details:**
• Campaign Name: {result['campaign_name']}
• Campaign ID: `{result['campaign_id']}`
• Daily Budget: ${result['daily_budget']:,.2f}
• Status: PAUSED (ready to enable)

🎨 **Asset Group Details:**
• Headlines: {asset_group.get('headlines_count', 0)} provided
• Descriptions: {asset_group.get('descriptions_count', 0)} provided
• Business Name: {asset_group.get('business_name', 'N/A')}
• Images: {asset_group.get('image_assets', 0)} uploaded
• Logos: {asset_group.get('logo_assets', 0)} uploaded

🔗 **Campaign Link:** [View in Google Ads]({result['preview_url']})

🌐 **Channels Covered:**
• Google Search • YouTube • Display Network  
• Gmail • Discover • Maps • Partner Sites

⚡ **Next Steps:**
1. Review campaign settings in Google Ads
2. Add conversion tracking if not already set up
3. Enable campaign when ready to start serving
4. Monitor performance across all channels

✅ {result['message']}
        """.strip()
    
    elif operation_type == "bulk_creation":
        return f"""
📦 **Bulk Ad Creation Completed!**

📊 **Summary:**
• Campaigns Created: {result.get('campaigns_created', 0)}
• Ad Groups Created: {result.get('ad_groups_created', 0)}
• Ads Created: {result.get('ads_created', 0)}

📝 **Details:**
{_format_bulk_details(result.get('details', []))}

✅ All created items start in PAUSED status for review.
        """.strip()
    
    else:
        return f"✅ Operation completed successfully: {result.get('message', 'No additional details')}"

def _format_error_response_text(result: Dict[str, Any], operation_type: str) -> str:
    """Format error response for Claude"""
    
    error_list = []
    for error in result.get('errors', []):
        if isinstance(error, dict):
            error_list.append(f"• {error.get('message', str(error))}")
        else:
            error_list.append(f"• {str(error)}")
    
    return f"""
❌ **{result.get('error_type', 'Operation Failed')}**

🔍 **Errors Found ({result.get('error_count', len(error_list))}):**
{chr(10).join(error_list)}

💡 **Troubleshooting Tips:**
{_get_troubleshooting_tips(operation_type)}

🕒 **Error Time:** {result.get('timestamp', 'Unknown')}
    """.strip()

def _format_text_list(items: List[str], max_items: int = 10) -> str:
    """Format a list of text items for display"""
    
    formatted_items = []
    for i, item in enumerate(items[:max_items]):
        formatted_items.append(f"  {i+1}. {item}")
    
    if len(items) > max_items:
        formatted_items.append(f"  ... and {len(items) - max_items} more")
    
    return "\n".join(formatted_items)

def _format_bulk_details(details: List[Dict[str, Any]]) -> str:
    """Format bulk operation details"""
    
    if not details:
        return "No details available"
    
    formatted_details = []
    for detail in details:
        formatted_details.append(
            f"• {detail.get('type', 'Unknown')}: {detail.get('name', 'Unnamed')} "
            f"(ID: {detail.get('id', 'N/A')})"
        )
    
    return "\n".join(formatted_details)

def _get_troubleshooting_tips(operation_type: str) -> str:
    """Get context-specific troubleshooting tips"""
    
    tips = {
        "rsa_creation": """• Check that headlines are 30 characters or less
• Ensure descriptions are 90 characters or less
• Verify ad group ID exists and is active
• Confirm customer ID format (123-456-7890)
• Make sure you have 3-15 headlines and 2-4 descriptions""",
        
        "pmax_creation": """• Verify customer ID format (123-456-7890)
• Check that budget amount is positive
• Ensure business name is provided and under 25 characters
• Confirm final URLs are valid and accessible
• Make sure you have at least 1 headline and 1 description""",
        
        "bulk_creation": """• Check JSON structure is valid
• Verify all required fields are present
• Ensure campaign types are valid (performance_max, search, display)
• Confirm all customer IDs and resource IDs exist
• Review individual campaign validation errors above"""
    }
    
    return tips.get(operation_type, "• Check API credentials and permissions\n• Verify input data format and values\n• Review Google Ads account access")

def format_performance_data(
    performance_data: List[Dict[str, Any]],
    date_range: str
) -> str:
    """Format performance data for Claude display"""
    
    if not performance_data:
        return f"No performance data found for {date_range}"
    
    total_impressions = sum(row.get('impressions', 0) for row in performance_data)
    total_clicks = sum(row.get('clicks', 0) for row in performance_data)
    total_cost = sum(row.get('cost', 0) for row in performance_data)
    total_conversions = sum(row.get('conversions', 0) for row in performance_data)
    
    avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    
    response = f"""
📈 **Performance Summary ({date_range})**

📊 **Totals:**
• Impressions: {total_impressions:,}
• Clicks: {total_clicks:,}
• CTR: {avg_ctr:.2f}%
• Cost: ${total_cost:,.2f}
• Conversions: {total_conversions:,.1f}

📝 **Individual Ads:**
"""
    
    for i, row in enumerate(performance_data[:10]):  # Limit to top 10
        response += f"""
  **Ad {i+1} (ID: {row.get('ad_id', 'N/A')})**
  • Headlines: {row.get('headlines_count', 0)} • Descriptions: {row.get('descriptions_count', 0)}
  • Impressions: {row.get('impressions', 0):,} • Clicks: {row.get('clicks', 0):,}
  • CTR: {row.get('ctr', 0):.2f}% • Cost: ${row.get('cost', 0):,.2f}
"""
    
    if len(performance_data) > 10:
        response += f"\n... and {len(performance_data) - 10} more ads"
    
    return response.strip()