"""Tests for data models."""

import pytest
from datetime import datetime
from app.models import (
    ProductStatusCounts,
    IssueCode,
    ProductStatusSnapshot,
    AlertThresholds,
    EmailAlert,
    HealthStatus,
    CheckResult
)


class TestProductStatusCounts:
    """Test ProductStatusCounts model."""
    
    def test_default_values(self):
        """Test default values are zero."""
        counts = ProductStatusCounts()
        assert counts.approved == 0
        assert counts.pending == 0
        assert counts.disapproved == 0
        assert counts.limited == 0
        assert counts.suspended == 0
        assert counts.under_review == 0
        assert counts.processing == 0
    
    def test_custom_values(self):
        """Test custom values."""
        counts = ProductStatusCounts(
            approved=100,
            pending=10,
            disapproved=5,
            limited=2,
            suspended=1
        )
        assert counts.approved == 100
        assert counts.pending == 10
        assert counts.disapproved == 5
        assert counts.limited == 2
        assert counts.suspended == 1
    
    def test_dict_conversion(self):
        """Test conversion to dict."""
        counts = ProductStatusCounts(approved=50, disapproved=10)
        data = counts.dict()
        assert data["approved"] == 50
        assert data["disapproved"] == 10
        assert data["pending"] == 0


class TestIssueCode:
    """Test IssueCode model."""
    
    def test_issue_code_creation(self):
        """Test IssueCode creation."""
        issue = IssueCode(
            code="MISSING_GTIN",
            description="Product is missing a GTIN",
            count=25
        )
        assert issue.code == "MISSING_GTIN"
        assert issue.description == "Product is missing a GTIN"
        assert issue.count == 25


class TestProductStatusSnapshot:
    """Test ProductStatusSnapshot model."""
    
    def test_snapshot_creation(self):
        """Test snapshot creation."""
        timestamp = datetime.utcnow()
        totals = ProductStatusCounts(approved=100, disapproved=5)
        issues = [IssueCode(code="TEST", description="Test issue", count=1)]
        
        snapshot = ProductStatusSnapshot(
            timestamp=timestamp,
            country="PL",
            reporting_context="SHOPPING_ADS",
            totals=totals,
            delta_disapproved=2,
            alert_sent=True,
            top_issues=issues
        )
        
        assert snapshot.timestamp == timestamp
        assert snapshot.country == "PL"
        assert snapshot.reporting_context == "SHOPPING_ADS"
        assert snapshot.totals.approved == 100
        assert snapshot.delta_disapproved == 2
        assert snapshot.alert_sent is True
        assert len(snapshot.top_issues) == 1


class TestAlertThresholds:
    """Test AlertThresholds model."""
    
    def test_thresholds_creation(self):
        """Test AlertThresholds creation."""
        thresholds = AlertThresholds(
            absolute_threshold=25,
            delta_threshold=10,
            country="PL",
            reporting_context="SHOPPING_ADS"
        )
        assert thresholds.absolute_threshold == 25
        assert thresholds.delta_threshold == 10
        assert thresholds.country == "PL"
        assert thresholds.reporting_context == "SHOPPING_ADS"


class TestEmailAlert:
    """Test EmailAlert model."""
    
    def test_email_alert_creation(self):
        """Test EmailAlert creation."""
        timestamp = datetime.utcnow()
        alert = EmailAlert(
            to="admin@example.com",
            subject="Test Alert",
            body="Test body",
            sent_at=timestamp
        )
        assert alert.to == "admin@example.com"
        assert alert.subject == "Test Alert"
        assert alert.body == "Test body"
        assert alert.sent_at == timestamp


class TestHealthStatus:
    """Test HealthStatus model."""
    
    def test_health_status_creation(self):
        """Test HealthStatus creation."""
        timestamp = datetime.utcnow()
        health = HealthStatus(
            status="healthy",
            timestamp=timestamp
        )
        assert health.status == "healthy"
        assert health.timestamp == timestamp
        assert health.version == "1.0.0"  # Default value


class TestCheckResult:
    """Test CheckResult model."""
    
    def test_check_result_creation(self):
        """Test CheckResult creation."""
        timestamp = datetime.utcnow()
        totals = ProductStatusCounts(approved=100, disapproved=5)
        issues = [IssueCode(code="TEST", description="Test", count=1)]
        
        result = CheckResult(
            checked_at=timestamp,
            country="PL",
            reporting_context="SHOPPING_ADS",
            totals=totals,
            delta={"disapproved": 2},
            alert_sent=True,
            top_issues=issues
        )
        
        assert result.checked_at == timestamp
        assert result.country == "PL"
        assert result.totals.approved == 100
        assert result.delta["disapproved"] == 2
        assert result.alert_sent is True
