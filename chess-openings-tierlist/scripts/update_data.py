#!/usr/bin/env python3
"""
Automated data update system for chess openings tier list.
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from data_collection.collect_openings import OpeningsDataCollector
from data_collection.data_processor import OpeningDataProcessor

# Load environment variables
load_dotenv('../config/.env')

logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/update_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutomatedUpdateSystem:
    """Automated system for updating chess opening data."""
    
    def __init__(self):
        self.update_interval_hours = int(os.getenv('UPDATE_INTERVAL_HOURS', '6'))
        self.collector = None
        self.processor = None
        
        logger.info(f"Initialized update system with {self.update_interval_hours}h interval")
    
    def initialize_components(self):
        """Initialize data collection and processing components."""
        try:
            self.collector = OpeningsDataCollector()
            self.processor = OpeningDataProcessor()
            logger.info("Components initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            return False
    
    def run_full_update(self):
        """Run a complete data update cycle."""
        logger.info("Starting full data update cycle")
        
        if not self.collector or not self.processor:
            if not self.initialize_components():
                logger.error("Cannot run update - components not initialized")
                return False
        
        try:
            # Collect fresh data from Lichess API
            logger.info("Collecting fresh opening data from Lichess API")
            openings_data = self.collector.discover_openings_tree(max_openings=50)
            
            if not openings_data:
                logger.warning("No data collected from API")
                return False
            
            # Save collected data to temporary file
            temp_filename = f"../database/temp_openings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            data_file = self.collector.save_openings_data(openings_data, temp_filename)
            
            # Process and load into database
            logger.info("Processing and loading data into database")
            success = self.processor.process_file(data_file)
            
            if success:
                logger.info("Full update completed successfully")
                # Clean up temporary file
                os.remove(data_file)
                return True
            else:
                logger.error("Failed to process data into database")
                return False
                
        except Exception as e:
            logger.error(f"Full update failed: {e}", exc_info=True)
            return False
    
    def run_incremental_update(self):
        """Run an incremental update (lighter than full update)."""
        logger.info("Starting incremental data update")
        
        # For now, incremental updates are the same as full updates
        # In the future, this could be optimized to only update recent data
        return self.run_full_update()
    
    def check_system_health(self):
        """Check if the system is healthy and ready for updates."""
        try:
            # Check if API key is available
            api_token = os.getenv('LICHESS_API_TOKEN')
            if not api_token:
                logger.error("LICHESS_API_TOKEN not configured")
                return False
            
            # Check if database is accessible
            database_url = os.getenv('DATABASE_URL', 'sqlite:///./chess_openings.db')
            if database_url.startswith('sqlite') and not os.path.exists(database_url.replace('sqlite:///', '')):
                logger.error("Database file not found")
                return False
            
            logger.info("System health check passed")
            return True
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return False
    
    def scheduled_update(self):
        """Scheduled update function."""
        logger.info("Scheduled update triggered")
        
        if not self.check_system_health():
            logger.error("System health check failed - skipping update")
            return
        
        # Run incremental update
        success = self.run_incremental_update()
        
        if success:
            logger.info("Scheduled update completed successfully")
        else:
            logger.error("Scheduled update failed")
    
    def start_scheduler(self):
        """Start the automated scheduling system."""
        logger.info(f"Starting scheduler with {self.update_interval_hours}h interval")
        
        # Schedule regular updates
        schedule.every(self.update_interval_hours).hours.do(self.scheduled_update)
        
        # Run initial update
        logger.info("Running initial data update")
        self.scheduled_update()
        
        # Keep the scheduler running
        logger.info("Scheduler started - waiting for scheduled updates")
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated chess openings data update system")
    parser.add_argument('--mode', choices=['once', 'schedule'], default='once',
                       help="Run mode: 'once' for single update, 'schedule' for continuous")
    parser.add_argument('--type', choices=['full', 'incremental'], default='incremental',
                       help="Update type: 'full' or 'incremental'")
    
    args = parser.parse_args()
    
    update_system = AutomatedUpdateSystem()
    
    if args.mode == 'once':
        logger.info(f"Running single {args.type} update")
        
        if args.type == 'full':
            success = update_system.run_full_update()
        else:
            success = update_system.run_incremental_update()
        
        if success:
            print("Update completed successfully!")
            return 0
        else:
            print("Update failed!")
            return 1
    
    elif args.mode == 'schedule':
        logger.info("Starting scheduled update system")
        try:
            update_system.start_scheduler()
            return 0
        except Exception as e:
            logger.error(f"Scheduler failed: {e}")
            return 1


if __name__ == "__main__":
    exit(main())