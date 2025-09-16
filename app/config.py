"""Configuration settings for the Merchant Center monitoring application."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google Cloud Configuration
    google_project_id: str
    google_service_account_email: str
    google_service_account_key: Optional[str] = None
    merchant_account_id: str
    
    # Alert Configuration
    alert_threshold_abs: int = 25
    alert_threshold_delta: int = 10
    alert_country: str = "PL"
    alert_reporting_context: str = "SHOPPING_ADS"
    
    # Email Configuration
    mail_from: str
    mail_to: str
    sendgrid_api_key: str
    
    # Application Configuration
    environment: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

