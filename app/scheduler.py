"""Scheduler service for running periodic checks."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import signal
import sys

from .alert_service import alert_service
from .config import settings

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for scheduling periodic product status checks."""
    
    def __init__(self, interval_minutes: int = 30):
        self.interval_minutes = interval_minutes
        self.interval_seconds = interval_minutes * 60
        self.running = False
        self.task: Optional[asyncio.Task] = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down scheduler...")
        self.stop()
        sys.exit(0)
    
    async def _run_check_cycle(self):
        """Run a single check cycle."""
        try:
            logger.info("Starting scheduled check cycle")
            result = alert_service.run_check()
            logger.info(f"Check cycle completed: {result}")
        except Exception as e:
            logger.error(f"Error in scheduled check cycle: {e}")
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        logger.info(f"Starting scheduler with {self.interval_minutes} minute intervals")
        
        while self.running:
            try:
                # Run the check
                await self._run_check_cycle()
                
                # Wait for the next interval
                logger.info(f"Waiting {self.interval_minutes} minutes until next check")
                await asyncio.sleep(self.interval_seconds)
                
            except asyncio.CancelledError:
                logger.info("Scheduler loop cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error in scheduler loop: {e}")
                # Wait a bit before retrying to avoid tight error loops
                await asyncio.sleep(60)
    
    def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if not self.running:
            logger.warning("Scheduler is not running")
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
        logger.info("Scheduler stopped")
    
    async def run_once(self):
        """Run a single check immediately."""
        logger.info("Running immediate check")
        await self._run_check_cycle()


# Global scheduler instance
scheduler = SchedulerService(interval_minutes=30)


async def start_scheduler():
    """Start the scheduler service."""
    scheduler.start()


async def stop_scheduler():
    """Stop the scheduler service."""
    scheduler.stop()


async def run_immediate_check():
    """Run an immediate check."""
    await scheduler.run_once()
