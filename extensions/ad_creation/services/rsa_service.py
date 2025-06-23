"""
Responsive Search Ad Service
Handles creation and management of RSAs through Google Ads API
"""

import logging
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from ..utils.validators import validate_rsa_inputs, validate_customer_id
from ..utils.formatters import format_rsa_response, format_error_response

logger = logging.getLogger(__name__)

class RSAService:
    """Service for creating and managing Responsive Search Ads"""
    
    def __init__(self, client: GoogleAdsClient, config):
        self.client = client
        self.config = config
        self.rsa_limits = config.get_rsa_limits()
    
    def create_responsive_search_ad(
        self,
        customer_id: str,
        ad_group_id: str,
        headlines: List[str],
        descriptions: List[str],
        final_urls: List[str],
        path1: Optional[str] = None,
        path2: Optional[str] = None,
        pinned_headlines: Optional[Dict[str, str]] = None,
        pinned_descriptions: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a Responsive Search Ad
        
        Args:
            customer_id: Google Ads customer ID (formatted)
            ad_group_id: Target ad group ID
            headlines: List of headlines (3-15 required)
            descriptions: List of descriptions (2-4 required)
            final_urls: List of final URLs
            path1: Optional display URL path 1
            path2: Optional display URL path 2
            pinned_headlines: Optional headline pinning
            pinned_descriptions: Optional description pinning
            
        Returns:
            Dictionary with creation results and metadata
        """
        
        try:
            # Validate inputs
            validation_result = validate_rsa_inputs(
                headlines, descriptions, final_urls, 
                path1, path2, self.rsa_limits
            )
            
            if not validation_result["valid"]:
                return format_error_response(
                    "Validation Error",
                    validation_result["errors"]
                )
            
            # Format customer ID and construct resource names
            formatted_customer_id = validate_customer_id(customer_id)
            ad_group_resource_name = f"customers/{formatted_customer_id}/adGroups/{ad_group_id}"
            
            # Create the ad through Google Ads API
            result = self._create_rsa_via_api(
                formatted_customer_id,
                ad_group_resource_name,
                headlines,
                descriptions,
                final_urls,
                path1,
                path2,
                pinned_headlines,
                pinned_descriptions
            )
            
            return result
            
        except Exception as e:
            logger.error(f"RSA creation failed: {str(e)}")
            return format_error_response(
                "RSA Creation Failed",
                [str(e)]
            )
    
    def _create_rsa_via_api(
        self,
        customer_id: str,
        ad_group_resource_name: str,
        headlines: List[str],
        descriptions: List[str],
        final_urls: List[str],
        path1: Optional[str],
        path2: Optional[str],
        pinned_headlines: Optional[Dict[str, str]],
        pinned_descriptions: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Execute the actual API call to create RSA"""
        
        try:
            ad_group_ad_service = self.client.get_service("AdGroupAdService")
            ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
            
            # Build the ad group ad
            ad_group_ad = ad_group_ad_operation.create
            ad_group_ad.ad_group = ad_group_resource_name
            ad_group_ad.status = getattr(
                self.client.enums.AdGroupAdStatusEnum, 
                self.config.default_ad_status
            )
            
            # Create responsive search ad info
            responsive_search_ad_info = self.client.get_type("ResponsiveSearchAdInfo")
            
            # Add headlines with optional pinning
            for headline_text in headlines:
                headline = self.client.get_type("AdTextAsset")
                headline.text = headline_text
                
                # Apply pinning if specified
                if pinned_headlines and headline_text in pinned_headlines:
                    pinned_field = getattr(
                        self.client.enums.ServedAssetFieldTypeEnum,
                        pinned_headlines[headline_text]
                    )
                    headline.pinned_field = pinned_field
                
                responsive_search_ad_info.headlines.append(headline)
            
            # Add descriptions with optional pinning
            for description_text in descriptions:
                description = self.client.get_type("AdTextAsset")
                description.text = description_text
                
                # Apply pinning if specified
                if pinned_descriptions and description_text in pinned_descriptions:
                    pinned_field = getattr(
                        self.client.enums.ServedAssetFieldTypeEnum,
                        pinned_descriptions[description_text]
                    )
                    description.pinned_field = pinned_field
                
                responsive_search_ad_info.descriptions.append(description)
            
            # Set final URLs
            ad_group_ad.ad.final_urls.extend(final_urls)
            
            # Set display URL paths
            if path1:
                ad_group_ad.ad.display_url_path_1 = path1
            if path2:
                ad_group_ad.ad.display_url_path_2 = path2
            
            # Assign the responsive search ad
            ad_group_ad.ad.responsive_search_ad = responsive_search_ad_info
            
            # Execute the operation
            response = ad_group_ad_service.mutate_ad_group_ads(
                customer_id=customer_id,
                operations=[ad_group_ad_operation]
            )
            
            # Extract result details
            ad_resource_name = response.results[0].resource_name
            ad_id = ad_resource_name.split('/')[-1]
            
            return format_rsa_response(
                success=True,
                ad_resource_name=ad_resource_name,
                ad_id=ad_id,
                customer_id=customer_id,
                headlines=headlines,
                descriptions=descriptions,
                status=self.config.default_ad_status
            )
            
        except GoogleAdsException as ex:
            logger.error(f"Google Ads API error: {ex}")
            return self._handle_google_ads_exception(ex)
        
        except Exception as ex:
            logger.error(f"Unexpected error in RSA creation: {ex}")
            return format_error_response(
                "Unexpected Error",
                [f"Failed to create RSA: {str(ex)}"]
            )
    
    def _handle_google_ads_exception(self, ex: GoogleAdsException) -> Dict[str, Any]:
        """Handle Google Ads API exceptions with detailed error information"""
        
        error_details = []
        for error in ex.failure.errors:
            error_detail = {
                "error_code": error.error_code,
                "message": error.message,
                "trigger": error.trigger.value if error.trigger else None,
                "location": []
            }
            
            if error.location:
                for field_path in error.location.field_path_elements:
                    error_detail["location"].append({
                        "field": field_path.field_name,
                        "index": field_path.index if field_path.index else None
                    })
            
            error_details.append(error_detail)
        
        return format_error_response(
            "Google Ads API Error",
            error_details,
            metadata={
                "request_id": getattr(ex, 'request_id', None),
                "failure_type": type(ex.failure).__name__
            }
        )
    
    def get_rsa_performance(
        self,
        customer_id: str,
        ad_id: str,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get performance data for a specific RSA"""
        
        try:
            formatted_customer_id = validate_customer_id(customer_id)
            
            # GAQL query for RSA performance
            query = f"""
                SELECT 
                    ad_group_ad.ad.id,
                    ad_group_ad.ad.responsive_search_ad.headlines,
                    ad_group_ad.ad.responsive_search_ad.descriptions,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.ctr,
                    metrics.conversions,
                    metrics.cost_micros
                FROM ad_group_ad
                WHERE ad_group_ad.ad.id = {ad_id}
                    AND segments.date DURING {date_range}
            """
            
            google_ads_service = self.client.get_service("GoogleAdsService")
            response = google_ads_service.search(
                customer_id=formatted_customer_id,
                query=query
            )
            
            # Process response
            performance_data = []
            for row in response:
                performance_data.append({
                    "ad_id": row.ad_group_ad.ad.id,
                    "headlines_count": len(row.ad_group_ad.ad.responsive_search_ad.headlines),
                    "descriptions_count": len(row.ad_group_ad.ad.responsive_search_ad.descriptions),
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "ctr": round(row.metrics.ctr * 100, 2),
                    "conversions": row.metrics.conversions,
                    "cost": row.metrics.cost_micros / 1_000_000
                })
            
            return {
                "success": True,
                "data": performance_data,
                "date_range": date_range,
                "total_ads": len(performance_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to get RSA performance: {e}")
            return format_error_response(
                "Performance Query Failed",
                [str(e)]
            )
    
    def update_rsa_status(
        self,
        customer_id: str,
        ad_group_id: str,
        ad_id: str,
        new_status: str
    ) -> Dict[str, Any]:
        """Update the status of an RSA (enable/pause/remove)"""
        
        try:
            formatted_customer_id = validate_customer_id(customer_id)
            ad_resource_name = f"customers/{formatted_customer_id}/adGroupAds/{ad_group_id}~{ad_id}"
            
            # Validate status
            valid_statuses = ["ENABLED", "PAUSED", "REMOVED"]
            if new_status not in valid_statuses:
                return format_error_response(
                    "Invalid Status",
                    [f"Status must be one of: {', '.join(valid_statuses)}"]
                )
            
            ad_group_ad_service = self.client.get_service("AdGroupAdService")
            ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
            
            ad_group_ad = ad_group_ad_operation.update
            ad_group_ad.resource_name = ad_resource_name
            ad_group_ad.status = getattr(
                self.client.enums.AdGroupAdStatusEnum,
                new_status
            )
            
            ad_group_ad_operation.update_mask.paths.append("status")
            
            response = ad_group_ad_service.mutate_ad_group_ads(
                customer_id=formatted_customer_id,
                operations=[ad_group_ad_operation]
            )
            
            return {
                "success": True,
                "ad_resource_name": response.results[0].resource_name,
                "ad_id": ad_id,
                "new_status": new_status,
                "message": f"RSA status updated to {new_status}"
            }
            
        except Exception as e:
            logger.error(f"Failed to update RSA status: {e}")
            return format_error_response(
                "Status Update Failed",
                [str(e)]
            )