#!/usr/bin/env python3
"""
Chess Openings Data Collection Script

This script collects opening statistics from the Lichess API using the berserk client.
It discovers popular openings and their performance metrics across different rating ranges
and time controls.
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

# Add parent directory to path to import berserk
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import berserk
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/.env')

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OpeningsDataCollector:
    """Collects chess opening statistics from Lichess API."""
    
    def __init__(self):
        self.api_token = os.getenv('LICHESS_API_TOKEN')
        if not self.api_token:
            raise ValueError("LICHESS_API_TOKEN not found in environment variables")
        
        # Initialize berserk client
        session = berserk.TokenSession(self.api_token)
        self.client = berserk.Client(session=session)
        
        # Configuration
        self.rating_ranges = ['1600', '1800', '2000', '2200']  # Simplified for initial testing
        self.time_controls = ['blitz', 'rapid', 'classical']   # Simplified for initial testing
        self.max_requests_per_minute = int(os.getenv('MAX_REQUESTS_PER_MINUTE', '60'))
        self.request_delay = 60 / self.max_requests_per_minute  # seconds between requests
        
        logger.info(f"Initialized collector with {len(self.rating_ranges)} rating ranges and {len(self.time_controls)} time controls")

    def get_popular_openings(self, max_moves: int = 10) -> List[Dict[str, Any]]:
        """
        Get popular opening moves from the starting position.
        
        Args:
            max_moves: Maximum number of opening moves to collect
            
        Returns:
            List of opening data dictionaries
        """
        logger.info("Collecting popular opening moves from starting position")
        openings_data = []
        
        try:
            # Get statistics from starting position
            stats = self.client.opening_explorer.get_lichess_games(
                ratings=self.rating_ranges,
                speeds=self.time_controls,
                moves=max_moves,
                recent_games=4,
                top_games=4
            )
            
            if 'moves' in stats:
                for move in stats['moves']:
                    opening_data = {
                        'move': move['san'],
                        'uci': move['uci'],
                        'white_wins': move['white'],
                        'black_wins': move['black'],
                        'draws': move['draws'],
                        'total_games': move['white'] + move['black'] + move['draws'],
                        'average_rating': move.get('averageRating', 0),
                        'win_rate_white': move['white'] / (move['white'] + move['black'] + move['draws']) if move['white'] + move['black'] + move['draws'] > 0 else 0,
                        'collected_at': datetime.utcnow().isoformat()
                    }
                    openings_data.append(opening_data)
                    
            logger.info(f"Collected {len(openings_data)} opening moves")
            time.sleep(self.request_delay)  # Rate limiting
            
        except Exception as e:
            logger.error(f"Error collecting opening moves: {e}")
            
        return openings_data

    def get_opening_continuations(self, moves: List[str], depth: int = 3) -> Dict[str, Any]:
        """
        Get statistics for opening continuations after the given moves.
        
        Args:
            moves: List of moves in algebraic notation
            depth: How many moves deep to analyze
            
        Returns:
            Statistics for the opening continuation
        """
        logger.info(f"Analyzing opening continuation: {' '.join(moves)}")
        
        try:
            stats = self.client.opening_explorer.get_lichess_games(
                play=moves,
                ratings=self.rating_ranges,
                speeds=self.time_controls,
                moves=5,
                recent_games=4,
                top_games=4
            )
            
            time.sleep(self.request_delay)  # Rate limiting
            
            # Extract opening information if available
            opening_info = {}
            if 'opening' in stats and stats['opening']:
                opening_info = {
                    'eco': stats['opening'].get('eco', ''),
                    'name': stats['opening'].get('name', ''),
                }
            
            return {
                'moves': moves,
                'opening': opening_info,
                'white_wins': stats.get('white', 0),
                'black_wins': stats.get('black', 0),
                'draws': stats.get('draws', 0),
                'total_games': stats.get('white', 0) + stats.get('black', 0) + stats.get('draws', 0),
                'continuations': stats.get('moves', []),
                'recent_games': stats.get('recentGames', []),
                'top_games': stats.get('topGames', []),
                'collected_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing opening continuation {moves}: {e}")
            return {}

    def discover_openings_tree(self, max_openings: int = 50) -> List[Dict[str, Any]]:
        """
        Discover popular openings by exploring the game tree.
        
        Args:
            max_openings: Maximum number of openings to discover
            
        Returns:
            List of opening data with comprehensive statistics
        """
        logger.info(f"Starting discovery of top {max_openings} openings")
        discovered_openings = []
        
        # Start with popular first moves
        first_moves = self.get_popular_openings(max_moves=8)
        
        # Explore continuations for each first move
        for first_move in first_moves[:8]:  # Top 8 first moves
            logger.info(f"Exploring continuations for {first_move['move']}")
            
            # Get second moves
            second_move_stats = self.get_opening_continuations([first_move['move']], depth=2)
            if not second_move_stats:
                continue
                
            for continuation in second_move_stats.get('continuations', [])[:5]:  # Top 5 continuations
                moves_sequence = [first_move['move'], continuation['san']]
                
                # Get full opening statistics
                opening_stats = self.get_opening_continuations(moves_sequence, depth=3)
                if not opening_stats:
                    continue
                
                # Calculate performance metrics
                total_games = opening_stats['total_games']
                if total_games < 100:  # Skip openings with too few games
                    continue
                
                win_rate_white = opening_stats['white_wins'] / total_games if total_games > 0 else 0
                win_rate_black = opening_stats['black_wins'] / total_games if total_games > 0 else 0
                draw_rate = opening_stats['draws'] / total_games if total_games > 0 else 0
                
                # Calculate a composite score (you can adjust this formula)
                performance_score = (win_rate_white * 0.4 + (1 - win_rate_black) * 0.4 + draw_rate * 0.2) * 100
                
                opening_data = {
                    'moves_sequence': moves_sequence,
                    'eco_code': opening_stats.get('opening', {}).get('eco', ''),
                    'opening_name': opening_stats.get('opening', {}).get('name', ''),
                    'white_wins': opening_stats['white_wins'],
                    'black_wins': opening_stats['black_wins'],
                    'draws': opening_stats['draws'],
                    'total_games': total_games,
                    'win_rate_white': win_rate_white,
                    'win_rate_black': win_rate_black,
                    'draw_rate': draw_rate,
                    'performance_score': performance_score,
                    'collected_at': datetime.utcnow().isoformat()
                }
                
                discovered_openings.append(opening_data)
                logger.info(f"Added opening: {opening_data.get('opening_name', 'Unknown')} "
                          f"(Score: {performance_score:.1f}, Games: {total_games})")
                
                if len(discovered_openings) >= max_openings:
                    break
            
            if len(discovered_openings) >= max_openings:
                break
        
        # Sort by performance score and total games
        discovered_openings.sort(key=lambda x: (x['performance_score'], x['total_games']), reverse=True)
        
        logger.info(f"Discovery complete. Found {len(discovered_openings)} openings.")
        return discovered_openings[:max_openings]

    def save_openings_data(self, openings_data: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """
        Save openings data to JSON file.
        
        Args:
            openings_data: List of opening statistics
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"database/openings_data_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(openings_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(openings_data)} openings to {filename}")
        return filename

def main():
    """Main execution function."""
    logger.info("Starting chess openings data collection")
    
    try:
        collector = OpeningsDataCollector()
        
        # Discover and collect opening statistics
        openings_data = collector.discover_openings_tree(max_openings=50)
        
        if openings_data:
            # Save to file
            filename = collector.save_openings_data(openings_data)
            logger.info(f"Data collection completed successfully. Saved to {filename}")
            
            # Print summary
            print(f"\nCollection Summary:")
            print(f"Total openings collected: {len(openings_data)}")
            print(f"Average games per opening: {sum(o['total_games'] for o in openings_data) / len(openings_data):.0f}")
            print(f"Top 5 openings by performance score:")
            for i, opening in enumerate(openings_data[:5], 1):
                name = opening.get('opening_name', 'Unknown')
                score = opening['performance_score']
                games = opening['total_games']
                print(f"  {i}. {name} (Score: {score:.1f}, Games: {games})")
        else:
            logger.warning("No openings data collected")
            
    except Exception as e:
        logger.error(f"Data collection failed: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())