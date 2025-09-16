"""Tests for alert service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from app.alert_service import AlertService
from app.models import ProductStatusCounts, ProductStatusSnapshot, IssueCode


class TestAlertService:
    """Test AlertService."""
    
    @pytest.fixture
    def alert_service(self):
        """Create alert service instance."""
        return AlertService()
    
    @pytest.fixture
    def mock_totals(self):
        """Mock product status totals."""
        return ProductStatusCounts(
            approved=1000,
            pending=50,
            disapproved=30,
            limited=5,
            suspended=2,
            under_review=10,
            processing=3
        )
    
    @pytest.fixture
    def mock_issues(self):
        """Mock issue codes."""
        return [
            IssueCode(code="MISSING_GTIN", description="Missing GTIN", count=15),
            IssueCode(code="IMAGE_BROKEN", description="Broken image", count=10),
            IssueCode(code="INVALID_PRICE", description="Invalid price", count=5)
        ]
    
    def test_should_send_alert_absolute_threshold_exceeded(self, alert_service, mock_totals):
        """Test alert when absolute threshold is exceeded."""
        # Mock settings with low threshold
        with patch('app.alert_service.settings') as mock_settings:
            mock_settings.alert_threshold_abs = 20  # Lower than problematic total (37)
            mock_settings.alert_threshold_delta = 10
            
            should_alert = alert_service._should_send_alert(mock_totals, 0)
            assert should_alert is True
    
    def test_should_send_alert_delta_threshold_exceeded(self, alert_service, mock_totals):
        """Test alert when delta threshold is exceeded."""
        # Mock settings
        with patch('app.alert_service.settings') as mock_settings:
            mock_settings.alert_threshold_abs = 100  # Higher than problematic total
            mock_settings.alert_threshold_delta = 5  # Lower than delta
            
            should_alert = alert_service._should_send_alert(mock_totals, 15)
            assert should_alert is True
    
    def test_should_not_send_alert_thresholds_not_exceeded(self, alert_service, mock_totals):
        """Test no alert when thresholds are not exceeded."""
        # Mock settings with high thresholds
        with patch('app.alert_service.settings') as mock_settings:
            mock_settings.alert_threshold_abs = 100  # Higher than problematic total
            mock_settings.alert_threshold_delta = 50  # Higher than delta
            
            should_alert = alert_service._should_send_alert(mock_totals, 5)
            assert should_alert is False
    
    def test_calculate_trend_increasing(self, alert_service):
        """Test trend calculation for increasing disapproved count."""
        snapshots = [
            ProductStatusSnapshot(
                timestamp=datetime.utcnow(),
                country="PL",
                reporting_context="SHOPPING_ADS",
                totals=ProductStatusCounts(disapproved=10),
                delta_disapproved=0,
                alert_sent=False
            ),
            ProductStatusSnapshot(
                timestamp=datetime.utcnow(),
                country="PL",
                reporting_context="SHOPPING_ADS",
                totals=ProductStatusCounts(disapproved=20),
                delta_disapproved=10,
                alert_sent=False
            )
        ]
        
        trend = alert_service._calculate_trend(snapshots)
        assert trend["trend"] == "increasing"
        assert trend["change"] == 10
    
    def test_calculate_trend_decreasing(self, alert_service):
        """Test trend calculation for decreasing disapproved count."""
        snapshots = [
            ProductStatusSnapshot(
                timestamp=datetime.utcnow(),
                country="PL",
                reporting_context="SHOPPING_ADS",
                totals=ProductStatusCounts(disapproved=20),
                delta_disapproved=0,
                alert_sent=False
            ),
            ProductStatusSnapshot(
                timestamp=datetime.utcnow(),
                country="PL",
                reporting_context="SHOPPING_ADS",
                totals=ProductStatusCounts(disapproved=10),
                delta_disapproved=-10,
                alert_sent=False
            )
        ]
        
        trend = alert_service._calculate_trend(snapshots)
        assert trend["trend"] == "decreasing"
        assert trend["change"] == -10
    
    def test_calculate_trend_stable(self, alert_service):
        """Test trend calculation for stable disapproved count."""
        snapshots = [
            ProductStatusSnapshot(
                timestamp=datetime.utcnow(),
                country="PL",
                reporting_context="SHOPPING_ADS",
                totals=ProductStatusCounts(disapproved=15),
                delta_disapproved=0,
                alert_sent=False
            ),
            ProductStatusSnapshot(
                timestamp=datetime.utcnow(),
                country="PL",
                reporting_context="SHOPPING_ADS",
                totals=ProductStatusCounts(disapproved=15),
                delta_disapproved=0,
                alert_sent=False
            )
        ]
        
        trend = alert_service._calculate_trend(snapshots)
        assert trend["trend"] == "stable"
        assert trend["change"] == 0
    
    def test_calculate_trend_insufficient_data(self, alert_service):
        """Test trend calculation with insufficient data."""
        snapshots = [
            ProductStatusSnapshot(
                timestamp=datetime.utcnow(),
                country="PL",
                reporting_context="SHOPPING_ADS",
                totals=ProductStatusCounts(disapproved=10),
                delta_disapproved=0,
                alert_sent=False
            )
        ]
        
        trend = alert_service._calculate_trend(snapshots)
        assert trend["trend"] == "insufficient_data"
        assert trend["change"] == 0
    
    @patch('app.alert_service.merchant_api')
    @patch('app.alert_service.db_service')
    @patch('app.alert_service.email_service')
    @patch('app.alert_service.settings')
    def test_run_check_success_no_alert(self, mock_settings, mock_email_service, 
                                       mock_db_service, mock_merchant_api, alert_service):
        """Test successful check run without alert."""
        # Setup mocks
        mock_settings.alert_country = "PL"
        mock_settings.alert_reporting_context = "SHOPPING_ADS"
        
        mock_api_response = {"items": []}
        mock_merchant_api.get_aggregate_product_statuses.return_value = mock_api_response
        mock_merchant_api.parse_product_status_counts.return_value = ProductStatusCounts()
        mock_merchant_api.get_top_issue_codes.return_value = []
        
        mock_db_service.get_latest_snapshot.return_value = None
        mock_db_service.save_snapshot.return_value = "snapshot_id"
        
        # Mock alert thresholds (high to prevent alert)
        mock_settings.alert_threshold_abs = 1000
        mock_settings.alert_threshold_delta = 1000
        
        # Run check
        result = alert_service.run_check()
        
        # Verify result
        assert result["alert_sent"] is False
        assert result["country"] == "PL"
        assert result["reporting_context"] == "SHOPPING_ADS"
        assert result["delta"]["disapproved"] == 0
        
        # Verify calls
        mock_merchant_api.get_aggregate_product_statuses.assert_called_once()
        mock_db_service.save_snapshot.assert_called_once()
        mock_email_service.send_alert_email.assert_not_called()
    
    @patch('app.alert_service.merchant_api')
    @patch('app.alert_service.db_service')
    @patch('app.alert_service.email_service')
    @patch('app.alert_service.settings')
    def test_run_check_success_with_alert(self, mock_settings, mock_email_service, 
                                         mock_db_service, mock_merchant_api, alert_service, 
                                         mock_totals, mock_issues):
        """Test successful check run with alert."""
        # Setup mocks
        mock_settings.alert_country = "PL"
        mock_settings.alert_reporting_context = "SHOPPING_ADS"
        
        mock_api_response = {"items": []}
        mock_merchant_api.get_aggregate_product_statuses.return_value = mock_api_response
        mock_merchant_api.parse_product_status_counts.return_value = mock_totals
        mock_merchant_api.get_top_issue_codes.return_value = mock_issues
        
        mock_db_service.get_latest_snapshot.return_value = None
        mock_db_service.save_snapshot.return_value = "snapshot_id"
        
        # Mock alert thresholds (low to trigger alert)
        mock_settings.alert_threshold_abs = 20  # Lower than problematic total (37)
        mock_settings.alert_threshold_delta = 5
        
        mock_email_service.send_alert_email.return_value = True
        
        # Run check
        result = alert_service.run_check()
        
        # Verify result
        assert result["alert_sent"] is True
        assert result["country"] == "PL"
        assert result["totals"]["disapproved"] == 30
        
        # Verify calls
        mock_merchant_api.get_aggregate_product_statuses.assert_called_once()
        mock_db_service.save_snapshot.assert_called_once()
        mock_email_service.send_alert_email.assert_called_once()
    
    @patch('app.alert_service.merchant_api')
    def test_run_check_api_error(self, mock_merchant_api, alert_service):
        """Test check run with API error."""
        # Setup mock to raise exception
        mock_merchant_api.get_aggregate_product_statuses.side_effect = Exception("API Error")
        
        # Run check - should raise exception
        with pytest.raises(Exception, match="API Error"):
            alert_service.run_check()
    
    @patch('app.alert_service.db_service')
    def test_get_status_summary_no_data(self, mock_db_service, alert_service):
        """Test status summary with no previous data."""
        mock_db_service.get_latest_snapshot.return_value = None
        mock_db_service.get_snapshots_last_24h.return_value = []
        
        result = alert_service.get_status_summary()
        
        assert result["status"] == "no_data"
        assert result["message"] == "No previous checks found"
        assert result["last_check"] is None
    
    @patch('app.alert_service.db_service')
    def test_get_status_summary_with_data(self, mock_db_service, alert_service, mock_totals):
        """Test status summary with previous data."""
        # Setup mock snapshot
        mock_snapshot = ProductStatusSnapshot(
            timestamp=datetime.utcnow(),
            country="PL",
            reporting_context="SHOPPING_ADS",
            totals=mock_totals,
            delta_disapproved=5,
            alert_sent=False,
            top_issues=[]
        )
        
        mock_db_service.get_latest_snapshot.return_value = mock_snapshot
        mock_db_service.get_snapshots_last_24h.return_value = [mock_snapshot]
        
        result = alert_service.get_status_summary()
        
        assert result["status"] == "healthy"
        assert result["country"] == "PL"
        assert result["totals"]["disapproved"] == 30
        assert result["delta"]["disapproved"] == 5
        assert result["alert_sent"] is False
    
    @patch('app.alert_service.db_service')
    def test_get_alert_history(self, mock_db_service, alert_service, mock_totals):
        """Test getting alert history."""
        # Setup mock snapshots
        mock_snapshots = [
            ProductStatusSnapshot(
                timestamp=datetime.utcnow(),
                country="PL",
                reporting_context="SHOPPING_ADS",
                totals=mock_totals,
                delta_disapproved=10,
                alert_sent=True,
                top_issues=[]
            )
        ]
        
        mock_db_service.get_alert_history.return_value = mock_snapshots
        
        result = alert_service.get_alert_history(limit=5)
        
        assert len(result) == 1
        assert result[0]["alert_sent"] is True
        assert result[0]["delta_disapproved"] == 10
