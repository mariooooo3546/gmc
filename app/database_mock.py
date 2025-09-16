"""Mock database service for development without Google Cloud."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from .models import ProductStatusSnapshot, ProductStatusCounts, IssueCode

logger = logging.getLogger(__name__)


class MockDatabaseService:
    """Mock database service for development."""
    
    def __init__(self):
        self.snapshots = []
        self.email_alerts = []
        self.settings = {
            "alert_threshold_abs": 25,
            "alert_threshold_delta": 10,
            "alert_country": "PL",
            "alert_reporting_context": "SHOPPING_ADS",
            "mail_to": "admin@example.com"
        }
        logger.info("Using mock database service for development")
    
    def save_snapshot(self, snapshot: ProductStatusSnapshot) -> str:
        """Save a product status snapshot."""
        snapshot_id = f"mock_snapshot_{len(self.snapshots) + 1}"
        self.snapshots.append(snapshot)
        logger.info(f"Saved mock snapshot with ID: {snapshot_id}")
        return snapshot_id
    
    def get_latest_snapshot(self) -> Optional[ProductStatusSnapshot]:
        """Get the most recent product status snapshot."""
        if not self.snapshots:
            logger.info("No mock snapshots found")
            return None
        
        latest = self.snapshots[-1]
        logger.info(f"Retrieved latest mock snapshot: {latest.timestamp}")
        return latest
    
    def get_snapshots_last_24h(self) -> List[ProductStatusSnapshot]:
        """Get all snapshots from the last 24 hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        recent_snapshots = [s for s in self.snapshots if s.timestamp >= cutoff_time]
        logger.info(f"Retrieved {len(recent_snapshots)} mock snapshots from last 24 hours")
        return recent_snapshots
    
    def get_alert_history(self, limit: int = 10) -> List[ProductStatusSnapshot]:
        """Get recent snapshots where alerts were sent."""
        alert_snapshots = [s for s in self.snapshots if s.alert_sent][-limit:]
        logger.info(f"Retrieved {len(alert_snapshots)} mock alert snapshots")
        return alert_snapshots
    
    def save_email_alert(self, to: str, subject: str, body: str) -> str:
        """Save email alert record."""
        alert_id = f"mock_alert_{len(self.email_alerts) + 1}"
        self.email_alerts.append({
            "to": to,
            "subject": subject,
            "body": body,
            "sent_at": datetime.utcnow()
        })
        logger.info(f"Saved mock email alert with ID: {alert_id}")
        return alert_id
    
    def get_settings(self) -> dict:
        """Get application settings."""
        logger.info("Retrieved mock settings")
        return self.settings.copy()
    
    def update_settings(self, new_settings: dict) -> None:
        """Update application settings."""
        self.settings.update(new_settings)
        logger.info("Updated mock settings")


# Global mock database service instance
db_service = MockDatabaseService()
