"""
Scenario simulation engine.

This module handles "what-if" scenario simulations by updating game results
and recalculating features to generate new predictions.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from pathlib import Path

from ..features.compute import compute_features
from ..model.predict import predict_rankings, load_model


class SimulationEngine:
    """
    Engine for simulating CFP scenarios.
    
    Takes base season data and user-specified game outcomes,
    then generates updated rankings and playoff projections.
    """
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        Initialize simulation engine.
        
        Args:
            model_path: Path to trained model. If None, uses default location.
        """
        self.model = None
        self.model_path = model_path
        self._load_model()
    
    def _load_model(self):
        """Load the trained model."""
        try:
            self.model = load_model(self.model_path)
        except FileNotFoundError:
            print("Warning: Model not found. Simulation will not work until model is trained.")
            self.model = None
    
    def simulate_scenario(
        self,
        base_games_df: pd.DataFrame,
        base_teams_df: pd.DataFrame,
        game_outcomes: Dict[str, str],
        target_week: int,
        season: int,
        base_rankings_df: Optional[pd.DataFrame] = None,
        champions_df: Optional[pd.DataFrame] = None,
        previous_rankings_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Simulate a scenario with modified game outcomes.
        
        Args:
            base_games_df: Original games DataFrame
            game_outcomes: Dict mapping game_id to winner team name
            target_week: Week to project rankings for
            season: Season year
            base_teams_df: Teams DataFrame
            base_rankings_df: Optional baseline rankings for comparison
            champions_df: Optional conference champions DataFrame
            previous_rankings_df: Optional previous week's rankings
            
        Returns:
            DataFrame with predicted rankings (team, predicted_rank, predicted_score)
        """
        if self.model is None:
            raise ValueError("Model not loaded. Cannot generate predictions.")
        
        # Create a copy of games DataFrame
        updated_games = base_games_df.copy()
        
        # Update game outcomes
        updated_games = self._update_game_outcomes(updated_games, game_outcomes, season)
        
        # Recompute features for all teams
        features_df = compute_features(
            season=season,
            week=target_week,
            games_df=updated_games,
            teams_df=base_teams_df,
            rankings_df=None,  # No target for prediction
            champions_df=champions_df,
            previous_rankings_df=previous_rankings_df,
        )
        
        if features_df.empty:
            return pd.DataFrame()
        
        # Generate predictions
        predictions = predict_rankings(features_df, model=self.model)
        
        # Apply head-to-head post-processing rule
        # If Team A beat Team B and resumes are similar, rank A above B
        predictions = self._apply_head_to_head_rule(
            predictions, updated_games, season, target_week
        )
        
        return predictions
    
    def _apply_head_to_head_rule(
        self,
        rankings_df: pd.DataFrame,
        games_df: pd.DataFrame,
        season: int,
        week: int
    ) -> pd.DataFrame:
        """
        Apply head-to-head post-processing rule.
        
        If Team A beat Team B and their predicted scores are close (comparable resumes),
        ensure A is ranked above B.
        
        Args:
            rankings_df: Predicted rankings DataFrame
            games_df: Games DataFrame
            season: Season year
            week: Week number
            
        Returns:
            Updated rankings DataFrame
        """
        if rankings_df.empty:
            return rankings_df
        
        rankings = rankings_df.copy().sort_values("predicted_score")
        
        # Get head-to-head results for this season/week
        season_games = games_df[
            (games_df["season"] == season) &
            (games_df["week"] <= week) &
            (games_df["team_won"].notna())
        ]
        
        # Create head-to-head map: {loser: [winners who beat them]}
        h2h_map = {}
        for _, game in season_games.iterrows():
            if game["team_won"]:
                winner = game["team"]
                loser = game["opponent"]
                if loser not in h2h_map:
                    h2h_map[loser] = []
                h2h_map[loser].append(winner)
        
        # Check for head-to-head violations
        # If two teams are close in score (within threshold) and one beat the other,
        # swap them if needed
        score_threshold = 0.1  # Teams within 0.1 score are "comparable"
        
        for i in range(len(rankings) - 1):
            team_a = rankings.iloc[i]["team"]
            team_b = rankings.iloc[i + 1]["team"]
            score_a = rankings.iloc[i]["predicted_score"]
            score_b = rankings.iloc[i + 1]["predicted_score"]
            
            # Check if scores are close (comparable)
            if abs(score_a - score_b) <= score_threshold:
                # Check head-to-head
                # Did A beat B?
                if team_b in h2h_map and team_a in h2h_map[team_b]:
                    # A beat B, but B is ranked higher - swap them
                    rankings.iloc[i], rankings.iloc[i + 1] = rankings.iloc[i + 1].copy(), rankings.iloc[i].copy()
                # Did B beat A? (A is already above B, so no swap needed)
        
        # Reassign ranks after potential swaps
        rankings = rankings.sort_values("predicted_score").reset_index(drop=True)
        rankings["predicted_rank"] = range(1, len(rankings) + 1)
        
        return rankings
    
    def simulate_weekly_rankings(
        self,
        base_games_df: pd.DataFrame,
        base_teams_df: pd.DataFrame,
        game_outcomes: Dict[str, str],
        start_week: int,
        end_week: int,
        season: int,
        base_rankings_df: Optional[pd.DataFrame] = None,
        champions_df: Optional[pd.DataFrame] = None
    ) -> Dict[int, pd.DataFrame]:
        """
        Simulate rankings week-by-week.
        
        Args:
            base_games_df: Original games DataFrame
            base_teams_df: Teams DataFrame
            game_outcomes: Dict mapping game_id to winner
            start_week: First week to predict
            end_week: Last week to predict
            season: Season year
            base_rankings_df: Optional baseline rankings
            champions_df: Optional conference champions
            
        Returns:
            Dictionary mapping week -> predicted rankings DataFrame
        """
        updated_games = base_games_df.copy()
        updated_games = self._update_game_outcomes(updated_games, game_outcomes, season)
        
        weekly_rankings = {}
        previous_rankings = base_rankings_df
        
        for week in range(start_week, end_week + 1):
            # Get previous week's rankings for feature computation
            if previous_rankings is not None:
                prev_week_rankings = previous_rankings[
                    (previous_rankings["season"] == season) &
                    (previous_rankings["week"] == week - 1)
                ] if week > start_week else None
            else:
                prev_week_rankings = None
            
            # Compute features for this week
            features_df = compute_features(
                season=season,
                week=week,
                games_df=updated_games,
                teams_df=base_teams_df,
                rankings_df=None,
                champions_df=champions_df if week >= 15 else None,
                previous_rankings_df=prev_week_rankings
            )
            
            if features_df.empty:
                continue
            
            # Generate predictions
            predictions = predict_rankings(features_df, model=self.model)
            
            # Apply head-to-head rule
            predictions = self._apply_head_to_head_rule(
                predictions, updated_games, season, week
            )
            
            weekly_rankings[week] = predictions
            
            # Use this week's predictions as previous week for next iteration
            previous_rankings = predictions.rename(columns={
                "predicted_rank": "rank",
                "team": "team_id"
            })
            previous_rankings["season"] = season
            previous_rankings["week"] = week
        
        return weekly_rankings
    
    def _update_game_outcomes(
        self,
        games_df: pd.DataFrame,
        game_outcomes: Dict[str, str],
        season: int
    ) -> pd.DataFrame:
        """
        Update game results based on user-specified outcomes.
        
        Args:
            games_df: Games DataFrame
            game_outcomes: Dict mapping game_id to winner
            season: Season year
            
        Returns:
            Updated games DataFrame
        """
        updated = games_df.copy()
        
        for game_id, winner in game_outcomes.items():
            # Find games matching this game_id
            game_mask = (
                (updated["game_id"] == game_id) |
                (updated.get("game_id", pd.Series()) == game_id)
            )
            
            # If game_id column doesn't exist, try to match by season/week/teams
            if not game_mask.any() and "game_id" not in updated.columns:
                # Try to construct game_id from other columns
                # This is a fallback if game_id wasn't in original data
                continue
            
            games_to_update = updated[game_mask]
            
            for idx in games_to_update.index:
                game = updated.loc[idx]
                
                # Determine if the team in this row won or lost
                if game["team"] == winner:
                    # This team won
                    updated.at[idx, "team_won"] = True
                    updated.at[idx, "team_score"] = max(
                        updated.at[idx, "team_score"] if pd.notna(updated.at[idx, "team_score"]) else 0,
                        updated.at[idx, "opp_score"] if pd.notna(updated.at[idx, "opp_score"]) else 0
                    ) + 1  # Ensure winner has higher score
                    if pd.notna(updated.at[idx, "opp_score"]):
                        updated.at[idx, "opp_score"] = updated.at[idx, "team_score"] - 1
                elif game["opponent"] == winner:
                    # Opponent won (this team lost)
                    updated.at[idx, "team_won"] = False
                    updated.at[idx, "opp_score"] = max(
                        updated.at[idx, "team_score"] if pd.notna(updated.at[idx, "team_score"]) else 0,
                        updated.at[idx, "opp_score"] if pd.notna(updated.at[idx, "opp_score"]) else 0
                    ) + 1
                    if pd.notna(updated.at[idx, "team_score"]):
                        updated.at[idx, "team_score"] = updated.at[idx, "opp_score"] - 1
        
        return updated
    
    def compare_scenarios(
        self,
        baseline_rankings: pd.DataFrame,
        scenario_rankings: pd.DataFrame,
        team_col: str = "team",
        rank_col: str = "predicted_rank"
    ) -> pd.DataFrame:
        """
        Compare baseline vs scenario rankings to show changes.
        
        Args:
            baseline_rankings: Baseline predicted rankings
            scenario_rankings: Scenario predicted rankings
            team_col: Column name for team
            rank_col: Column name for rank
            
        Returns:
            DataFrame with comparison (team, baseline_rank, scenario_rank, rank_change)
        """
        baseline = baseline_rankings[[team_col, rank_col]].copy()
        baseline.columns = [team_col, "baseline_rank"]
        
        scenario = scenario_rankings[[team_col, rank_col]].copy()
        scenario.columns = [team_col, "scenario_rank"]
        
        comparison = pd.merge(baseline, scenario, on=team_col, how="outer")
        comparison["rank_change"] = comparison["baseline_rank"] - comparison["scenario_rank"]
        # Positive change = moved up, negative = moved down
        
        return comparison.sort_values("scenario_rank")


def simulate_scenario(
    base_games_df: pd.DataFrame,
    base_teams_df: pd.DataFrame,
    game_outcomes: Dict[str, str],
    target_week: int,
    season: int,
    model_path: Optional[Path] = None,
    champions_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Convenience function to simulate a scenario.
    
    Args:
        base_games_df: Original games DataFrame
        base_teams_df: Teams DataFrame
        game_outcomes: Dict mapping game_id to winner
        target_week: Week to project
        season: Season year
        model_path: Optional path to model
        champions_df: Optional conference champions
        
    Returns:
        Predicted rankings DataFrame
    """
    engine = SimulationEngine(model_path=model_path)
    return engine.simulate_scenario(
        base_games_df=base_games_df,
        base_teams_df=base_teams_df,
        game_outcomes=game_outcomes,
        target_week=target_week,
        season=season,
        champions_df=champions_df
    )

