"""Alert service for monitoring product statuses - Development version."""

import logging
from datetime import datetime
from typing import Tuple

from .config import settings
from .models import ProductStatusCounts, ProductStatusSnapshot, IssueCode
from .database_mock import db_service  # Use mock database

logger = logging.getLogger(__name__)


class AlertServiceDev:
    """Development version of alert service with mock data."""
    
    def run_check(self) -> dict:
        """Run a mock product status check."""
        logger.info("Starting mock product status check")
        
        try:
            # Mock current totals
            current_totals = ProductStatusCounts(
                approved=1000,
                pending=50,
                disapproved=25,
                limited=5,
                suspended=2,
                under_review=10,
                processing=3
            )
            
            # Mock top issues
            top_issues = [
                IssueCode(code="MISSING_GTIN", description="Product is missing a GTIN", count=10),
                IssueCode(code="IMAGE_LINK_BROKEN", description="Product image link is broken", count=8),
                IssueCode(code="INVALID_PRICE", description="Product price is invalid", count=5)
            ]
            
            # Get previous snapshot for delta calculation
            previous_snapshot = db_service.get_latest_snapshot()
            
            # Calculate delta
            delta_disapproved = 5  # Mock delta
            if previous_snapshot:
                delta_disapproved = current_totals.disapproved - previous_snapshot.totals.disapproved
            
            # Check if alert should be sent
            alert_sent = self._should_send_alert(current_totals, delta_disapproved)
            
            # Create and save snapshot
            snapshot = ProductStatusSnapshot(
                timestamp=datetime.utcnow(),
                country=settings.alert_country,
                reporting_context=settings.alert_reporting_context,
                totals=current_totals,
                delta_disapproved=delta_disapproved,
                alert_sent=alert_sent,
                top_issues=top_issues
            )
            
            snapshot_id = db_service.save_snapshot(snapshot)
            logger.info(f"Saved mock snapshot with ID: {snapshot_id}")
            
            # Prepare result
            result = {
                "checked_at": snapshot.timestamp.isoformat(),
                "country": snapshot.country,
                "reporting_context": snapshot.reporting_context,
                "totals": current_totals.dict(),
                "delta": {"disapproved": delta_disapproved},
                "alert_sent": alert_sent,
                "top_issues": [issue.dict() for issue in top_issues]
            }
            
            logger.info(f"Mock check completed successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during mock product status check: {e}")
            raise
    
    def _should_send_alert(self, totals: ProductStatusCounts, delta_disapproved: int) -> bool:
        """Determine if an alert should be sent based on thresholds."""
        
        # Calculate total problematic products
        problematic_total = totals.disapproved + totals.suspended + totals.limited
        
        # Check absolute threshold
        if problematic_total > settings.alert_threshold_abs:
            logger.warning(f"Absolute threshold exceeded: {problematic_total} > {settings.alert_threshold_abs}")
            return True
        
        # Check delta threshold
        if delta_disapproved >= settings.alert_threshold_delta:
            logger.warning(f"Delta threshold exceeded: {delta_disapproved} >= {settings.alert_threshold_delta}")
            return True
        
        logger.info(f"Thresholds not exceeded: problematic={problematic_total}, delta={delta_disapproved}")
        return False
    
    def get_status_summary(self) -> dict:
        """Get current status summary for API endpoint."""
        try:
            # Get latest snapshot
            latest_snapshot = db_service.get_latest_snapshot()
            
            if not latest_snapshot:
                return {
                    "status": "no_data",
                    "message": "No previous checks found",
                    "last_check": None
                }
            
            # Get 24h history for trend analysis
            snapshots_24h = db_service.get_snapshots_last_24h()
            
            # Calculate trend
            trend = self._calculate_trend(snapshots_24h)
            
            return {
                "status": "healthy" if not latest_snapshot.alert_sent else "alert",
                "last_check": latest_snapshot.timestamp.isoformat(),
                "country": latest_snapshot.country,
                "reporting_context": latest_snapshot.reporting_context,
                "totals": latest_snapshot.totals.dict(),
                "delta": {"disapproved": latest_snapshot.delta_disapproved},
                "alert_sent": latest_snapshot.alert_sent,
                "trend_24h": trend,
                "checks_24h": len(snapshots_24h)
            }
            
        except Exception as e:
            logger.error(f"Error getting status summary: {e}")
            return {
                "status": "error",
                "message": str(e),
                "last_check": None
            }
    
    def _calculate_trend(self, snapshots_24h: list) -> dict:
        """Calculate trend from 24h snapshots."""
        if len(snapshots_24h) < 2:
            return {"trend": "insufficient_data", "change": 0}
        
        # Get first and last snapshots
        first_snapshot = snapshots_24h[0]
        last_snapshot = snapshots_24h[-1]
        
        # Calculate change in disapproved products
        change = last_snapshot.totals.disapproved - first_snapshot.totals.disapproved
        
        if change > 0:
            trend = "increasing"
        elif change < 0:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "change": change,
            "period": "24h"
        }
    
    def get_alert_history(self, limit: int = 10) -> list:
        """Get history of alerts sent."""
        try:
            alert_snapshots = db_service.get_alert_history(limit=limit)
            return [
                {
                    "timestamp": snapshot.timestamp.isoformat(),
                    "country": snapshot.country,
                    "reporting_context": snapshot.reporting_context,
                    "totals": snapshot.totals.dict(),
                    "delta_disapproved": snapshot.delta_disapproved,
                    "top_issues": [issue.dict() for issue in snapshot.top_issues]
                }
                for snapshot in alert_snapshots
            ]
        except Exception as e:
            logger.error(f"Error getting alert history: {e}")
            return []


# Global alert service instance
alert_service = AlertServiceDev()
