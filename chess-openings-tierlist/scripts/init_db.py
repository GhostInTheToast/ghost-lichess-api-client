#!/usr/bin/env python3
"""
Database initialization script for chess openings tier list.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from database.models import create_database, get_session, Base

# Load environment variables
load_dotenv('config/.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize the database."""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./chess_openings.db')
    
    logger.info(f"Initializing database: {database_url}")
    
    try:
        # Create database and tables
        engine = create_database(database_url)
        logger.info("Database tables created successfully")
        
        # Test connection
        session = get_session(engine)
        session.close()
        logger.info("Database connection test successful")
        
        print("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())