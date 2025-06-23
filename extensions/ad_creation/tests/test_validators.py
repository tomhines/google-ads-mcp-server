"""
Test suite for input validators
Run with: pytest extensions/ad_creation/tests/test_validators.py -v
"""

import pytest
from extensions.ad_creation.utils.validators import (
    validate_rsa_inputs,
    validate_pmax_inputs,
    validate_customer_id,
    validate_json_input,
    validate_pinning_config,
    auto_fix_character_limits
)

class TestRSAValidation:
    """Test RSA input validation"""
    
    def test_valid_rsa_inputs(self):
        """Test valid RSA inputs pass validation"""
        headlines = ["Great Product", "Buy Now", "Limited Time"]
        descriptions = ["Best quality products", "Free shipping available"]
        urls = ["https://example.com"]
        limits = {"max_headlines": 15, "max_descriptions": 4, "headline_char_limit": 30, "description_char_limit": 90}
        
        result = validate_rsa_inputs(headlines, descriptions, urls, None, None, limits)
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    def test_insufficient_headlines(self):
        """Test validation fails with too few headlines"""
        headlines = ["Only One", "Two Headlines"]  # Need 3 minimum
        descriptions = ["Description one", "Description two"]
        urls = ["https://example.com"]
        limits = {"max_headlines": 15, "max_descriptions": 4, "headline_char_limit": 30, "description_char_limit": 90}
        
        result = validate_rsa_inputs(headlines, descriptions, urls, None, None, limits)
        
        assert result["valid"] is False
        assert any("at least 3 headlines" in error for error in result["errors"])
    
    def test_headline_character_limit(self):
        """Test validation fails with headlines too long"""
        headlines = [
            "This headline is way too long and exceeds the thirty character limit",
            "Normal headline",
            "Another normal one"
        ]
        descriptions = ["Description one", "Description two"]
        urls = ["https://example.com"]
        limits = {"max_headlines": 15, "max_descriptions": 4, "headline_char_limit": 30, "description_char_limit": 90}
        
        result = validate_rsa_inputs(headlines, descriptions, urls, None, None, limits)
        
        assert result["valid"] is False
        assert any("exceeds 30 characters" in error for error in result["errors"])
    
    def test_duplicate_headlines(self):
        """Test validation fails with duplicate headlines"""
        headlines = ["Same headline", "Different headline", "Same headline"]
        descriptions = ["Description one", "Description two"]
        urls = ["https://example.com"]
        limits = {"max_headlines": 15, "max_descriptions": 4, "headline_char_limit": 30, "description_char_limit": 90}
        
        result = validate_rsa_inputs(headlines, descriptions, urls, None, None, limits)
        
        assert result["valid"] is False
        assert any("unique" in error for error in result["errors"])
    
    def test_invalid_urls(self):
        """Test validation fails with invalid URLs"""
        headlines = ["Headline 1", "Headline 2", "Headline 3"]
        descriptions = ["Description one", "Description two"]
        urls = ["not-a-valid-url", "https://valid.com"]
        limits = {"max_headlines": 15, "max_descriptions": 4, "headline_char_limit": 30, "description_char_limit": 90}
        
        result = validate_rsa_inputs(headlines, descriptions, urls, None, None, limits)
        
        assert result["valid"] is False
        assert any("not valid" in error for error in result["errors"])

class TestPMaxValidation:
    """Test Performance Max input validation"""
    
    def test_valid_pmax_inputs(self):
        """Test valid PMax inputs pass validation"""
        result = validate_p