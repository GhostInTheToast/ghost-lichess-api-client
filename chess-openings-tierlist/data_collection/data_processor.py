#!/usr/bin/env python3
"""
Data processor for loading opening statistics into the database.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from database.models import Opening, OpeningStatistic, DataUpdateLog, get_session

# Load environment variables
load_dotenv('../config/.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpeningDataProcessor:
    """Process and load opening data into the database."""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///./chess_openings.db')
        self.engine = create_engine(self.database_url)
        
    def load_json_data(self, filename: str) -> List[Dict[str, Any]]:
        """Load opening data from JSON file."""
        logger.info(f"Loading data from {filename}")
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {len(data)} openings from file")
        return data
    
    def process_opening_data(self, raw_data: List[Dict[str, Any]]) -> tuple:
        """
        Process raw opening data into database models.
        
        Returns:
            Tuple of (openings_list, statistics_list)
        """
        logger.info("Processing opening data for database insertion")
        
        openings = []
        statistics = []
        
        for i, data in enumerate(raw_data, 1):
            # Create Opening record
            opening = Opening(
                eco_code=data.get('eco_code', ''),
                name=data.get('opening_name', f"Unknown Opening {i}"),
                moves_sequence=data.get('moves_sequence', []),
                popularity_rank=i,  # Based on order in the data
                is_active=True
            )
            openings.append(opening)
            
            # Create OpeningStatistic record
            statistic = OpeningStatistic(
                white_wins=data.get('white_wins', 0),
                black_wins=data.get('black_wins', 0),
                draws=data.get('draws', 0),
                total_games=data.get('total_games', 0),
                win_rate_white=data.get('win_rate_white', 0.0),
                win_rate_black=data.get('win_rate_black', 0.0),
                draw_rate=data.get('draw_rate', 0.0),
                performance_score=data.get('performance_score', 0.0),
                rating_range="all",  # Default range for now
                time_control="all",  # Default time control for now
                collected_at=datetime.fromisoformat(data.get('collected_at', datetime.utcnow().isoformat()))
            )
            statistics.append(statistic)
        
        logger.info(f"Processed {len(openings)} openings and {len(statistics)} statistics")
        return openings, statistics
    
    def save_to_database(self, openings: List[Opening], statistics: List[OpeningStatistic]) -> bool:
        """Save processed data to database."""
        session = get_session(self.engine)
        update_log = DataUpdateLog(
            operation_type="initial_load",
            status="in_progress",
            started_at=datetime.utcnow()
        )
        
        try:
            session.add(update_log)
            session.commit()
            
            # Clear existing data (for fresh load)
            logger.info("Clearing existing data")
            session.query(OpeningStatistic).delete()
            session.query(Opening).delete()
            session.commit()
            
            # Insert openings
            logger.info(f"Inserting {len(openings)} openings")
            session.add_all(openings)
            session.flush()  # Get IDs without committing
            
            # Link statistics to openings
            for i, statistic in enumerate(statistics):
                statistic.opening_id = openings[i].id
            
            # Insert statistics
            logger.info(f"Inserting {len(statistics)} statistics")
            session.add_all(statistics)
            
            # Update log
            update_log.status = "success"
            update_log.completed_at = datetime.utcnow()
            update_log.duration_seconds = (update_log.completed_at - update_log.started_at).total_seconds()
            update_log.openings_processed = len(openings)
            update_log.statistics_updated = len(statistics)
            
            session.commit()
            logger.info("Data saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            update_log.status = "error"
            update_log.error_message = str(e)
            update_log.completed_at = datetime.utcnow()
            session.commit()
            session.rollback()
            return False
            
        finally:
            session.close()
    
    def process_file(self, filename: str) -> bool:
        """Process a data file and load it into the database."""
        try:
            # Load raw data
            raw_data = self.load_json_data(filename)
            
            # Process data
            openings, statistics = self.process_opening_data(raw_data)
            
            # Save to database
            success = self.save_to_database(openings, statistics)
            
            if success:
                logger.info(f"Successfully processed file: {filename}")
            else:
                logger.error(f"Failed to process file: {filename}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            return False


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process opening data into database")
    parser.add_argument("filename", help="JSON file containing opening data")
    parser.add_argument("--database-url", help="Database URL override")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.filename):
        print(f"Error: File {args.filename} not found")
        return 1
    
    processor = OpeningDataProcessor(args.database_url)
    success = processor.process_file(args.filename)
    
    if success:
        print("Data processing completed successfully!")
        return 0
    else:
        print("Data processing failed!")
        return 1


if __name__ == "__main__":
    exit(main())