"""Alert service for monitoring product statuses and triggering alerts."""

import logging
from datetime import datetime
from typing import Tuple

from .config import settings
from .models import ProductStatusCounts, ProductStatusSnapshot, IssueCode
from .merchant_api import merchant_api
from .database import db_service
from .email_service import email_service

logger = logging.getLogger(__name__)


class AlertService:
    """Service for monitoring product statuses and managing alerts."""
    
    def run_check(self) -> dict:
        """Run a complete product status check and send alerts if needed."""
        logger.info("Starting product status check")
        
        try:
            # Get current product statuses from Merchant API
            api_response = merchant_api.get_aggregate_product_statuses(
                country=settings.alert_country,
                reporting_context=settings.alert_reporting_context
            )
            
            # Parse the response
            current_totals = merchant_api.parse_product_status_counts(api_response)
            top_issues = merchant_api.get_top_issue_codes(api_response, limit=5)
            
            # Get previous snapshot for delta calculation
            previous_snapshot = db_service.get_latest_snapshot()
            
            # Calculate delta
            delta_disapproved = 0
            if previous_snapshot:
                delta_disapproved = current_totals.disapproved - previous_snapshot.totals.disapproved
            
            # Check if alert should be sent
            alert_sent = self._should_send_alert(current_totals, delta_disapproved)
            
            # Send alert if needed
            if alert_sent:
                logger.warning("Alert thresholds exceeded, sending email")
                email_success = email_service.send_alert_email(
                    totals=current_totals,
                    delta_disapproved=delta_disapproved,
                    top_issues=top_issues,
                    country=settings.alert_country,
                    reporting_context=settings.alert_reporting_context
                )
                
                if not email_success:
                    logger.error("Failed to send alert email")
                    alert_sent = False  # Don't mark as sent if email failed
            
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
            logger.info(f"Saved snapshot with ID: {snapshot_id}")
            
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
            
            logger.info(f"Check completed successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during product status check: {e}")
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
alert_service = AlertService()
