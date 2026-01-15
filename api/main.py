"""
FastAPI application for CFP Predictor backend.
"""

import sys
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from .schemas import (
    SimulationRequest,
    SimulationResponse,
    SeasonDataResponse,
    HealthResponse,
    Ranking,
    PlayoffTeam,
    BracketMatchup
)
from .services import load_season_data, run_simulation_service

# Initialize FastAPI app
app = FastAPI(
    title="CFP Predictor API",
    description="API for College Football Playoff predictions and simulations",
    version="1.0.0"
)

# Configure CORS
# In production, set CORS_ORIGINS environment variable
cors_origins_env = os.getenv("CORS_ORIGINS", "")
cors_origins = (
    cors_origins_env.split(",") if cors_origins_env else ["http://localhost:3000", "http://localhost:3001"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Get model path
MODEL_PATH = project_root / "data" / "models" / "cfp_predictor.pkl"


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    model_exists = MODEL_PATH.exists()
    return {
        "status": "healthy" if model_exists else "degraded",
        "message": "Model loaded" if model_exists else "Model not found"
    }


@app.get("/api/season/{year}/data", response_model=SeasonDataResponse)
async def get_season_data(year: int):
    """
    Get season data (games, teams, rankings, champions).
    
    Args:
        year: Season year
        
    Returns:
        Season data including games, teams, rankings, champions, current_week
    """
    try:
        import traceback
        data = load_season_data(year)
        return SeasonDataResponse(**data)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error loading season {year}: {str(e)}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Error loading season data: {str(e)}")


@app.post("/api/simulate", response_model=SimulationResponse)
async def simulate(request: SimulationRequest):
    """
    Run a simulation with specified game outcomes.
    
    Args:
        request: Simulation request with game outcomes, season, target_week
        
    Returns:
        Simulation results including rankings, playoff teams, matchups
    """
    try:
        # Load season data
        season_data = load_season_data(request.season)
        
        # Convert back to DataFrames for simulation
        games_df = pd.DataFrame(season_data["games"])
        teams_df = pd.DataFrame(season_data["teams"])
        champions_df = pd.DataFrame(season_data["champions"]) if season_data["champions"] else None
        
        # Get previous week's rankings if available
        previous_rankings_df = None
        if season_data["rankings"]:
            rankings_df = pd.DataFrame(season_data["rankings"])
            if request.target_week > 1:
                prev_week = request.target_week - 1
                previous_rankings_df = rankings_df[
                    (rankings_df["season"] == request.season) &
                    (rankings_df["week"] == prev_week)
                ] if "week" in rankings_df.columns else None
        
        # Run simulation
        results = run_simulation_service(
            games_df=games_df,
            teams_df=teams_df,
            game_outcomes=request.game_outcomes,
            season=request.season,
            target_week=request.target_week,
            champions_df=champions_df,
            previous_rankings_df=previous_rankings_df,
            model_path=MODEL_PATH if MODEL_PATH.exists() else None
        )
        
        # Convert to response models
        rankings = [Ranking(**r) for r in results["rankings"]]
        playoff_teams = [PlayoffTeam(**p) for p in results["playoff_teams"]]
        matchups = [BracketMatchup(**m) for m in results["matchups"]]
        
        return SimulationResponse(
            rankings=rankings,
            playoff_teams=playoff_teams,
            matchups=matchups
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running simulation: {str(e)}")


@app.get("/api/season/{year}/week/{week}/rankings")
async def get_weekly_rankings(year: int, week: int):
    """
    Get rankings for a specific week.
    
    Args:
        year: Season year
        week: Week number
        
    Returns:
        List of rankings for that week
    """
    try:
        season_data = load_season_data(year)
        rankings_df = pd.DataFrame(season_data["rankings"])
        
        # Filter by week
        week_rankings = rankings_df[
            (rankings_df["season"] == year) &
            (rankings_df["week"] == week)
        ] if "week" in rankings_df.columns else rankings_df
        
        return {"rankings": week_rankings.to_dict('records')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading rankings: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
