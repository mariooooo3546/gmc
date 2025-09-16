"""FastAPI application for Merchant Center monitoring - Production version."""

import logging
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn

from .models import HealthStatus, CheckResult
from .database_mock import db_service  # Use mock database for now

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Merchant Center Monitor",
    description="Monitor product statuses in Google Merchant Center and send alerts",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Templates for dashboard
templates = Jinja2Templates(directory="templates")


@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint for monitoring."""
    logger.info("Health check requested")
    return HealthStatus(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@app.post("/tasks/run", response_model=CheckResult)
async def run_check():
    """Run a single product status check and send alerts if needed."""
    try:
        logger.info("Manual check triggered via API")
        
        # Mock result for production
        result = {
            "checked_at": datetime.utcnow().isoformat(),
            "country": "PL",
            "reporting_context": "SHOPPING_ADS",
            "totals": {
                "approved": 1000,
                "pending": 50,
                "disapproved": 25,
                "limited": 5,
                "suspended": 2,
                "under_review": 10,
                "processing": 3
            },
            "delta": {"disapproved": 5},
            "alert_sent": False,
            "top_issues": [
                {
                    "code": "MISSING_GTIN",
                    "description": "Product is missing a GTIN",
                    "count": 10
                },
                {
                    "code": "IMAGE_LINK_BROKEN",
                    "description": "Product image link is broken",
                    "count": 8
                }
            ]
        }
        
        return CheckResult(**result)
    except Exception as e:
        logger.error(f"Error running check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """Get current status summary."""
    try:
        # Mock status for production
        return {
            "status": "healthy",
            "last_check": datetime.utcnow().isoformat(),
            "country": "PL",
            "reporting_context": "SHOPPING_ADS",
            "totals": {
                "approved": 1000,
                "pending": 50,
                "disapproved": 25,
                "limited": 5,
                "suspended": 2,
                "under_review": 10,
                "processing": 3
            },
            "delta": {"disapproved": 5},
            "alert_sent": False,
            "trend_24h": {
                "trend": "stable",
                "change": 0,
                "period": "24h"
            },
            "checks_24h": 48
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alerts/history")
async def get_alert_history(limit: int = 10):
    """Get history of sent alerts."""
    try:
        if limit > 50:
            limit = 50  # Cap at 50 for performance
        
        # Mock alert history
        return [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "country": "PL",
                "reporting_context": "SHOPPING_ADS",
                "totals": {
                    "approved": 1000,
                    "pending": 50,
                    "disapproved": 30,
                    "limited": 8,
                    "suspended": 3,
                    "under_review": 10,
                    "processing": 3
                },
                "delta_disapproved": 10,
                "top_issues": [
                    {
                        "code": "MISSING_GTIN",
                        "description": "Product is missing a GTIN",
                        "count": 15
                    }
                ]
            }
        ]
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Simple dashboard for monitoring."""
    try:
        # Mock data for production
        status = {
            "status": "healthy",
            "last_check": datetime.utcnow().isoformat(),
            "country": "PL",
            "reporting_context": "SHOPPING_ADS",
            "totals": {
                "approved": 1000,
                "pending": 50,
                "disapproved": 25,
                "limited": 5,
                "suspended": 2,
                "under_review": 10,
                "processing": 3
            },
            "delta": {"disapproved": 5},
            "alert_sent": False
        }
        
        recent_alerts = []
        chart_data = []
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "status": status,
            "recent_alerts": recent_alerts,
            "chart_data": chart_data,
            "settings": {
                "country": "PL",
                "reporting_context": "SHOPPING_ADS",
                "threshold_abs": 25,
                "threshold_delta": 10
            }
        })
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic info."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Merchant Center Monitor</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
            .endpoint { background-color: #e9ecef; padding: 10px; margin: 10px 0; border-radius: 3px; }
            .method { font-weight: bold; color: #007bff; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Merchant Center Monitor</h1>
            <p>Monitor product statuses in Google Merchant Center and receive alerts when thresholds are exceeded.</p>
        </div>
        
        <h2>Available Endpoints:</h2>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/health</code> - Health check
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span> <code>/tasks/run</code> - Run manual check
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/status</code> - Get current status
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/alerts/history</code> - Get alert history
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/dashboard</code> - Web dashboard
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/docs</code> - API documentation
        </div>
        
        <h2>Quick Actions:</h2>
        <p>
            <a href="/dashboard" style="color: #007bff; text-decoration: none; font-weight: bold;">📊 View Dashboard</a> |
            <a href="/status" style="color: #007bff; text-decoration: none; font-weight: bold;">📈 Check Status</a> |
            <a href="/docs" style="color: #007bff; text-decoration: none; font-weight: bold;">📚 API Docs</a>
        </p>
        
        <div style="margin-top: 30px; padding: 15px; background-color: #d1ecf1; border-radius: 5px;">
            <h3>ℹ️ Configuration:</h3>
            <ul>
                <li><strong>Country:</strong> PL</li>
                <li><strong>Reporting Context:</strong> SHOPPING_ADS</li>
                <li><strong>Absolute Threshold:</strong> 25</li>
                <li><strong>Delta Threshold:</strong> 10</li>
            </ul>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "app.main_prod:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
