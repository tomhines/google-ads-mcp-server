"""
Input validation utilities for ad creation
Ensures data quality and API compliance
"""

import re
from typing import List, Dict, Optional, Any, Tuple
from urllib.parse import urlparse

def validate_rsa_inputs(
    headlines: List[str],
    descriptions: List[str], 
    final_urls: List[str],
    path1: Optional[str],
    path2: Optional[str],
    limits: Dict[str, int]
) -> Dict[str, Any]:
    """
    Validate inputs for Responsive Search Ad creation
    
    Returns:
        Dict with 'valid' boolean and 'errors' list
    """
    
    errors = []
    
    # Validate headlines
    if len(headlines) < 3:
        errors.append("RSA requires at least 3 headlines")
    if len(headlines) > limits["max_headlines"]:
        errors.append(f"RSA allows maximum {limits['max_headlines']} headlines")
    
    for i, headline in enumerate(headlines):
        if len(headline) == 0:
            errors.append(f"Headline {i+1} cannot be empty")
        elif len(headline) > limits["headline_char_limit"]:
            errors.append(f"Headline {i+1} exceeds {limits['headline_char_limit']} characters: '{headline[:50]}...'")
    
    # Validate descriptions
    if len(descriptions) < 2:
        errors.append("RSA requires at least 2 descriptions")
    if len(descriptions) > limits["max_descriptions"]:
        errors.append(f"RSA allows maximum {limits['max_descriptions']} descriptions")
    
    for i, description in enumerate(descriptions):
        if len(description) == 0:
            errors.append(f"Description {i+1} cannot be empty")
        elif len(description) > limits["description_char_limit"]:
            errors.append(f"Description {i+1} exceeds {limits['description_char_limit']} characters")
    
    # Validate URLs
    if not final_urls:
        errors.append("At least one final URL is required")
    
    for i, url in enumerate(final_urls):
        if not _is_valid_url(url):
            errors.append(f"Final URL {i+1} is not valid: {url}")
    
    # Validate paths
    if path1 and len(path1) > 15:
        errors.append("Path 1 must be 15 characters or less")
    if path2 and len(path2) > 15:
        errors.append("Path 2 must be 15 characters or less")
    
    # Check for duplicate headlines/descriptions
    if len(set(headlines)) != len(headlines):
        errors.append("Headlines must be unique")
    if len(set(descriptions)) != len(descriptions):
        errors.append("Descriptions must be unique")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def validate_pmax_inputs(
    campaign_name: str,
    budget_amount: float,
    headlines: List[str],
    descriptions: List[str],
    final_urls: List[str],
    business_name: str
) -> Dict[str, Any]:
    """Validate inputs for Performance Max campaign creation"""
    
    errors = []
    
    # Campaign name validation
    if not campaign_name or len(campaign_name.strip()) == 0:
        errors.append("Campaign name is required")
    elif len(campaign_name) > 255:
        errors.append("Campaign name must be 255 characters or less")
    
    # Budget validation
    if budget_amount <= 0:
        errors.append("Budget must be greater than 0")
    elif budget_amount > 1000000:  # $1M daily budget seems reasonable as max
        errors.append("Daily budget seems unusually high")
    
    # Business name validation
    if not business_name or len(business_name.strip()) == 0:
        errors.append("Business name is required for Performance Max campaigns")
    elif len(business_name) > 25:
        errors.append("Business name must be 25 characters or less")
    
    # Asset group validation (similar to RSA but more flexible)
    if len(headlines) < 1:
        errors.append("Performance Max requires at least 1 headline")
    if len(descriptions) < 1:
        errors.append("Performance Max requires at least 1 description")
    
    # Validate final URLs
    for i, url in enumerate(final_urls):
        if not _is_valid_url(url):
            errors.append(f"Final URL {i+1} is not valid: {url}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def validate_customer_id(customer_id: str) -> str:
    """
    Validate and format Google Ads customer ID
    
    Args:
        customer_id: Customer ID in format 123-456-7890 or 1234567890
        
    Returns:
        Formatted customer ID without dashes
        
    Raises:
        ValueError: If customer ID format is invalid
    """
    
    # Remove any dashes or spaces
    cleaned_id = re.sub(r'[-\s]', '', customer_id)
    
    # Validate format (10 digits)
    if not re.match(r'^\d{10}$', cleaned_id):
        raise ValueError(f"Invalid customer ID format: {customer_id}. Expected format: 123-456-7890")
    
    return cleaned_id

def validate_ad_group_id(ad_group_id: str) -> str:
    """
    Validate ad group ID format
    
    Returns:
        Clean ad group ID
        
    Raises:
        ValueError: If format is invalid
    """
    
    # Ad group IDs should be numeric
    if not re.match(r'^\d+$', str(ad_group_id)):
        raise ValueError(f"Invalid ad group ID format: {ad_group_id}")
    
    return str(ad_group_id)

def validate_json_input(json_string: str, field_name: str) -> List[str]:
    """
    Validate and parse JSON string input from Claude
    
    Args:
        json_string: JSON string to parse
        field_name: Name of the field for error messages
        
    Returns:
        Parsed list
        
    Raises:
        ValueError: If JSON is invalid
    """
    
    try:
        import json
        parsed = json.loads(json_string)
        
        if not isinstance(parsed, list):
            raise ValueError(f"{field_name} must be a JSON array")
        
        # Convert all items to strings and strip whitespace
        return [str(item).strip() for item in parsed if str(item).strip()]
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON for {field_name}: {str(e)}")

def validate_pinning_config(
    pinning_json: Optional[str],
    assets: List[str],
    field_name: str
) -> Optional[Dict[str, str]]:
    """
    Validate pinning configuration for RSA
    
    Args:
        pinning_json: JSON string with pinning config
        assets: List of headlines or descriptions
        field_name: "headlines" or "descriptions"
        
    Returns:
        Validated pinning dictionary or None
    """
    
    if not pinning_json:
        return None
    
    try:
        import json
        pinning = json.loads(pinning_json)
        
        if not isinstance(pinning, dict):
            raise ValueError(f"Pinning config for {field_name} must be a JSON object")
        
        # Validate that pinned assets exist in the assets list
        for asset_text, position in pinning.items():
            if asset_text not in assets:
                raise ValueError(f"Pinned {field_name[:-1]} '{asset_text}' not found in {field_name} list")
            
            # Validate position format
            valid_positions = {
                "headlines": ["HEADLINE_1", "HEADLINE_2", "HEADLINE_3"],
                "descriptions": ["DESCRIPTION_1", "DESCRIPTION_2"]
            }
            
            if position not in valid_positions[field_name]:
                raise ValueError(f"Invalid position '{position}' for {field_name}")
        
        return pinning
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON for {field_name} pinning: {str(e)}")

def _is_valid_url(url: str) -> bool:
    """Check if URL is properly formatted"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except Exception:
        return False

def auto_fix_character_limits(
    text: str,
    max_chars: int,
    suffix: str = "..."
) -> str:
    """
    Auto-fix text that exceeds character limits
    
    Args:
        text: Text to potentially truncate
        max_chars: Maximum allowed characters
        suffix: Suffix to add when truncating
        
    Returns:
        Fixed text within character limits
    """
    
    if len(text) <= max_chars:
        return text
    
    # Truncate and add suffix
    truncated = text[:max_chars - len(suffix)] + suffix
    return truncated

def validate_bulk_campaign_data(campaign_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate bulk campaign creation data structure"""
    
    errors = []
    
    if "campaigns" not in campaign_data:
        errors.append("Missing 'campaigns' array in bulk data")
        return {"valid": False, "errors": errors}
    
    campaigns = campaign_data["campaigns"]
    if not isinstance(campaigns, list):
        errors.append("'campaigns' must be an array")
        return {"valid": False, "errors": errors}
    
    for i, campaign in enumerate(campaigns):
        campaign_errors = _validate_single_campaign_data(campaign, i)
        errors.extend(campaign_errors)
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def _validate_single_campaign_data(campaign: Dict[str, Any], index: int) -> List[str]:
    """Validate a single campaign in bulk data"""
    
    errors = []
    prefix = f"Campaign {index + 1}: "
    
    required_fields = ["type", "name", "budget_dollars"]
    for field in required_fields:
        if field not in campaign:
            errors.append(f"{prefix}Missing required field '{field}'")
    
    # Validate campaign type
    if campaign.get("type") not in ["performance_max", "search", "display"]:
        errors.append(f"{prefix}Invalid campaign type: {campaign.get('type')}")
    
    # Type-specific validation
    if campaign.get("type") == "performance_max":
        if "asset_group" not in campaign:
            errors.append(f"{prefix}Performance Max campaigns require 'asset_group'")
        elif "headlines" not in campaign["asset_group"]:
            errors.append(f"{prefix}Asset group missing 'headlines'")
    
    return errors