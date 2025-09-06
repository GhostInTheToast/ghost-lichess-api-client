#!/usr/bin/env python3
"""Quick test of Lichess API to understand the correct parameters."""

import berserk
import os
from dotenv import load_dotenv

load_dotenv('config/.env')

api_token = os.getenv('LICHESS_API_TOKEN')
print(f"Using API token: {api_token[:10]}...")

session = berserk.TokenSession(api_token)
client = berserk.Client(session=session)

print("\n1. Testing basic opening explorer...")
try:
    # Test with minimal parameters
    stats = client.opening_explorer.get_lichess_games()
    print(f"Success! Found {len(stats.get('moves', []))} moves")
    
    if 'moves' in stats:
        for i, move in enumerate(stats['moves'][:3]):
            print(f"  Move {i+1}: {move['san']} - {move['white']+move['black']+move['draws']} games")
    
except Exception as e:
    print(f"Error: {e}")

print("\n2. Testing with specific rating...")
try:
    # Test with single rating range
    stats = client.opening_explorer.get_lichess_games(ratings=['1600'])
    print(f"Success with rating filter! Found {len(stats.get('moves', []))} moves")
    
except Exception as e:
    print(f"Error with rating: {e}")

print("\n3. Testing with specific speed...")
try:
    # Test with single speed
    stats = client.opening_explorer.get_lichess_games(speeds=['blitz'])
    print(f"Success with speed filter! Found {len(stats.get('moves', []))} moves")
    
except Exception as e:
    print(f"Error with speed: {e}")

print("\n4. Testing combined filters...")
try:
    # Test with combined filters
    stats = client.opening_explorer.get_lichess_games(
        speeds=['blitz'],
        ratings=['1600'],
        moves=3
    )
    print(f"Success with combined filters! Found {len(stats.get('moves', []))} moves")
    
    # Check for opening information
    if 'opening' in stats:
        opening = stats['opening']
        if opening:
            print(f"Opening detected: {opening.get('name', 'Unknown')} ({opening.get('eco', 'No ECO')})")
    
except Exception as e:
    print(f"Error with combined filters: {e}")