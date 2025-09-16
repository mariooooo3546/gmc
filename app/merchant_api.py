"""Google Merchant API integration for product status monitoring."""

import logging
import time
from typing import Dict, List, Optional
import httpx
from google.auth.exceptions import GoogleAuthError

from .auth import auth_service
from .config import settings
from .models import ProductStatusCounts, IssueCode

logger = logging.getLogger(__name__)


class MerchantAPIService:
    """Service for interacting with Google Merchant API."""
    
    BASE_URL = "https://merchantapi.googleapis.com"
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
    
    def _make_request(self, method: str, url: str, params: Optional[Dict] = None, max_retries: int = 3) -> Dict:
        """Make authenticated request to Merchant API with retry logic."""
        for attempt in range(max_retries):
            try:
                token = auth_service.get_access_token()
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                response = self.client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limit - exponential backoff
                    wait_time = (2 ** attempt) * 60  # 1min, 2min, 4min
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                    time.sleep(wait_time)
                    continue
                elif response.status_code >= 500:
                    # Server error - retry with backoff
                    wait_time = (2 ** attempt) * 10  # 10s, 20s, 40s
                    logger.warning(f"Server error {response.status_code}, retrying in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                else:
                    # Client error - don't retry
                    logger.error(f"API request failed: {response.status_code} - {response.text}")
                    response.raise_for_status()
                    
            except httpx.TimeoutException:
                logger.warning(f"Request timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep((2 ** attempt) * 5)
                    continue
                raise
            except GoogleAuthError:
                # Token might be expired, try to refresh
                logger.warning("Authentication error, refreshing token")
                auth_service.refresh_token()
                if attempt < max_retries - 1:
                    continue
                raise
            except Exception as e:
                logger.error(f"Unexpected error in API request: {e}")
                if attempt < max_retries - 1:
                    time.sleep((2 ** attempt) * 5)
                    continue
                raise
        
        raise Exception(f"Failed to make API request after {max_retries} attempts")
    
    def get_aggregate_product_statuses(self, country: str = None, reporting_context: str = None) -> Dict:
        """Get aggregated product statuses from Merchant API."""
        country = country or settings.alert_country
        reporting_context = reporting_context or settings.alert_reporting_context
        
        url = f"{self.BASE_URL}/issueresolution/v1/accounts/{settings.merchant_account_id}/aggregateProductStatuses"
        
        # Build filter query
        filter_parts = []
        if reporting_context:
            filter_parts.append(f'reporting_context="{reporting_context}"')
        if country:
            filter_parts.append(f'country="{country}"')
        
        filter_query = " AND ".join(filter_parts)
        
        params = {
            "filter": filter_query,
            "pageSize": 250
        }
        
        logger.info(f"Fetching aggregate product statuses for country={country}, context={reporting_context}")
        
        try:
            response = self._make_request("GET", url, params=params)
            logger.info(f"Successfully fetched {len(response.get('items', []))} status items")
            return response
        except Exception as e:
            logger.error(f"Failed to fetch aggregate product statuses: {e}")
            raise
    
    def parse_product_status_counts(self, api_response: Dict) -> ProductStatusCounts:
        """Parse API response into ProductStatusCounts model."""
        counts = ProductStatusCounts()
        
        items = api_response.get("items", [])
        for item in items:
            status = item.get("status", "").upper()
            count = item.get("count", 0)
            
            if status == "APPROVED":
                counts.approved += count
            elif status == "PENDING":
                counts.pending += count
            elif status == "DISAPPROVED":
                counts.disapproved += count
            elif status == "LIMITED":
                counts.limited += count
            elif status == "SUSPENDED":
                counts.suspended += count
            elif status == "UNDER_REVIEW":
                counts.under_review += count
            elif status == "PROCESSING":
                counts.processing += count
        
        logger.info(f"Parsed status counts: {counts}")
        return counts
    
    def get_top_issue_codes(self, api_response: Dict, limit: int = 5) -> List[IssueCode]:
        """Extract top issue codes from API response."""
        issues = []
        
        items = api_response.get("items", [])
        for item in items:
            if item.get("status", "").upper() in ["DISAPPROVED", "LIMITED", "SUSPENDED"]:
                issue_details = item.get("issueDetails", [])
                for detail in issue_details:
                    code = detail.get("code", "")
                    description = detail.get("description", "")
                    count = detail.get("count", 0)
                    
                    if code and count > 0:
                        issues.append(IssueCode(
                            code=code,
                            description=description,
                            count=count
                        ))
        
        # Sort by count descending and return top N
        issues.sort(key=lambda x: x.count, reverse=True)
        return issues[:limit]
    
    def get_products_with_issues(self, page_size: int = 100) -> Dict:
        """Get detailed list of products with issues."""
        url = f"{self.BASE_URL}/products/v1/accounts/{settings.merchant_account_id}/products"
        
        params = {
            "pageSize": page_size,
            "filter": 'status="DISAPPROVED" OR status="LIMITED" OR status="SUSPENDED"'
        }
        
        logger.info(f"Fetching products with issues (page_size={page_size})")
        
        try:
            response = self._make_request("GET", url, params=params)
            logger.info(f"Successfully fetched {len(response.get('products', []))} products with issues")
            return response
        except Exception as e:
            logger.error(f"Failed to fetch products with issues: {e}")
            raise


# Global service instance
merchant_api = MerchantAPIService()
