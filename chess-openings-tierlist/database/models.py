"""
SQLAlchemy models for chess openings database.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy import create_engine
import json

Base = declarative_base()


class Opening(Base):
    """Chess opening information."""
    __tablename__ = "openings"
    
    id = Column(Integer, primary_key=True, index=True)
    eco_code = Column(String(10), index=True)  # ECO classification (e.g., "E20")
    name = Column(String(200), index=True)  # Opening name (e.g., "Queen's Gambit")
    moves_sequence = Column(JSON)  # List of moves in algebraic notation
    moves_uci = Column(JSON)  # List of moves in UCI notation
    fen_position = Column(Text)  # Final FEN position after moves
    description = Column(Text)  # Optional description of the opening
    popularity_rank = Column(Integer, index=True)  # Popularity ranking (1 = most popular)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # Whether to include in tier lists
    
    # Relationships
    statistics = relationship("OpeningStatistic", back_populates="opening", cascade="all, delete-orphan")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_eco_name', 'eco_code', 'name'),
        Index('idx_popularity', 'popularity_rank', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Opening(eco_code='{self.eco_code}', name='{self.name}')>"
    
    @property
    def moves_string(self):
        """Return moves as a space-separated string."""
        if self.moves_sequence:
            return " ".join(self.moves_sequence)
        return ""


class OpeningStatistic(Base):
    """Performance statistics for chess openings."""
    __tablename__ = "opening_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    opening_id = Column(Integer, ForeignKey("openings.id"), nullable=False, index=True)
    
    # Game counts
    white_wins = Column(Integer, default=0)
    black_wins = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    total_games = Column(Integer, default=0, index=True)
    
    # Performance metrics
    win_rate_white = Column(Float, index=True)  # White win percentage
    win_rate_black = Column(Float, index=True)  # Black win percentage
    draw_rate = Column(Float)  # Draw percentage
    performance_score = Column(Float, index=True)  # Composite performance score
    
    # Context filters
    rating_range = Column(String(20), index=True)  # e.g., "1800-2000"
    time_control = Column(String(20), index=True)  # e.g., "blitz", "rapid"
    date_range_start = Column(DateTime, index=True)  # Statistics period start
    date_range_end = Column(DateTime, index=True)  # Statistics period end
    
    # Additional metrics
    average_rating = Column(Integer)  # Average rating of players in games
    average_game_length = Column(Integer)  # Average number of moves
    frequency_rank = Column(Integer, index=True)  # Frequency rank within filters
    
    # Metadata
    collected_at = Column(DateTime, default=datetime.utcnow, index=True)
    data_source = Column(String(50), default="lichess")  # Data source identifier
    
    # Relationships
    opening = relationship("Opening", back_populates="statistics")
    
    # Indexes for efficient filtering
    __table_args__ = (
        Index('idx_opening_context', 'opening_id', 'rating_range', 'time_control'),
        Index('idx_performance', 'performance_score', 'total_games'),
        Index('idx_date_range', 'date_range_start', 'date_range_end'),
    )
    
    def __repr__(self):
        return f"<OpeningStatistic(opening_id={self.opening_id}, games={self.total_games}, score={self.performance_score})>"
    
    @property
    def win_rate_for_white(self):
        """Win rate from White's perspective (includes draws as 0.5)."""
        if self.total_games == 0:
            return 0.0
        return (self.white_wins + self.draws * 0.5) / self.total_games
    
    @property
    def win_rate_for_black(self):
        """Win rate from Black's perspective (includes draws as 0.5)."""
        if self.total_games == 0:
            return 0.0
        return (self.black_wins + self.draws * 0.5) / self.total_games


class DataUpdateLog(Base):
    """Log of data update operations."""
    __tablename__ = "data_update_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    operation_type = Column(String(50), index=True)  # "full_update", "incremental", etc.
    status = Column(String(20), index=True)  # "success", "error", "in_progress"
    
    # Update details
    openings_processed = Column(Integer, default=0)
    statistics_updated = Column(Integer, default=0)
    api_requests_made = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, index=True)
    duration_seconds = Column(Float)
    
    # Error information
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # Configuration used
    rating_ranges = Column(JSON)
    time_controls = Column(JSON)
    date_range = Column(JSON)
    
    def __repr__(self):
        return f"<DataUpdateLog(type='{self.operation_type}', status='{self.status}')>"


class TierListEntry(Base):
    """User-created tier list entries."""
    __tablename__ = "tier_list_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    opening_id = Column(Integer, ForeignKey("openings.id"), nullable=False, index=True)
    
    # Tier information
    tier_rank = Column(String(5), index=True)  # "S", "A", "B", "C", "D"
    tier_position = Column(Integer)  # Position within tier (1 = leftmost)
    
    # Context for the tier list
    rating_range = Column(String(20), index=True)
    time_control = Column(String(20), index=True)
    user_id = Column(String(100), index=True)  # For future user system
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    opening = relationship("Opening")
    
    # Ensure uniqueness per context
    __table_args__ = (
        Index('idx_tier_context', 'rating_range', 'time_control', 'user_id'),
    )
    
    def __repr__(self):
        return f"<TierListEntry(opening_id={self.opening_id}, tier='{self.tier_rank}')>"


# Database utility functions
def create_database(database_url: str = "sqlite:///./chess_openings.db"):
    """Create database and all tables."""
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    return engine


def get_session(engine) -> Session:
    """Get database session."""
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


# Pydantic models for API responses
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class OpeningResponse(BaseModel):
    """API response model for opening data."""
    id: int
    eco_code: Optional[str]
    name: Optional[str]
    moves_sequence: List[str]
    moves_string: str
    popularity_rank: Optional[int]
    
    class Config:
        from_attributes = True


class OpeningStatisticResponse(BaseModel):
    """API response model for opening statistics."""
    id: int
    opening_id: int
    white_wins: int
    black_wins: int
    draws: int
    total_games: int
    win_rate_white: float
    win_rate_black: float
    draw_rate: float
    performance_score: float
    rating_range: Optional[str]
    time_control: Optional[str]
    average_rating: Optional[int]
    collected_at: datetime
    
    class Config:
        from_attributes = True


class TierListResponse(BaseModel):
    """API response model for tier list data."""
    opening: OpeningResponse
    statistics: OpeningStatisticResponse
    tier_rank: Optional[str]
    tier_position: Optional[int]
    
    class Config:
        from_attributes = True