"""
Service layer that wraps existing Python modules for API use.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from project root
load_dotenv(project_root / ".env")

from src.app.utils import load_current_season_data, get_current_week, run_simulation
from src.simulation.playoff import select_playoff_teams, generate_bracket, determine_conference_champions


def dataframe_to_dict(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert pandas DataFrame to list of dicts for JSON serialization."""
    if df.empty:
        return []
    
    # Replace NaN with None for JSON serialization
    # Also convert datetime objects to strings
    df_copy = df.copy()
    
    # Convert datetime columns to strings
    for col in df_copy.columns:
        if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
            df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        elif df_copy[col].dtype == 'object':
            # Check for datetime objects in object columns (skip conversion, handle in final pass)
            pass
    
    # Replace NaN/NaT with None
    df_copy = df_copy.replace({pd.NA: None, pd.NaT: None})
    
    # Convert to dict and handle any remaining datetime objects
    records = df_copy.to_dict('records')
    
    # Final pass to convert any remaining Timestamp objects
    for record in records:
        for key, value in record.items():
            if pd.api.types.is_datetime64_any_dtype(type(value)) or isinstance(value, pd.Timestamp):
                record[key] = str(value) if value is not None else None
    
    return records


def load_season_data(season: int) -> Dict[str, Any]:
    """
    Load season data and convert to JSON-serializable format.
    
    Args:
        season: Season year
        
    Returns:
        Dictionary with games, teams, rankings, champions, current_week
    """
    try:
        data = load_current_season_data(season)
        
        # Check if we have any data
        if data["games"].empty and data["teams"].empty and data["rankings"].empty:
            # Try to use a previous season's data structure as fallback
            print(f"Warning: No data available for {season}. Returning empty structure.")
        
        current_week = 1
        if not data["games"].empty:
            try:
                current_week = get_current_week(season, data["games"])
            except:
                current_week = 1
        
        return {
            "games": dataframe_to_dict(data["games"]),
            "teams": dataframe_to_dict(data["teams"]),
            "rankings": dataframe_to_dict(data["rankings"]),
            "champions": dataframe_to_dict(data["champions"]),
            "current_week": current_week
        }
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Error in load_season_data for {season}: {error_msg}")
        print(traceback.format_exc())
        
        # Return empty structure instead of crashing
        return {
            "games": [],
            "teams": [],
            "rankings": [],
            "champions": [],
            "current_week": 1
        }


def run_simulation_service(
    games_df: pd.DataFrame,
    teams_df: pd.DataFrame,
    game_outcomes: Dict[str, str],
    season: int,
    target_week: int,
    champions_df: Optional[pd.DataFrame] = None,
    previous_rankings_df: Optional[pd.DataFrame] = None,
    model_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run simulation and convert results to JSON-serializable format.
    
    Args:
        games_df: Base games DataFrame
        teams_df: Teams DataFrame
        game_outcomes: Dict of game_id -> winner
        season: Season year
        target_week: Target week for projection
        champions_df: Optional champions DataFrame
        previous_rankings_df: Optional previous week's rankings
        model_path: Optional model path
        
    Returns:
        Dictionary with rankings, playoff_teams, matchups
    """
    results = run_simulation(
        games_df=games_df,
        teams_df=teams_df,
        game_outcomes=game_outcomes,
        season=season,
        target_week=target_week,
        model_path=model_path,
        champions_df=champions_df,
        previous_rankings_df=previous_rankings_df
    )
    
    # Convert DataFrames to lists of dicts
    rankings_list = dataframe_to_dict(results["rankings"])
    playoff_teams_list = dataframe_to_dict(results["playoff_teams"])
    matchups_list = dataframe_to_dict(results["matchups"])
    
    return {
        "rankings": rankings_list,
        "playoff_teams": playoff_teams_list,
        "matchups": matchups_list
    }
