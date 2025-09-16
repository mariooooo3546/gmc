"""Firestore database operations for storing product status snapshots."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from google.cloud import firestore
from google.cloud.exceptions import GoogleCloudError

from .config import settings
from .models import ProductStatusSnapshot, ProductStatusCounts, IssueCode

logger = logging.getLogger(__name__)


class FirestoreService:
    """Service for Firestore database operations."""
    
    def __init__(self):
        try:
            self.db = firestore.Client(project=settings.google_project_id)
            logger.info("Successfully connected to Firestore")
        except Exception as e:
            logger.error(f"Failed to connect to Firestore: {e}")
            raise
    
    def save_snapshot(self, snapshot: ProductStatusSnapshot) -> str:
        """Save a product status snapshot to Firestore."""
        try:
            # Convert to dict for Firestore
            data = {
                "timestamp": snapshot.timestamp,
                "country": snapshot.country,
                "reporting_context": snapshot.reporting_context,
                "totals": snapshot.totals.dict(),
                "delta_disapproved": snapshot.delta_disapproved,
                "alert_sent": snapshot.alert_sent,
                "top_issues": [issue.dict() for issue in snapshot.top_issues]
            }
            
            # Add to checks collection
            doc_ref = self.db.collection("checks").add(data)[1]
            logger.info(f"Saved snapshot with ID: {doc_ref.id}")
            return doc_ref.id
            
        except GoogleCloudError as e:
            logger.error(f"Failed to save snapshot to Firestore: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving snapshot: {e}")
            raise
    
    def get_latest_snapshot(self) -> Optional[ProductStatusSnapshot]:
        """Get the most recent product status snapshot."""
        try:
            # Query for the latest snapshot
            query = self.db.collection("checks").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1)
            docs = query.stream()
            
            for doc in docs:
                data = doc.to_dict()
                return ProductStatusSnapshot(
                    timestamp=data["timestamp"],
                    country=data["country"],
                    reporting_context=data["reporting_context"],
                    totals=ProductStatusCounts(**data["totals"]),
                    delta_disapproved=data["delta_disapproved"],
                    alert_sent=data["alert_sent"],
                    top_issues=[IssueCode(**issue) for issue in data.get("top_issues", [])]
                )
            
            logger.info("No previous snapshots found")
            return None
            
        except GoogleCloudError as e:
            logger.error(f"Failed to get latest snapshot from Firestore: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting latest snapshot: {e}")
            raise
    
    def get_snapshots_last_24h(self) -> List[ProductStatusSnapshot]:
        """Get all snapshots from the last 24 hours."""
        try:
            # Calculate 24 hours ago
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Query for snapshots in the last 24 hours
            query = self.db.collection("checks").where("timestamp", ">=", cutoff_time).order_by("timestamp")
            docs = query.stream()
            
            snapshots = []
            for doc in docs:
                data = doc.to_dict()
                snapshot = ProductStatusSnapshot(
                    timestamp=data["timestamp"],
                    country=data["country"],
                    reporting_context=data["reporting_context"],
                    totals=ProductStatusCounts(**data["totals"]),
                    delta_disapproved=data["delta_disapproved"],
                    alert_sent=data["alert_sent"],
                    top_issues=[IssueCode(**issue) for issue in data.get("top_issues", [])]
                )
                snapshots.append(snapshot)
            
            logger.info(f"Retrieved {len(snapshots)} snapshots from last 24 hours")
            return snapshots
            
        except GoogleCloudError as e:
            logger.error(f"Failed to get 24h snapshots from Firestore: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting 24h snapshots: {e}")
            raise
    
    def get_alert_history(self, limit: int = 10) -> List[ProductStatusSnapshot]:
        """Get recent snapshots where alerts were sent."""
        try:
            # Query for snapshots where alert_sent is True
            query = self.db.collection("checks").where("alert_sent", "==", True).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
            docs = query.stream()
            
            snapshots = []
            for doc in docs:
                data = doc.to_dict()
                snapshot = ProductStatusSnapshot(
                    timestamp=data["timestamp"],
                    country=data["country"],
                    reporting_context=data["reporting_context"],
                    totals=ProductStatusCounts(**data["totals"]),
                    delta_disapproved=data["delta_disapproved"],
                    alert_sent=data["alert_sent"],
                    top_issues=[IssueCode(**issue) for issue in data.get("top_issues", [])]
                )
                snapshots.append(snapshot)
            
            logger.info(f"Retrieved {len(snapshots)} alert snapshots")
            return snapshots
            
        except GoogleCloudError as e:
            logger.error(f"Failed to get alert history from Firestore: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting alert history: {e}")
            raise
    
    def save_email_alert(self, to: str, subject: str, body: str) -> str:
        """Save email alert record to Firestore."""
        try:
            data = {
                "to": to,
                "subject": subject,
                "body": body,
                "sent_at": datetime.utcnow()
            }
            
            doc_ref = self.db.collection("email_alerts").add(data)[1]
            logger.info(f"Saved email alert with ID: {doc_ref.id}")
            return doc_ref.id
            
        except GoogleCloudError as e:
            logger.error(f"Failed to save email alert to Firestore: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving email alert: {e}")
            raise
    
    def get_settings(self) -> dict:
        """Get application settings from Firestore."""
        try:
            doc_ref = self.db.collection("settings").document("app_config")
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                # Return default settings
                default_settings = {
                    "alert_threshold_abs": settings.alert_threshold_abs,
                    "alert_threshold_delta": settings.alert_threshold_delta,
                    "alert_country": settings.alert_country,
                    "alert_reporting_context": settings.alert_reporting_context,
                    "mail_to": settings.mail_to
                }
                # Save default settings
                doc_ref.set(default_settings)
                return default_settings
                
        except GoogleCloudError as e:
            logger.error(f"Failed to get settings from Firestore: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting settings: {e}")
            raise
    
    def update_settings(self, new_settings: dict) -> None:
        """Update application settings in Firestore."""
        try:
            doc_ref = self.db.collection("settings").document("app_config")
            doc_ref.set(new_settings, merge=True)
            logger.info("Updated settings in Firestore")
            
        except GoogleCloudError as e:
            logger.error(f"Failed to update settings in Firestore: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating settings: {e}")
            raise


# Global database service instance
db_service = FirestoreService()
