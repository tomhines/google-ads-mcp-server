"""
Performance Max Campaign Service
Handles creation and management of Performance Max campaigns
"""

import logging
import uuid
from typing import List, Dict, Optional, Any
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from ..utils.validators import validate_pmax_inputs, validate_customer_id
from ..utils.formatters import format_pmax_response, format_error_response

logger = logging.getLogger(__name__)

class PMaxService:
    """Service for creating and managing Performance Max campaigns"""
    
    def __init__(self, client: GoogleAdsClient, config):
        self.client = client
        self.config = config
    
    def create_performance_max_campaign(
        self,
        customer_id: str,
        campaign_name: str,
        budget_amount_dollars: float,
        headlines: List[str],
        descriptions: List[str],
        final_urls: List[str],
        business_name: str,
        target_roas: Optional[float] = None,
        marketing_image_urls: Optional[List[str]] = None,
        logo_image_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a complete Performance Max campaign with asset group
        
        Args:
            customer_id: Google Ads customer ID
            campaign_name: Name for the campaign
            budget_amount_dollars: Daily budget in dollars
            headlines: List of headlines for asset group
            descriptions: List of descriptions for asset group
            final_urls: List of final URLs
            business_name: Business name for branding
            target_roas: Optional target ROAS (e.g., 3.5 for 350%)
            marketing_image_urls: Optional list of image URLs
            logo_image_urls: Optional list of logo image URLs
            
        Returns:
            Dictionary with campaign creation results
        """
        
        try:
            # Validate inputs
            validation_result = validate_pmax_inputs(
                campaign_name, budget_amount_dollars, headlines, 
                descriptions, final_urls, business_name
            )
            
            if not validation_result["valid"]:
                return format_error_response(
                    "Validation Error",
                    validation_result["errors"]
                )
            
            # Format customer ID
            formatted_customer_id = validate_customer_id(customer_id)
            budget_amount_micros = int(budget_amount_dollars * 1_000_000)
            
            # Step 1: Create campaign budget
            budget_resource_name = self._create_campaign_budget(
                formatted_customer_id, 
                f"{campaign_name} Budget", 
                budget_amount_micros
            )
            
            # Step 2: Create Performance Max campaign
            campaign_resource_name = self._create_pmax_campaign(
                formatted_customer_id,
                campaign_name,
                budget_resource_name,
                target_roas
            )
            
            # Step 3: Create text assets
            headline_assets = self._create_text_assets(formatted_customer_id, headlines)
            description_assets = self._create_text_assets(formatted_customer_id, descriptions)
            
            # Step 4: Create asset group with assets
            asset_group_result = self._create_asset_group_with_assets(
                formatted_customer_id,
                campaign_resource_name,
                f"{campaign_name} Asset Group",
                headline_assets,
                description_assets,
                final_urls,
                business_name,
                marketing_image_urls,
                logo_image_urls
            )
            
            campaign_id = campaign_resource_name.split('/')[-1]
            
            return format_pmax_response(
                success=True,
                campaign_resource_name=campaign_resource_name,
                campaign_id=campaign_id,
                campaign_name=campaign_name,
                budget_amount_dollars=budget_amount_dollars,
                asset_group_data=asset_group_result
            )
            
        except Exception as e:
            logger.error(f"Performance Max creation failed: {str(e)}")
            return format_error_response(
                "Performance Max Creation Failed",
                [str(e)]
            )
    
    def _create_campaign_budget(
        self, 
        customer_id: str, 
        budget_name: str, 
        amount_micros: int
    ) -> str:
        """Create a campaign budget and return its resource name"""
        
        try:
            campaign_budget_service = self.client.get_service("CampaignBudgetService")
            campaign_budget_operation = self.client.get_type("CampaignBudgetOperation")
            
            campaign_budget = campaign_budget_operation.create
            campaign_budget.name = budget_name
            campaign_budget.delivery_method = (
                self.client.enums.BudgetDeliveryMethodEnum.STANDARD
            )
            campaign_budget.amount_micros = amount_micros
            
            response = campaign_budget_service.mutate_campaign_budgets(
                customer_id=customer_id,
                operations=[campaign_budget_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as e:
            logger.error(f"Failed to create campaign budget: {e}")
            raise
    
    def _create_pmax_campaign(
        self,
        customer_id: str,
        campaign_name: str,
        budget_resource_name: str,
        target_roas: Optional[float] = None
    ) -> str:
        """Create Performance Max campaign and return its resource name"""
        
        try:
            campaign_service = self.client.get_service("CampaignService")
            campaign_operation = self.client.get_type("CampaignOperation")
            
            campaign = campaign_operation.create
            campaign.name = campaign_name
            campaign.status = getattr(
                self.client.enums.CampaignStatusEnum,
                self.config.default_campaign_status
            )
            campaign.advertising_channel_type = (
                self.client.enums.AdvertisingChannelTypeEnum.PERFORMANCE_MAX
            )
            campaign.campaign_budget = budget_resource_name
            
            # Set bidding strategy
            if target_roas:
                campaign.maximize_conversion_value.target_roas = target_roas
            else:
                campaign.maximize_conversions = self.client.get_type("MaximizeConversions")
            
            # Performance Max specific settings
            campaign.url_expansion_opt_out = False  # Allow URL expansion
            
            response = campaign_service.mutate_campaigns(
                customer_id=customer_id,
                operations=[campaign_operation]
            )
            
            return response.results[0].resource_name
            
        except GoogleAdsException as e:
            logger.error(f"Failed to create Performance Max campaign: {e}")
            raise
    
    def _create_text_assets(self, customer_id: str, texts: List[str]) -> List[str]:
        """Create text assets and return their resource names"""
        
        try:
            asset_service = self.client.get_service("AssetService")
            operations = []
            
            for text in texts:
                asset_operation = self.client.get_type("AssetOperation")
                asset = asset_operation.create
                asset.text_asset.text = text
                operations.append(asset_operation)
            
            response = asset_service.mutate_assets(
                customer_id=customer_id,
                operations=operations
            )
            
            return [result.resource_name for result in response.results]
            
        except GoogleAdsException as e:
            logger.error(f"Failed to create text assets: {e}")
            raise
    
    def _create_asset_group_with_assets(
        self,
        customer_id: str,
        campaign_resource_name: str,
        asset_group_name: str,
        headline_assets: List[str],
        description_assets: List[str],
        final_urls: List[str],
        business_name: str,
        marketing_image_urls: Optional[List[str]] = None,
        logo_image_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create asset group and link all required assets"""
        
        try:
            # Generate unique resource name for asset group
            asset_group_temp_id = str(uuid.uuid4().int)[:10]
            asset_group_resource_name = f"customers/{customer_id}/assetGroups/{asset_group_temp_id}"
            
            operations = []
            
            # 1. Create asset group operation
            asset_group_operation = self.client.get_type("AssetGroupOperation")
            asset_group = asset_group_operation.create
            asset_group.resource_name = asset_group_resource_name
            asset_group.name = asset_group_name
            asset_group.campaign = campaign_resource_name
            asset_group.final_urls.extend(final_urls)
            asset_group.status = self.client.enums.AssetGroupStatusEnum.PAUSED
            
            operations.append({
                "asset_group_operation": asset_group_operation
            })
            
            # 2. Create business name asset and link it
            business_name_asset = self._create_single_text_asset(customer_id, business_name)
            business_name_link_op = self._create_asset_group_asset_operation(
                asset_group_resource_name,
                business_name_asset,
                self.client.enums.AssetFieldTypeEnum.BUSINESS_NAME
            )
            operations.append({
                "asset_group_asset_operation": business_name_link_op
            })
            
            # 3. Link headline assets
            for headline_asset in headline_assets:
                headline_link_op = self._create_asset_group_asset_operation(
                    asset_group_resource_name,
                    headline_asset,
                    self.client.enums.AssetFieldTypeEnum.HEADLINE
                )
                operations.append({
                    "asset_group_asset_operation": headline_link_op
                })
            
            # 4. Link description assets
            for description_asset in description_assets:
                description_link_op = self._create_asset_group_asset_operation(
                    asset_group_resource_name,
                    description_asset,
                    self.client.enums.AssetFieldTypeEnum.DESCRIPTION
                )
                operations.append({
                    "asset_group_asset_operation": description_link_op
                })
            
            # 5. Execute all operations in a single batch
            self._execute_mutate_operations(customer_id, operations)
            
            return {
                "asset_group_name": asset_group_name,
                "asset_group_resource_name": asset_group_resource_name,
                "headlines_count": len(headline_assets),
                "descriptions_count": len(description_assets),
                "business_name": business_name,
                "image_assets": len(marketing_image_urls) if marketing_image_urls else 0,
                "logo_assets": len(logo_image_urls) if logo_image_urls else 0,
                "status": "created"
            }
            
        except Exception as e:
            logger.error(f"Failed to create asset group: {e}")
            raise
    
    def _create_single_text_asset(self, customer_id: str, text: str) -> str:
        """Create a single text asset"""
        assets = self._create_text_assets(customer_id, [text])
        return assets[0]
    
    def _create_asset_group_asset_operation(
        self,
        asset_group_resource_name: str,
        asset_resource_name: str,
        field_type
    ):
        """Create an AssetGroupAsset operation to link asset to asset group"""
        
        asset_group_asset_operation = self.client.get_type("AssetGroupAssetOperation")
        asset_group_asset = asset_group_asset_operation.create
        asset_group_asset.asset_group = asset_group_resource_name
        asset_group_asset.asset = asset_resource_name
        asset_group_asset.field_type = field_type
        
        return asset_group_asset_operation
    
    def _execute_mutate_operations(self, customer_id: str, operations: List[Dict]):
        """Execute multiple operations in a single mutate request"""
        
        try:
            google_ads_service = self.client.get_service("GoogleAdsService")
            mutate_operations = []
            
            for operation in operations:
                mutate_operation = self.client.get_type("MutateOperation")
                
                if "asset_group_operation" in operation:
                    mutate_operation.asset_group_operation = operation["asset_group_operation"]
                elif "asset_group_asset_operation" in operation:
                    mutate_operation.asset_group_asset_operation = operation["asset_group_asset_operation"]
                
                mutate_operations.append(mutate_operation)
            
            response = google_ads_service.mutate(
                customer_id=customer_id,
                mutate_operations=mutate_operations
            )
            
            logger.info(f"Successfully executed {len(mutate_operations)} operations")
            return response
            
        except GoogleAdsException as e:
            logger.error(f"Failed to execute mutate operations: {e}")
            raise
    
    def get_pmax_performance(
        self,
        customer_id: str,
        campaign_id: str,
        date_range: str = "LAST_30_DAYS"
    ) -> Dict[str, Any]:
        """Get performance data for Performance Max campaign"""
        
        try:
            formatted_customer_id = validate_customer_id(customer_id)
            
            query = f"""
                SELECT 
                    campaign.id,
                    campaign.name,
                    asset_group.id,
                    asset_group.name,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.ctr,
                    metrics.conversions,
                    metrics.cost_micros,
                    metrics.conversions_value
                FROM asset_group
                WHERE campaign.id = {campaign_id}
                    AND segments.date DURING {date_range}
            """
            
            google_ads_service = self.client.get_service("GoogleAdsService")
            response = google_ads_service.search(
                customer_id=formatted_customer_id,
                query=query
            )
            
            performance_data = []
            for row in response:
                performance_data.append({
                    "campaign_id": row.campaign.id,
                    "campaign_name": row.campaign.name,
                    "asset_group_id": row.asset_group.id,
                    "asset_group_name": row.asset_group.name,
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "ctr": round(row.metrics.ctr * 100, 2),
                    "conversions": row.metrics.conversions,
                    "cost": row.metrics.cost_micros / 1_000_000,
                    "conversions_value": row.metrics.conversions_value
                })
            
            return {
                "success": True,
                "data": performance_data,
                "date_range": date_range,
                "total_asset_groups": len(performance_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to get Performance Max performance: {e}")
            return format_error_response(
                "Performance Query Failed",
                [str(e)]
            )