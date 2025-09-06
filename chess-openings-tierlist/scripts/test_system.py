#!/usr/bin/env python3
"""
System testing script for chess openings tier list.
"""

import os
import sys
import json
import time
import logging
import requests
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from database.models import get_session, Opening, OpeningStatistic

# Load environment variables
load_dotenv('config/.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemTester:
    """Test the complete chess openings tier list system."""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///./chess_openings.db')
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.engine = create_engine(self.database_url)
        
    def test_database_connection(self):
        """Test database connectivity and basic queries."""
        logger.info("Testing database connection...")
        
        try:
            session = get_session(self.engine)
            
            # Test basic query
            opening_count = session.query(Opening).count()
            statistics_count = session.query(OpeningStatistic).count()
            
            session.close()
            
            logger.info(f"✅ Database connection successful")
            logger.info(f"   Openings: {opening_count}")
            logger.info(f"   Statistics: {statistics_count}")
            
            return True, opening_count, statistics_count
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False, 0, 0
    
    def test_api_endpoints(self):
        """Test API endpoints."""
        logger.info("Testing API endpoints...")
        
        endpoints = [
            ('GET', '/'),
            ('GET', '/openings'),
            ('GET', '/tier-list'),
            ('GET', '/statistics/summary'),
        ]
        
        results = {}
        
        for method, endpoint in endpoints:
            try:
                url = f"{self.api_base_url}{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"✅ {method} {endpoint} - OK")
                    results[endpoint] = True
                else:
                    logger.warning(f"⚠️ {method} {endpoint} - Status {response.status_code}")
                    results[endpoint] = False
                    
            except requests.exceptions.ConnectionError:
                logger.error(f"❌ {method} {endpoint} - Connection failed (is API server running?)")
                results[endpoint] = False
            except Exception as e:
                logger.error(f"❌ {method} {endpoint} - Error: {e}")
                results[endpoint] = False
        
        return results
    
    def test_data_quality(self):
        """Test data quality and consistency."""
        logger.info("Testing data quality...")
        
        try:
            session = get_session(self.engine)
            
            # Check for openings without statistics
            openings_without_stats = session.query(Opening).outerjoin(OpeningStatistic).filter(
                OpeningStatistic.id.is_(None)
            ).count()
            
            # Check for statistics without openings
            stats_without_openings = session.query(OpeningStatistic).outerjoin(Opening).filter(
                Opening.id.is_(None)
            ).count()
            
            # Check for invalid performance scores
            invalid_scores = session.query(OpeningStatistic).filter(
                (OpeningStatistic.performance_score < 0) | 
                (OpeningStatistic.performance_score > 100)
            ).count()
            
            # Check for empty opening names
            empty_names = session.query(Opening).filter(
                (Opening.name.is_(None)) | (Opening.name == '')
            ).count()
            
            session.close()
            
            issues = []
            
            if openings_without_stats > 0:
                issues.append(f"{openings_without_stats} openings without statistics")
            
            if stats_without_openings > 0:
                issues.append(f"{stats_without_openings} statistics without openings")
            
            if invalid_scores > 0:
                issues.append(f"{invalid_scores} statistics with invalid performance scores")
            
            if empty_names > 0:
                issues.append(f"{empty_names} openings with empty names")
            
            if issues:
                logger.warning("⚠️ Data quality issues found:")
                for issue in issues:
                    logger.warning(f"   - {issue}")
                return False, issues
            else:
                logger.info("✅ Data quality check passed")
                return True, []
                
        except Exception as e:
            logger.error(f"❌ Data quality test failed: {e}")
            return False, [str(e)]
    
    def test_lichess_api_integration(self):
        """Test Lichess API integration."""
        logger.info("Testing Lichess API integration...")
        
        api_token = os.getenv('LICHESS_API_TOKEN')
        
        if not api_token:
            logger.error("❌ LICHESS_API_TOKEN not configured")
            return False
        
        try:
            # Test a simple API call to Lichess
            import berserk
            session = berserk.TokenSession(api_token)
            client = berserk.Client(session=session)
            
            # Try to get opening statistics for starting position
            stats = client.opening_explorer.get_lichess_games(moves=1)
            
            if 'moves' in stats and len(stats['moves']) > 0:
                logger.info("✅ Lichess API integration working")
                logger.info(f"   Found {len(stats['moves'])} opening moves")
                return True
            else:
                logger.warning("⚠️ Lichess API returned empty results")
                return False
                
        except Exception as e:
            logger.error(f"❌ Lichess API integration failed: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests and provide a comprehensive report."""
        logger.info("🧪 Starting comprehensive system test")
        logger.info("=" * 50)
        
        results = {}
        
        # Test database
        db_success, opening_count, stats_count = self.test_database_connection()
        results['database'] = db_success
        
        # Test API endpoints
        api_results = self.test_api_endpoints()
        results['api'] = all(api_results.values())
        
        # Test data quality
        quality_success, quality_issues = self.test_data_quality()
        results['data_quality'] = quality_success
        
        # Test Lichess API
        lichess_success = self.test_lichess_api_integration()
        results['lichess_api'] = lichess_success
        
        # Generate report
        logger.info("=" * 50)
        logger.info("📊 TEST REPORT")
        logger.info("=" * 50)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name.replace('_', ' ').title():<20} {status}")
        
        logger.info("-" * 50)
        logger.info(f"Tests passed: {passed}/{total}")
        
        if opening_count > 0:
            logger.info(f"Database contains: {opening_count} openings, {stats_count} statistics")
        
        if quality_issues:
            logger.info(f"Data quality issues: {len(quality_issues)}")
        
        if passed == total:
            logger.info("🎉 All tests passed! System is ready.")
            return True
        else:
            logger.info("❌ Some tests failed. Please check the logs above.")
            return False


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test chess openings tier list system")
    parser.add_argument('--test', choices=['all', 'database', 'api', 'data', 'lichess'],
                       default='all', help="Specific test to run")
    
    args = parser.parse_args()
    
    tester = SystemTester()
    
    try:
        if args.test == 'all':
            success = tester.run_comprehensive_test()
        elif args.test == 'database':
            success, _, _ = tester.test_database_connection()
        elif args.test == 'api':
            results = tester.test_api_endpoints()
            success = all(results.values())
        elif args.test == 'data':
            success, _ = tester.test_data_quality()
        elif args.test == 'lichess':
            success = tester.test_lichess_api_integration()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())