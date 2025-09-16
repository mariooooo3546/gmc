"""Google Service Account authentication for Merchant API."""

import json
import logging
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.auth.exceptions import GoogleAuthError

from .config import settings

logger = logging.getLogger(__name__)


class GoogleAuthService:
    """Service for handling Google authentication."""
    
    def __init__(self):
        self._credentials: Optional[service_account.Credentials] = None
        self._token: Optional[str] = None
    
    def _get_credentials(self) -> service_account.Credentials:
        """Get or create service account credentials."""
        if self._credentials is None or not self._credentials.valid:
            try:
                if self._credentials and self._credentials.expired and self._credentials.refresh_token:
                    # Refresh existing credentials
                    self._credentials.refresh(Request())
                else:
                    # Create new credentials
                    if settings.google_service_account_key:
                        # Load from file path
                        self._credentials = service_account.Credentials.from_service_account_file(
                            settings.google_service_account_key,
                            scopes=['https://www.googleapis.com/auth/content']
                        )
                    else:
                        # Use default credentials (for Cloud Run with Workload Identity)
                        self._credentials = service_account.Credentials.from_service_account_info(
                            self._get_service_account_info(),
                            scopes=['https://www.googleapis.com/auth/content']
                        )
                
                logger.info("Successfully authenticated with Google Service Account")
                
            except GoogleAuthError as e:
                logger.error(f"Failed to authenticate with Google: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during authentication: {e}")
                raise
        
        return self._credentials
    
    def _get_service_account_info(self) -> dict:
        """Get service account info from environment or metadata server."""
        # In Cloud Run, we can get this from metadata server
        # For local development, this would need to be set in environment
        import os
        
        # Try to get from environment variable (for local dev)
        sa_info_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_INFO')
        if sa_info_json:
            return json.loads(sa_info_json)
        
        # For Cloud Run with Workload Identity, we don't need explicit SA info
        # The default credentials will work
        return {
            "type": "service_account",
            "project_id": settings.google_project_id,
            "client_email": settings.google_service_account_email,
        }
    
    def get_access_token(self) -> str:
        """Get a valid access token for API calls."""
        if self._token is None:
            credentials = self._get_credentials()
            # Refresh token if needed
            if not credentials.valid:
                credentials.refresh(Request())
            
            self._token = credentials.token
        
        return self._token
    
    def refresh_token(self) -> str:
        """Force refresh the access token."""
        credentials = self._get_credentials()
        credentials.refresh(Request())
        self._token = credentials.token
        return self._token


# Global auth service instance
auth_service = GoogleAuthService()
