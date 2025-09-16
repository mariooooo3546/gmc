"""Integration tests for the complete application."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime
from app.main import app
from app.models import ProductStatusCounts, IssueCode


class TestIntegration:
    """Integration tests for the complete application."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_api_response(self):
        """Mock Merchant API response."""
        return {
            "items": [
                {
                    "status": "APPROVED",
                    "count": 1000
                },
                {
                    "status": "DISAPPROVED",
                    "count": 100,  # High number to trigger alert
                    "issueDetails": [
                        {
                            "code": "MISSING_GTIN",
                            "description": "Product is missing a GTIN",
                            "count": 50
                        },
                        {
                            "code": "IMAGE_LINK_BROKEN",
                            "description": "Product image link is broken",
                            "count": 30
                        }
                    ]
                },
                {
                    "status": "LIMITED",
                    "count": 20,
                    "issueDetails": [
                        {
                            "code": "INVALID_PRICE",
                            "description": "Product price is invalid",
                            "count": 20
                        }
                    ]
                }
            ]
        }
    
    @patch('app.main.alert_service')
    def test_health_endpoint(self, mock_alert_service, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"
    
    @patch('app.main.alert_service')
    def test_run_check_endpoint_success(self, mock_alert_service, client, mock_api_response):
        """Test manual check endpoint with successful result."""
        # Setup mock
        mock_result = {
            "checked_at": "2025-01-16T13:00:00Z",
            "country": "PL",
            "reporting_context": "SHOPPING_ADS",
            "totals": {
                "approved": 1000,
                "disapproved": 100,
                "limited": 20,
                "pending": 0,
                "suspended": 0,
                "under_review": 0,
                "processing": 0
            },
            "delta": {"disapproved": 10},
            "alert_sent": True,
            "top_issues": [
                {
                    "code": "MISSING_GTIN",
                    "description": "Product is missing a GTIN",
                    "count": 50
                }
            ]
        }
        mock_alert_service.run_check.return_value = mock_result
        
        # Make request
        response = client.post("/tasks/run")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["country"] == "PL"
        assert data["totals"]["disapproved"] == 100
        assert data["alert_sent"] is True
        assert len(data["top_issues"]) == 1
        
        # Verify service was called
        mock_alert_service.run_check.assert_called_once()
    
    @patch('app.main.alert_service')
    def test_run_check_endpoint_error(self, mock_alert_service, client):
        """Test manual check endpoint with error."""
        # Setup mock to raise exception
        mock_alert_service.run_check.side_effect = Exception("API Error")
        
        # Make request
        response = client.post("/tasks/run")
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "API Error" in data["detail"]
    
    @patch('app.main.alert_service')
    def test_status_endpoint(self, mock_alert_service, client):
        """Test status endpoint."""
        # Setup mock
        mock_status = {
            "status": "healthy",
            "last_check": "2025-01-16T13:00:00Z",
            "country": "PL",
            "reporting_context": "SHOPPING_ADS",
            "totals": {
                "approved": 1000,
                "disapproved": 25,
                "limited": 5,
                "pending": 10,
                "suspended": 0,
                "under_review": 0,
                "processing": 0
            },
            "delta": {"disapproved": 2},
            "alert_sent": False,
            "trend_24h": {
                "trend": "stable",
                "change": 0,
                "period": "24h"
            },
            "checks_24h": 48
        }
        mock_alert_service.get_status_summary.return_value = mock_status
        
        # Make request
        response = client.get("/status")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["country"] == "PL"
        assert data["totals"]["disapproved"] == 25
        assert data["alert_sent"] is False
        assert data["checks_24h"] == 48
    
    @patch('app.main.alert_service')
    def test_alert_history_endpoint(self, mock_alert_service, client):
        """Test alert history endpoint."""
        # Setup mock
        mock_history = [
            {
                "timestamp": "2025-01-16T13:00:00Z",
                "country": "PL",
                "reporting_context": "SHOPPING_ADS",
                "totals": {
                    "approved": 1000,
                    "disapproved": 50,
                    "limited": 10,
                    "pending": 0,
                    "suspended": 0,
                    "under_review": 0,
                    "processing": 0
                },
                "delta_disapproved": 15,
                "top_issues": [
                    {
                        "code": "MISSING_GTIN",
                        "description": "Product is missing a GTIN",
                        "count": 25
                    }
                ]
            }
        ]
        mock_alert_service.get_alert_history.return_value = mock_history
        
        # Make request
        response = client.get("/alerts/history")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["country"] == "PL"
        assert data[0]["delta_disapproved"] == 15
        assert len(data[0]["top_issues"]) == 1
    
    @patch('app.main.alert_service')
    def test_alert_history_endpoint_with_limit(self, mock_alert_service, client):
        """Test alert history endpoint with custom limit."""
        # Setup mock
        mock_alert_service.get_alert_history.return_value = []
        
        # Make request with limit
        response = client.get("/alerts/history?limit=5")
        
        # Verify response
        assert response.status_code == 200
        mock_alert_service.get_alert_history.assert_called_once_with(limit=5)
    
    @patch('app.main.alert_service')
    def test_alert_history_endpoint_limit_cap(self, mock_alert_service, client):
        """Test alert history endpoint with limit cap."""
        # Setup mock
        mock_alert_service.get_alert_history.return_value = []
        
        # Make request with high limit (should be capped at 50)
        response = client.get("/alerts/history?limit=100")
        
        # Verify response
        assert response.status_code == 200
        mock_alert_service.get_alert_history.assert_called_once_with(limit=50)
    
    @patch('app.main.db_service')
    @patch('app.main.alert_service')
    def test_dashboard_endpoint(self, mock_alert_service, mock_db_service, client):
        """Test dashboard endpoint."""
        # Setup mocks
        mock_status = {
            "status": "healthy",
            "last_check": "2025-01-16T13:00:00Z",
            "country": "PL",
            "reporting_context": "SHOPPING_ADS",
            "totals": {
                "approved": 1000,
                "disapproved": 25,
                "limited": 5,
                "pending": 10,
                "suspended": 0,
                "under_review": 0,
                "processing": 0
            },
            "delta": {"disapproved": 2},
            "alert_sent": False
        }
        mock_alert_service.get_status_summary.return_value = mock_status
        mock_alert_service.get_alert_history.return_value = []
        mock_db_service.get_snapshots_last_24h.return_value = []
        
        # Make request
        response = client.get("/dashboard")
        
        # Verify response
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Merchant Center Monitor" in response.text
        assert "PL" in response.text
    
    @patch('app.main.db_service')
    @patch('app.main.alert_service')
    def test_dashboard_endpoint_error(self, mock_alert_service, mock_db_service, client):
        """Test dashboard endpoint with error."""
        # Setup mock to raise exception
        mock_alert_service.get_status_summary.side_effect = Exception("Database Error")
        
        # Make request
        response = client.get("/dashboard")
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "Dashboard error" in data["detail"]
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Merchant Center Monitor" in response.text
        assert "/dashboard" in response.text
        assert "/status" in response.text
    
    @patch('app.main.settings')
    def test_root_endpoint_with_settings(self, mock_settings, client):
        """Test root endpoint displays settings."""
        # Setup mock settings
        mock_settings.alert_country = "PL"
        mock_settings.alert_reporting_context = "SHOPPING_ADS"
        mock_settings.alert_threshold_abs = 25
        mock_settings.alert_threshold_delta = 10
        
        response = client.get("/")
        
        assert response.status_code == 200
        assert "PL" in response.text
        assert "SHOPPING_ADS" in response.text
        assert "25" in response.text
        assert "10" in response.text


class TestEndToEndFlow:
    """End-to-end flow tests."""
    
    @patch('app.main.merchant_api')
    @patch('app.main.db_service')
    @patch('app.main.email_service')
    @patch('app.main.settings')
    def test_complete_alert_flow(self, mock_settings, mock_email_service, 
                                mock_db_service, mock_merchant_api):
        """Test complete flow from API call to email alert."""
        from app.alert_service import AlertService
        
        # Setup mocks
        mock_settings.alert_country = "PL"
        mock_settings.alert_reporting_context = "SHOPPING_ADS"
        mock_settings.alert_threshold_abs = 50  # Lower than problematic total
        mock_settings.alert_threshold_delta = 5
        
        # Mock API response with high disapproved count
        mock_api_response = {
            "items": [
                {
                    "status": "APPROVED",
                    "count": 1000
                },
                {
                    "status": "DISAPPROVED",
                    "count": 60,  # High enough to trigger alert
                    "issueDetails": [
                        {
                            "code": "MISSING_GTIN",
                            "description": "Product is missing a GTIN",
                            "count": 30
                        }
                    ]
                }
            ]
        }
        
        mock_merchant_api.get_aggregate_product_statuses.return_value = mock_api_response
        mock_merchant_api.parse_product_status_counts.return_value = ProductStatusCounts(
            approved=1000,
            disapproved=60
        )
        mock_merchant_api.get_top_issue_codes.return_value = [
            IssueCode(code="MISSING_GTIN", description="Missing GTIN", count=30)
        ]
        
        # Mock database
        mock_db_service.get_latest_snapshot.return_value = None
        mock_db_service.save_snapshot.return_value = "snapshot_id"
        
        # Mock email service
        mock_email_service.send_alert_email.return_value = True
        
        # Run the complete flow
        alert_service = AlertService()
        result = alert_service.run_check()
        
        # Verify result
        assert result["alert_sent"] is True
        assert result["totals"]["disapproved"] == 60
        assert result["country"] == "PL"
        
        # Verify all services were called
        mock_merchant_api.get_aggregate_product_statuses.assert_called_once()
        mock_db_service.save_snapshot.assert_called_once()
        mock_email_service.send_alert_email.assert_called_once()
        
        # Verify email was called with correct parameters
        call_args = mock_email_service.send_alert_email.call_args
        assert call_args[1]["totals"].disapproved == 60
        assert call_args[1]["country"] == "PL"
        assert call_args[1]["reporting_context"] == "SHOPPING_ADS"
