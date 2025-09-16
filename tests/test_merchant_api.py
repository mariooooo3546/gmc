"""Tests for Merchant API service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.merchant_api import MerchantAPIService
from app.models import ProductStatusCounts, IssueCode


class TestMerchantAPIService:
    """Test MerchantAPIService."""
    
    @pytest.fixture
    def api_service(self):
        """Create API service instance."""
        return MerchantAPIService()
    
    @pytest.fixture
    def mock_api_response(self):
        """Mock API response data."""
        return {
            "items": [
                {
                    "status": "APPROVED",
                    "count": 1000
                },
                {
                    "status": "PENDING",
                    "count": 50
                },
                {
                    "status": "DISAPPROVED",
                    "count": 25,
                    "issueDetails": [
                        {
                            "code": "MISSING_GTIN",
                            "description": "Product is missing a GTIN",
                            "count": 15
                        },
                        {
                            "code": "IMAGE_LINK_BROKEN",
                            "description": "Product image link is broken",
                            "count": 10
                        }
                    ]
                },
                {
                    "status": "LIMITED",
                    "count": 5,
                    "issueDetails": [
                        {
                            "code": "INVALID_PRICE",
                            "description": "Product price is invalid",
                            "count": 5
                        }
                    ]
                }
            ]
        }
    
    def test_parse_product_status_counts(self, api_service, mock_api_response):
        """Test parsing API response into ProductStatusCounts."""
        counts = api_service.parse_product_status_counts(mock_api_response)
        
        assert counts.approved == 1000
        assert counts.pending == 50
        assert counts.disapproved == 25
        assert counts.limited == 5
        assert counts.suspended == 0
        assert counts.under_review == 0
        assert counts.processing == 0
    
    def test_parse_product_status_counts_empty_response(self, api_service):
        """Test parsing empty API response."""
        empty_response = {"items": []}
        counts = api_service.parse_product_status_counts(empty_response)
        
        assert counts.approved == 0
        assert counts.pending == 0
        assert counts.disapproved == 0
        assert counts.limited == 0
        assert counts.suspended == 0
    
    def test_get_top_issue_codes(self, api_service, mock_api_response):
        """Test extracting top issue codes."""
        issues = api_service.get_top_issue_codes(mock_api_response, limit=3)
        
        assert len(issues) == 3
        assert issues[0].code == "MISSING_GTIN"
        assert issues[0].count == 15
        assert issues[1].code == "IMAGE_LINK_BROKEN"
        assert issues[1].count == 10
        assert issues[2].code == "INVALID_PRICE"
        assert issues[2].count == 5
    
    def test_get_top_issue_codes_limit(self, api_service, mock_api_response):
        """Test limiting number of issue codes."""
        issues = api_service.get_top_issue_codes(mock_api_response, limit=2)
        
        assert len(issues) == 2
        assert issues[0].code == "MISSING_GTIN"
        assert issues[1].code == "IMAGE_LINK_BROKEN"
    
    def test_get_top_issue_codes_no_issues(self, api_service):
        """Test with no issues in response."""
        response_without_issues = {
            "items": [
                {
                    "status": "APPROVED",
                    "count": 1000
                }
            ]
        }
        issues = api_service.get_top_issue_codes(response_without_issues)
        
        assert len(issues) == 0
    
    @patch('app.merchant_api.auth_service')
    @patch('app.merchant_api.httpx.Client')
    def test_make_request_success(self, mock_client_class, mock_auth_service, api_service):
        """Test successful API request."""
        # Setup mocks
        mock_auth_service.get_access_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        # Create new service instance to use mocked client
        service = MerchantAPIService()
        service.client = mock_client
        
        # Make request
        result = service._make_request("GET", "https://test.com")
        
        assert result == {"success": True}
        mock_client.request.assert_called_once()
    
    @patch('app.merchant_api.auth_service')
    @patch('app.merchant_api.httpx.Client')
    def test_make_request_rate_limit_retry(self, mock_client_class, mock_auth_service, api_service):
        """Test retry logic for rate limiting."""
        # Setup mocks
        mock_auth_service.get_access_token.return_value = "test_token"
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"success": True}
        
        mock_client = Mock()
        mock_client.request.side_effect = [mock_response_429, mock_response_200]
        mock_client_class.return_value = mock_client
        
        # Create new service instance
        service = MerchantAPIService()
        service.client = mock_client
        
        # Make request with retry
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = service._make_request("GET", "https://test.com", max_retries=2)
        
        assert result == {"success": True}
        assert mock_client.request.call_count == 2
    
    @patch('app.merchant_api.auth_service')
    @patch('app.merchant_api.httpx.Client')
    def test_make_request_server_error_retry(self, mock_client_class, mock_auth_service, api_service):
        """Test retry logic for server errors."""
        # Setup mocks
        mock_auth_service.get_access_token.return_value = "test_token"
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"success": True}
        
        mock_client = Mock()
        mock_client.request.side_effect = [mock_response_500, mock_response_200]
        mock_client_class.return_value = mock_client
        
        # Create new service instance
        service = MerchantAPIService()
        service.client = mock_client
        
        # Make request with retry
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = service._make_request("GET", "https://test.com", max_retries=2)
        
        assert result == {"success": True}
        assert mock_client.request.call_count == 2
    
    @patch('app.merchant_api.auth_service')
    @patch('app.merchant_api.httpx.Client')
    def test_make_request_client_error_no_retry(self, mock_client_class, mock_auth_service, api_service):
        """Test that client errors are not retried."""
        # Setup mocks
        mock_auth_service.get_access_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        
        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        # Create new service instance
        service = MerchantAPIService()
        service.client = mock_client
        
        # Make request - should not retry on 400
        with pytest.raises(Exception):
            service._make_request("GET", "https://test.com")
        
        # Should only be called once (no retry)
        assert mock_client.request.call_count == 1
    
    @patch('app.merchant_api.auth_service')
    @patch('app.merchant_api.httpx.Client')
    def test_make_request_max_retries_exceeded(self, mock_client_class, mock_auth_service, api_service):
        """Test behavior when max retries are exceeded."""
        # Setup mocks
        mock_auth_service.get_access_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 500
        
        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        # Create new service instance
        service = MerchantAPIService()
        service.client = mock_client
        
        # Make request with limited retries
        with patch('time.sleep'):  # Mock sleep to speed up test
            with pytest.raises(Exception, match="Failed to make API request after 2 attempts"):
                service._make_request("GET", "https://test.com", max_retries=2)
        
        # Should be called max_retries times
        assert mock_client.request.call_count == 2
