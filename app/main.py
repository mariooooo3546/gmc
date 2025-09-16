"""FastAPI application for Merchant Center monitoring."""

import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from .config import settings
from .models import HealthStatus, CheckResult
from .alert_service import alert_service
from .database import db_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Merchant Center Monitor",
    description="Monitor product statuses in Google Merchant Center and send alerts",
    version="1.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None
)

# Templates for dashboard
templates = Jinja2Templates(directory="templates")


@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint for monitoring."""
    return HealthStatus(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@app.post("/tasks/run", response_model=CheckResult)
async def run_check():
    """Run a single product status check and send alerts if needed."""
    try:
        logger.info("Manual check triggered via API")
        result = alert_service.run_check()
        return CheckResult(**result)
    except Exception as e:
        logger.error(f"Error running check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """Get current status summary."""
    try:
        return alert_service.get_status_summary()
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alerts/history")
async def get_alert_history(limit: int = 10):
    """Get history of sent alerts."""
    try:
        if limit > 50:
            limit = 50  # Cap at 50 for performance
        return alert_service.get_alert_history(limit=limit)
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Simple dashboard for monitoring."""
    try:
        # Get current status
        status = alert_service.get_status_summary()
        
        # Get recent alerts
        recent_alerts = alert_service.get_alert_history(limit=5)
        
        # Get 24h snapshots for chart
        snapshots_24h = db_service.get_snapshots_last_24h()
        
        # Prepare chart data
        chart_data = []
        for snapshot in snapshots_24h:
            chart_data.append({
                "timestamp": snapshot.timestamp.isoformat(),
                "disapproved": snapshot.totals.disapproved,
                "limited": snapshot.totals.limited,
                "suspended": snapshot.totals.suspended
            })
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "status": status,
            "recent_alerts": recent_alerts,
            "chart_data": chart_data,
            "settings": {
                "country": settings.alert_country,
                "reporting_context": settings.alert_reporting_context,
                "threshold_abs": settings.alert_threshold_abs,
                "threshold_delta": settings.alert_threshold_delta
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
            <span class="method">GET</span> <code>/docs</code> - API documentation (dev only)
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
                <li><strong>Country:</strong> {settings.alert_country}</li>
                <li><strong>Reporting Context:</strong> {settings.alert_reporting_context}</li>
                <li><strong>Absolute Threshold:</strong> {settings.alert_threshold_abs}</li>
                <li><strong>Delta Threshold:</strong> {settings.alert_threshold_delta}</li>
            </ul>
        </div>
    </body>
    </html>
    """.format(settings=settings)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.environment == "development"
    )
