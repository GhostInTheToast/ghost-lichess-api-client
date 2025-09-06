"""
FastAPI backend for chess openings tier list application.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, desc, func
from pydantic import BaseModel
from dotenv import load_dotenv

from database.models import (
    Opening, OpeningStatistic, TierListEntry, DataUpdateLog,
    OpeningResponse, OpeningStatisticResponse, TierListResponse,
    get_session
)

# Load environment variables
load_dotenv('../config/.env')

# Initialize FastAPI app
app = FastAPI(
    title="Chess Openings Tier List API",
    description="API for managing and serving chess opening statistics and tier lists",
    version="1.0.0"
)

# Configure CORS
origins = os.getenv('CORS_ORIGINS', '["http://localhost:3000"]')
if isinstance(origins, str):
    import json
    origins = json.loads(origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
database_url = os.getenv('DATABASE_URL', 'sqlite:///./chess_openings.db')
engine = create_engine(database_url)

def get_db() -> Session:
    """Dependency to get database session."""
    session = get_session(engine)
    try:
        yield session
    finally:
        session.close()


# Pydantic models for requests/responses
class FilterParams(BaseModel):
    """Filtering parameters for opening queries."""
    rating_range: Optional[str] = None
    time_control: Optional[str] = None
    min_games: Optional[int] = 100
    sort_by: Optional[str] = "performance_score"
    order: Optional[str] = "desc"
    limit: Optional[int] = 50


class TierListUpdate(BaseModel):
    """Model for updating tier list entries."""
    opening_id: int
    tier_rank: str
    tier_position: int


# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Chess Openings Tier List API", "status": "healthy"}


@app.get("/openings", response_model=List[OpeningResponse])
async def get_openings(
    db: Session = Depends(get_db),
    rating_range: Optional[str] = Query(None, description="Rating range filter (e.g., '1800-2000')"),
    time_control: Optional[str] = Query(None, description="Time control filter (e.g., 'blitz')"),
    min_games: int = Query(100, description="Minimum number of games"),
    sort_by: str = Query("performance_score", description="Sort field"),
    order: str = Query("desc", description="Sort order (asc/desc)"),
    limit: int = Query(50, description="Maximum number of results")
):
    """Get list of openings with optional filtering."""
    
    query = db.query(Opening).join(OpeningStatistic)
    
    # Apply filters
    if rating_range:
        query = query.filter(OpeningStatistic.rating_range == rating_range)
    if time_control:
        query = query.filter(OpeningStatistic.time_control == time_control)
    if min_games:
        query = query.filter(OpeningStatistic.total_games >= min_games)
    
    # Apply sorting
    sort_field = getattr(OpeningStatistic, sort_by, OpeningStatistic.performance_score)
    if order.lower() == "desc":
        query = query.order_by(desc(sort_field))
    else:
        query = query.order_by(sort_field)
    
    # Apply limit
    openings = query.limit(limit).all()
    
    return [OpeningResponse.model_validate(opening) for opening in openings]


@app.get("/openings/{opening_id}", response_model=OpeningResponse)
async def get_opening(opening_id: int, db: Session = Depends(get_db)):
    """Get a specific opening by ID."""
    opening = db.query(Opening).filter(Opening.id == opening_id).first()
    if not opening:
        raise HTTPException(status_code=404, detail="Opening not found")
    
    return OpeningResponse.model_validate(opening)


@app.get("/openings/{opening_id}/statistics", response_model=List[OpeningStatisticResponse])
async def get_opening_statistics(
    opening_id: int,
    db: Session = Depends(get_db),
    rating_range: Optional[str] = Query(None),
    time_control: Optional[str] = Query(None)
):
    """Get statistics for a specific opening."""
    query = db.query(OpeningStatistic).filter(OpeningStatistic.opening_id == opening_id)
    
    if rating_range:
        query = query.filter(OpeningStatistic.rating_range == rating_range)
    if time_control:
        query = query.filter(OpeningStatistic.time_control == time_control)
    
    statistics = query.order_by(desc(OpeningStatistic.collected_at)).all()
    
    return [OpeningStatisticResponse.model_validate(stat) for stat in statistics]


@app.get("/tier-list", response_model=List[TierListResponse])
async def get_tier_list(
    db: Session = Depends(get_db),
    rating_range: Optional[str] = Query("all", description="Rating range filter"),
    time_control: Optional[str] = Query("all", description="Time control filter"),
    user_id: Optional[str] = Query("default", description="User ID for personalized tier lists")
):
    """Get tier list data with openings and their statistics."""
    
    # Query for openings with their latest statistics
    query = db.query(Opening, OpeningStatistic).join(
        OpeningStatistic, Opening.id == OpeningStatistic.opening_id
    ).filter(Opening.is_active == True)
    
    # Apply filters
    if rating_range and rating_range != "all":
        query = query.filter(OpeningStatistic.rating_range == rating_range)
    if time_control and time_control != "all":
        query = query.filter(OpeningStatistic.time_control == time_control)
    
    # Get latest statistics for each opening
    subquery = db.query(
        OpeningStatistic.opening_id,
        func.max(OpeningStatistic.collected_at).label('latest_collected_at')
    ).group_by(OpeningStatistic.opening_id).subquery()
    
    query = query.join(
        subquery,
        (OpeningStatistic.opening_id == subquery.c.opening_id) &
        (OpeningStatistic.collected_at == subquery.c.latest_collected_at)
    )
    
    # Order by performance score
    query = query.order_by(desc(OpeningStatistic.performance_score))
    
    results = query.limit(50).all()
    
    # Format response
    tier_list = []
    for opening, statistic in results:
        # Try to get tier list entry
        tier_entry = db.query(TierListEntry).filter(
            TierListEntry.opening_id == opening.id,
            TierListEntry.rating_range == rating_range,
            TierListEntry.time_control == time_control,
            TierListEntry.user_id == user_id
        ).first()
        
        tier_data = TierListResponse(
            opening=OpeningResponse.model_validate(opening),
            statistics=OpeningStatisticResponse.model_validate(statistic),
            tier_rank=tier_entry.tier_rank if tier_entry else None,
            tier_position=tier_entry.tier_position if tier_entry else None
        )
        tier_list.append(tier_data)
    
    return tier_list


@app.post("/tier-list")
async def update_tier_list(
    updates: List[TierListUpdate],
    db: Session = Depends(get_db),
    rating_range: str = Query("all"),
    time_control: str = Query("all"),
    user_id: str = Query("default")
):
    """Update tier list entries."""
    
    try:
        for update in updates:
            # Check if entry exists
            existing = db.query(TierListEntry).filter(
                TierListEntry.opening_id == update.opening_id,
                TierListEntry.rating_range == rating_range,
                TierListEntry.time_control == time_control,
                TierListEntry.user_id == user_id
            ).first()
            
            if existing:
                existing.tier_rank = update.tier_rank
                existing.tier_position = update.tier_position
                existing.updated_at = datetime.utcnow()
            else:
                new_entry = TierListEntry(
                    opening_id=update.opening_id,
                    tier_rank=update.tier_rank,
                    tier_position=update.tier_position,
                    rating_range=rating_range,
                    time_control=time_control,
                    user_id=user_id
                )
                db.add(new_entry)
        
        db.commit()
        return {"message": "Tier list updated successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update tier list: {str(e)}")


@app.get("/statistics/summary")
async def get_statistics_summary(db: Session = Depends(get_db)):
    """Get summary statistics about the data."""
    
    total_openings = db.query(Opening).filter(Opening.is_active == True).count()
    total_statistics = db.query(OpeningStatistic).count()
    
    # Get latest update info
    latest_update = db.query(DataUpdateLog).filter(
        DataUpdateLog.status == "success"
    ).order_by(desc(DataUpdateLog.completed_at)).first()
    
    # Get rating range and time control options
    rating_ranges = db.query(OpeningStatistic.rating_range).distinct().all()
    time_controls = db.query(OpeningStatistic.time_control).distinct().all()
    
    return {
        "total_openings": total_openings,
        "total_statistics": total_statistics,
        "last_updated": latest_update.completed_at if latest_update else None,
        "available_rating_ranges": [r[0] for r in rating_ranges if r[0]],
        "available_time_controls": [t[0] for t in time_controls if t[0]]
    }


@app.get("/statistics/top-performers")
async def get_top_performers(
    db: Session = Depends(get_db),
    limit: int = Query(10, description="Number of top performers to return"),
    metric: str = Query("performance_score", description="Metric to sort by")
):
    """Get top performing openings by specified metric."""
    
    sort_field = getattr(OpeningStatistic, metric, OpeningStatistic.performance_score)
    
    query = db.query(Opening, OpeningStatistic).join(
        OpeningStatistic, Opening.id == OpeningStatistic.opening_id
    ).filter(
        Opening.is_active == True,
        OpeningStatistic.total_games >= 100  # Minimum games threshold
    ).order_by(desc(sort_field)).limit(limit)
    
    results = query.all()
    
    top_performers = []
    for opening, statistic in results:
        top_performers.append({
            "opening": OpeningResponse.model_validate(opening),
            "statistics": OpeningStatisticResponse.model_validate(statistic),
            "metric_value": getattr(statistic, metric)
        })
    
    return top_performers


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', '8000'))
    
    uvicorn.run("main:app", host=host, port=port, reload=True)