"""
Pydantic schemas for API request/response models.
"""

from pydantic import BaseModel
from typing import Dict, List, Optional, Any


class Team(BaseModel):
    """Team information."""
    name: str
    abbreviation: Optional[str] = None
    conference: Optional[str] = None
    is_power5: Optional[bool] = None


class Ranking(BaseModel):
    """Team ranking."""
    rank: int
    team: str
    predicted_score: Optional[float] = None
    wins: Optional[int] = None
    losses: Optional[int] = None
    win_pct: Optional[float] = None
    sos_score: Optional[float] = None
    weighted_sos_score: Optional[float] = None
    wins_vs_top25: Optional[int] = None
    record_strength_score: Optional[float] = None
    is_conference_champion: Optional[bool] = None


class BracketMatchup(BaseModel):
    """Bracket matchup information."""
    round: str
    game: str
    team1: Optional[str] = None
    team1_seed: Optional[int] = None
    team2: Optional[str] = None
    team2_seed: Optional[int] = None


class PlayoffTeam(BaseModel):
    """Playoff team with seeding."""
    team: str
    seed: int
    predicted_rank: int
    is_auto_bid: bool
    conference: Optional[str] = None


class SimulationRequest(BaseModel):
    """Request model for simulation."""
    game_outcomes: Dict[str, str]  # game_id -> winner team name
    season: int
    target_week: int = 15


class SimulationResponse(BaseModel):
    """Response model for simulation results."""
    rankings: List[Ranking]
    playoff_teams: List[PlayoffTeam]
    matchups: List[BracketMatchup]


class SeasonDataResponse(BaseModel):
    """Response model for season data."""
    games: List[Dict[str, Any]]
    teams: List[Dict[str, Any]]
    rankings: List[Dict[str, Any]]
    champions: List[Dict[str, Any]]
    current_week: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    message: str
