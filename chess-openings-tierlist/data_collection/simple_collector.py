#!/usr/bin/env python3
"""
Simplified chess openings data collector that actually works with Lichess API.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import berserk
from dotenv import load_dotenv

load_dotenv('config/.env')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SimpleOpeningsCollector:
    """Simple, reliable chess opening data collector."""
    
    def __init__(self):
        self.api_token = os.getenv('LICHESS_API_TOKEN')
        session = berserk.TokenSession(self.api_token)
        self.client = berserk.Client(session=session)
        
    def get_top_first_moves(self):
        """Get the most popular first moves."""
        logger.info("Collecting top first moves...")
        
        stats = self.client.opening_explorer.get_lichess_games(
            ratings=['1600'],  # Focus on intermediate players
            speeds=['blitz'],  # Focus on blitz games
            moves=5
        )
        
        moves_data = []
        for move in stats.get('moves', [])[:8]:  # Top 8 first moves
            total_games = move['white'] + move['black'] + move['draws']
            if total_games < 1000:  # Skip rare moves
                continue
                
            win_rate_white = move['white'] / total_games
            moves_data.append({
                'move': move['san'],
                'uci': move['uci'],
                'total_games': total_games,
                'white_wins': move['white'],
                'black_wins': move['black'],
                'draws': move['draws'],
                'win_rate_white': win_rate_white,
                'win_rate_black': move['black'] / total_games,
                'draw_rate': move['draws'] / total_games,
                'average_rating': move.get('averageRating', 1600),
                'collected_at': datetime.now().isoformat()
            })
            
        logger.info(f"Collected {len(moves_data)} first moves")
        return moves_data
    
    def explore_opening_line(self, moves_list, max_depth=3):
        """Explore an opening line to get full statistics."""
        logger.info(f"Exploring opening: {' '.join(moves_list)}")
        
        try:
            time.sleep(1)  # Rate limiting
            
            stats = self.client.opening_explorer.get_lichess_games(
                play=moves_list,
                ratings=['1600'],
                speeds=['blitz'],
                moves=3,
                top_games=2,
                recent_games=2
            )
            
            total_games = stats.get('white', 0) + stats.get('black', 0) + stats.get('draws', 0)
            
            if total_games < 100:  # Skip lines with too few games
                return None
            
            # Calculate performance score (favoring White slightly, as is traditional)
            win_rate_white = stats.get('white', 0) / total_games
            win_rate_black = stats.get('black', 0) / total_games
            draw_rate = stats.get('draws', 0) / total_games
            
            # Performance score: White wins = 1, Draws = 0.5, Black wins = 0
            performance_score = (win_rate_white + draw_rate * 0.5) * 100
            
            opening_info = stats.get('opening', {}) or {}
            
            return {
                'moves_sequence': moves_list,
                'eco_code': opening_info.get('eco', ''),
                'opening_name': opening_info.get('name', f"Opening: {' '.join(moves_list)}"),
                'white_wins': stats.get('white', 0),
                'black_wins': stats.get('black', 0),
                'draws': stats.get('draws', 0),
                'total_games': total_games,
                'win_rate_white': win_rate_white,
                'win_rate_black': win_rate_black,
                'draw_rate': draw_rate,
                'performance_score': performance_score,
                'collected_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exploring {moves_list}: {e}")
            return None
    
    def collect_popular_openings(self, max_openings=30):
        """Collect popular chess openings with their statistics."""
        logger.info(f"Starting collection of top {max_openings} openings")
        
        openings = []
        
        # Get popular first moves
        first_moves = self.get_top_first_moves()
        
        # Well-known opening sequences to explore
        popular_sequences = [
            # King's Pawn openings
            ['e4', 'e5', 'Nf3'],                    # Italian/Spanish setup
            ['e4', 'e5', 'Bc4'],                    # Italian Game
            ['e4', 'e5', 'Bb5'],                    # Spanish/Ruy Lopez
            ['e4', 'c5', 'Nf3'],                    # Sicilian Defense
            ['e4', 'c6', 'e5'],                     # Caro-Kann Defense
            ['e4', 'e6', 'e5'],                     # French Defense
            ['e4', 'Nf6'],                          # Alekhine's Defense
            
            # Queen's Pawn openings
            ['d4', 'd5', 'c4'],                     # Queen's Gambit
            ['d4', 'Nf6', 'c4'],                    # Queen's Indian setup
            ['d4', 'Nf6', 'Nf3'],                   # Queen's Pawn Game
            ['d4', 'g6', 'e4'],                     # King's Indian Defense
            ['d4', 'e6', 'e4'],                     # French Defense via d4
            ['d4', 'c5'],                           # Benoni Defense
            
            # Other openings
            ['Nf3', 'Nf6'],                         # Reti Opening
            ['c4', 'e5'],                           # English Opening
            ['c4', 'Nf6'],                          # English vs Nf6
            ['f4'],                                 # King's Indian Attack
            ['b3'],                                 # Nimzowitsch-Larsen Attack
            ['g3', 'g6'],                           # King's Indian Attack vs King's Indian
        ]
        
        # Add simple first moves as openings too
        for move_data in first_moves[:5]:
            opening_data = self.explore_opening_line([move_data['move']])
            if opening_data and opening_data['total_games'] >= 1000:
                openings.append(opening_data)
        
        # Explore popular sequences
        for sequence in popular_sequences:
            if len(openings) >= max_openings:
                break
                
            opening_data = self.explore_opening_line(sequence)
            if opening_data and opening_data['total_games'] >= 100:
                openings.append(opening_data)
        
        # Sort by a combination of popularity and performance
        openings.sort(key=lambda x: (x['performance_score'], x['total_games']), reverse=True)
        
        logger.info(f"Collection complete. Found {len(openings)} openings")
        return openings[:max_openings]
    
    def save_data(self, openings_data, filename=None):
        """Save collected data to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"database/openings_data_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(openings_data, f, indent=2)
        
        logger.info(f"Saved {len(openings_data)} openings to {filename}")
        return filename


def main():
    """Main execution function."""
    collector = SimpleOpeningsCollector()
    
    # Collect opening data
    openings = collector.collect_popular_openings(30)
    
    if openings:
        # Save to file
        filename = collector.save_data(openings)
        
        print(f"\n🎉 Successfully collected {len(openings)} openings!")
        print(f"📁 Saved to: {filename}")
        print(f"\nTop 5 openings by performance:")
        
        for i, opening in enumerate(openings[:5], 1):
            name = opening['opening_name']
            score = opening['performance_score']
            games = opening['total_games']
            eco = opening['eco_code']
            print(f"  {i}. {eco} {name}")
            print(f"     Score: {score:.1f}% | Games: {games:,}")
        
        return filename
    else:
        print("❌ No openings data collected")
        return None


if __name__ == "__main__":
    main()