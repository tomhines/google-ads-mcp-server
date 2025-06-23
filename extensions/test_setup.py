#!/usr/bin/env python3
"""
Test script to validate extension setup and basic functionality
Run this to ensure everything is working before connecting to Claude
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        # Test basic imports
        from extensions.ad_creation.utils.validators import validate_rsa_inputs
        from extensions.ad_creation.utils.formatters import format_rsa_response
        from extensions.config.enhanced_config import EnhancedConfig
        print("  ✅ Core modules imported successfully")
        
        # Test Google Ads client (without credentials)
        from google.ads.googleads.client import GoogleAdsClient
        print("  ✅ Google Ads API client available")
        
        # Test MCP imports
        from mcp.server import Server
        from mcp.types import Tool, TextContent
        print("  ✅ MCP modules available")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False

def test_validators():
    """Test validation functions"""
    print("\n🔍 Testing validators...")
    
    try:
        from extensions.ad_creation.utils.validators import validate_rsa_inputs, validate_customer_id, validate_json_input
        
        # Test RSA validation with valid input
        headlines = ["Great Product", "Buy Now", "Limited Time"]
        descriptions = ["Best quality products", "Free shipping available"]
        urls = ["https://example.com"]
        limits = {"max_headlines": 15, "max_descriptions": 4, "headline_char_limit": 30, "description_char_limit": 90}
        
        result = validate_rsa_inputs(headlines, descriptions, urls, None, None, limits)
        assert result["valid"] is True, "Valid RSA input should pass validation"
        print("  ✅ RSA validation passed")
        
        # Test customer ID validation
        customer_id = validate_customer_id("123-456-7890")
        assert customer_id == "1234567890", "Customer ID should be formatted correctly"
        print("  ✅ Customer ID validation passed")
        
        # Test JSON validation
        json_headlines = json.dumps(headlines)
        parsed_headlines = validate_json_input(json_headlines, "headlines")
        assert parsed_headlines == headlines, "JSON parsing should work correctly"
        print("  ✅ JSON validation passed")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Validation test error: {e}")
        return False

def test_formatters():
    """Test response formatters"""
    print("\n📝 Testing formatters...")
    
    try:
        from extensions.ad_creation.utils.formatters import format_rsa_response, format_error_response, format_claude_response
        
        # Test successful RSA response
        rsa_response = format_rsa_response(
            success=True,
            ad_resource_name="customers/1234567890/adGroupAds/123~456",
            ad_id="456",
            customer_id="1234567890",
            headlines=["Test Headline 1", "Test Headline 2", "Test Headline 3"],
            descriptions=["Test Description 1", "Test Description 2"],
            status="PAUSED"
        )
        
        assert rsa_response["success"] is True, "RSA response should indicate success"
        assert rsa_response["ad_id"] == "456", "Ad ID should be preserved"
        print("  ✅ RSA response formatting passed")
        
        # Test error response
        error_response = format_error_response("Test Error", ["Error message 1", "Error message 2"])
        assert error_response["success"] is False, "Error response should indicate failure"
        assert len(error_response["errors"]) == 2, "Should preserve all error messages"
        print("  ✅ Error response formatting passed")
        
        # Test Claude response formatting
        claude_response = format_claude_response(rsa_response, "rsa_creation")
        assert isinstance(claude_response, str), "Claude response should be formatted as string"
        assert "Responsive Search Ad Created Successfully" in claude_response, "Should contain success message"
        print("  ✅ Claude response formatting passed")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Formatter test error: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from extensions.config.enhanced_config import EnhancedConfig
        
        # Test config initialization (should work even without env vars)
        config = EnhancedConfig()
        
        # Test limit getters
        rsa_limits = config.get_rsa_limits()
        assert "max_headlines" in rsa_limits, "RSA limits should include max_headlines"
        assert "headline_char_limit" in rsa_limits, "RSA limits should include character limits"
        print("  ✅ RSA limits configuration passed")
        
        asset_limits = config.get_asset_limits()
        assert "max_size_mb" in asset_limits, "Asset limits should include size limits"
        print("  ✅ Asset limits configuration passed")
        
        # Test config dict conversion
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict), "Config should convert to dict"
        print("  ✅ Config serialization passed")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Config test error: {e}")
        return False

def test_mcp_tools_structure():
    """Test MCP tools can be imported and structured correctly"""
    print("\n🔧 Testing MCP tools structure...")
    
    try:
        from extensions.ad_creation.tools.rsa_tools import RSA_TOOLS
        
        # Validate tool structure
        assert isinstance(RSA_TOOLS, list), "RSA_TOOLS should be a list"
        assert len(RSA_TOOLS) > 0, "Should have at least one tool defined"
        
        for tool in RSA_TOOLS:
            assert hasattr(tool, 'name'), "Each tool should have a name"
            assert hasattr(tool, 'description'), "Each tool should have a description"
            assert hasattr(tool, 'inputSchema'), "Each tool should have an input schema"
            print(f"  ✅ Tool '{tool.name}' structure valid")
        
        return True
        
    except Exception as e:
        print(f"  ❌ MCP tools test error: {e}")
        return False

def test_sample_workflow():
    """Test a sample workflow without actual API calls"""
    print("\n🚀 Testing sample workflow...")
    
    try:
        # Simulate Claude input
        sample_headlines = json.dumps([
            "Professional Digital Marketing",
            "Grow Your Business Online",
            "Expert Marketing Solutions"
        ])
        
        sample_descriptions = json.dumps([
            "Get more customers with our proven digital marketing strategies.",
            "Free consultation available. Start growing your business today."
        ])
        
        sample_urls = json.dumps(["https://example.com"])
        
        # Test input validation
        from extensions.ad_creation.utils.validators import validate_json_input
        
        headlines_list = validate_json_input(sample_headlines, "headlines")
        descriptions_list = validate_json_input(sample_descriptions, "descriptions")
        urls_list = validate_json_input(sample_urls, "final_urls")
        
        print(f"  ✅ Parsed {len(headlines_list)} headlines")
        print(f"  ✅ Parsed {len(descriptions_list)} descriptions")
        print(f"  ✅ Parsed {len(urls_list)} URLs")
        
        # Test validation
        from extensions.ad_creation.utils.validators import validate_rsa_inputs
        limits = {"max_headlines": 15, "max_descriptions": 4, "headline_char_limit": 30, "description_char_limit": 90}
        
        validation_result = validate_rsa_inputs(headlines_list, descriptions_list, urls_list, None, None, limits)
        
        if validation_result["valid"]:
            print("  ✅ Sample workflow validation passed")
        else:
            print(f"  ⚠️ Sample workflow validation issues: {validation_result['errors']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Sample workflow test error: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("🎯 Running Extension Setup Tests\n")
    
    tests = [
        ("Import Tests", test_imports),
        ("Validator Tests", test_validators),
        ("Formatter Tests", test_formatters),
        ("Configuration Tests", test_config),
        ("MCP Tools Tests", test_mcp_tools_structure),
        ("Sample Workflow Tests", test_sample_workflow)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  ❌ {test_name} failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your extension setup is ready.")
        print("\n📋 Next Steps:")
        print("1. Set up your Google Ads API credentials")
        print("2. Update your .env file with credentials")
        print("3. Configure Claude Desktop to use the enhanced server")
        print("4. Test with Claude!")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)