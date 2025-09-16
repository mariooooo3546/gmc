"""Data models for the Merchant Center monitoring application."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel


class ProductStatusCounts(BaseModel):
    """Product status counts from Merchant API."""
    approved: int = 0
    pending: int = 0
    disapproved: int = 0
    limited: int = 0
    suspended: int = 0
    under_review: int = 0
    processing: int = 0


class IssueCode(BaseModel):
    """Issue code with description and count."""
    code: str
    description: str
    count: int


class ProductStatusSnapshot(BaseModel):
    """Snapshot of product statuses at a point in time."""
    timestamp: datetime
    country: str
    reporting_context: str
    totals: ProductStatusCounts
    delta_disapproved: int
    alert_sent: bool
    top_issues: List[IssueCode] = []


class AlertThresholds(BaseModel):
    """Alert threshold configuration."""
    absolute_threshold: int
    delta_threshold: int
    country: str
    reporting_context: str


class EmailAlert(BaseModel):
    """Email alert data."""
    to: str
    subject: str
    body: str
    sent_at: datetime


class HealthStatus(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str = "1.0.0"


class CheckResult(BaseModel):
    """Result of a product status check."""
    checked_at: datetime
    country: str
    reporting_context: str
    totals: ProductStatusCounts
    delta: Dict[str, int]
    alert_sent: bool
    top_issues: List[IssueCode] = []
