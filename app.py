"""Simple FastAPI application for Railway deployment."""

import os
import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Merchant Center Monitor",
    description="Monitor product statuses in Google Merchant Center",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Merchant Center Monitor is running!",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/status")
async def status():
    """Status endpoint."""
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
        "alert_sent": False
    }


@app.post("/tasks/run")
async def run_check():
    """Run manual check."""
    logger.info("Manual check triggered")
    return {
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
            }
        ]
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Simple dashboard."""
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
            <span class="method">GET</span> <code>/dashboard</code> - Web dashboard
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/docs</code> - API documentation
        </div>
        
        <h2>Quick Actions:</h2>
        <p>
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
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
