"""
Feature computation utility functions.

This module contains helper functions for computing individual features
that mirror the CFP committee's evaluation criteria.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Set


# Power 5 conferences (historical, pre-2024 realignment)
POWER_5_CONFERENCES = {
    "SEC", "Big Ten", "Big 12", "ACC", "Pac-12"
}


def compute_record_features(
    games_df: pd.DataFrame,
    team: str,
    season: int,
    week: int
) -> Dict[str, float]:
    """
    Compute basic win-loss record features.
    
    Args:
        games_df: Processed games DataFrame
        team: Team name
        season: Season year
        week: Week number (cutoff)
        
    Returns:
        Dictionary with record features
    """
    # Filter games for this team up to this week
    team_games = games_df[
        (games_df["team"] == team) &
        (games_df["season"] == season) &
        (games_df["week"] <= week) &
        (games_df["team_won"].notna())
    ]
    
    wins = team_games["team_won"].sum()
    losses = len(team_games) - wins
    games_played = len(team_games)
    win_pct = wins / games_played if games_played > 0 else 0.0
    
    # Conference vs non-conference
    conf_games = team_games[team_games.get("is_conference_game", False)]
    conf_wins = conf_games["team_won"].sum() if not conf_games.empty else 0
    conf_losses = len(conf_games) - conf_wins
    
    non_conf_games = team_games[~team_games.get("is_conference_game", True)]
    non_conf_wins = non_conf_games["team_won"].sum() if not non_conf_games.empty else 0
    non_conf_losses = len(non_conf_games) - non_conf_wins
    
    return {
        "wins": float(wins),
        "losses": float(losses),
        "games_played": float(games_played),
        "win_pct": win_pct,
        "conference_wins": float(conf_wins),
        "conference_losses": float(conf_losses),
        "non_conference_wins": float(non_conf_wins),
        "non_conference_losses": float(non_conf_losses)
    }


def compute_sos(
    games_df: pd.DataFrame,
    team: str,
    season: int,
    week: int,
    team_records: Optional[pd.DataFrame] = None,
    previous_rankings: Optional[pd.DataFrame] = None
) -> Dict[str, float]:
    """
    Compute Strength of Schedule metrics.
    
    Enhanced version includes weighted SOS that emphasizes games against
    strong opponents (Top 25 teams count more).
    
    Args:
        games_df: Processed games DataFrame
        team: Team name
        season: Season year
        week: Week number (cutoff)
        team_records: Optional pre-computed team records DataFrame
        previous_rankings: Optional previous week's rankings for Top 25 weighting
        
    Returns:
        Dictionary with SOS features
    """
    # Get team's games
    team_games = games_df[
        (games_df["team"] == team) &
        (games_df["season"] == season) &
        (games_df["week"] <= week)
    ]
    
    if team_games.empty:
        return {
            "sos_score": 0.0,
            "opponents_avg_wins": 0.0,
            "opponents_avg_win_pct": 0.0,
            "weighted_sos_score": 0.0,
            "sos_of_sos": 0.0
        }
    
    # Compute opponent records
    if team_records is None:
        # Compute records on the fly (less efficient)
        opponent_records = []
        for _, game in team_games.iterrows():
            opp = game["opponent"]
            opp_games = games_df[
                (games_df["team"] == opp) &
                (games_df["season"] == season) &
                (games_df["week"] <= game["week"]) &
                (games_df["team_won"].notna())
            ]
            if not opp_games.empty:
                opp_wins = opp_games["team_won"].sum()
                opp_games_played = len(opp_games)
                opponent_records.append({
                    "opponent": opp,
                    "wins": opp_wins,
                    "games_played": opp_games_played,
                    "win_pct": opp_wins / opp_games_played if opp_games_played > 0 else 0.0
                })
    else:
        # Use pre-computed records
        opponent_records = []
        for _, game in team_games.iterrows():
            opp = game["opponent"]
            opp_week = game["week"]
            opp_record = team_records[
                (team_records["team"] == opp) &
                (team_records["season"] == season) &
                (team_records["as_of_week"] == opp_week)
            ]
            if not opp_record.empty:
                rec = opp_record.iloc[0]
                opponent_records.append({
                    "opponent": opp,
                    "wins": rec["wins"],
                    "games_played": rec["games_played"],
                    "win_pct": rec["win_pct"]
                })
    
    if not opponent_records:
        return {
            "sos_score": 0.0,
            "opponents_avg_wins": 0.0,
            "opponents_avg_win_pct": 0.0,
            "weighted_sos_score": 0.0,
            "sos_of_sos": 0.0
        }
    
    opp_df = pd.DataFrame(opponent_records)
    
    # Basic SOS (average opponent win %)
    basic_sos = float(opp_df["win_pct"].mean())
    
    # Weighted SOS: weight games by opponent quality
    # Top 25 opponents get 2x weight, Top 10 get 3x weight
    weighted_scores = []
    prev_week = week - 1 if week > 1 else week
    
    for _, game in team_games.iterrows():
        opp = game["opponent"]
        weight = 1.0  # Base weight
        
        # Check if opponent was ranked
        if previous_rankings is not None:
            opp_ranked = previous_rankings[
                (previous_rankings["team_id"] == opp) &
                (previous_rankings["season"] == season) &
                (previous_rankings["week"] == prev_week)
            ]
            if not opp_ranked.empty:
                opp_rank = opp_ranked.iloc[0]["rank"]
                if opp_rank <= 10:
                    weight = 3.0  # Top 10
                elif opp_rank <= 25:
                    weight = 2.0  # Top 25
        
        # Get opponent's win pct
        opp_record = opp_df[opp_df["opponent"] == opp]
        if not opp_record.empty:
            opp_win_pct = opp_record.iloc[0]["win_pct"]
            weighted_scores.append(opp_win_pct * weight)
    
    weighted_sos = float(np.mean(weighted_scores)) if weighted_scores else basic_sos
    
    # SOS of SOS: average of opponents' opponent win %
    # This is computationally expensive, so we'll compute a simplified version
    # by averaging the basic SOS of opponents
    sos_of_sos = 0.0
    if len(opp_df) > 0:
        # Simplified: use opponents' average win pct as proxy for their SOS
        # In full implementation, would compute each opponent's SOS
        sos_of_sos = basic_sos  # Placeholder - full implementation would be more complex
    
    return {
        "sos_score": basic_sos,
        "opponents_avg_wins": float(opp_df["wins"].mean()),
        "opponents_avg_win_pct": basic_sos,
        "weighted_sos_score": weighted_sos,
        "sos_of_sos": sos_of_sos
    }


def compute_quality_wins(
    games_df: pd.DataFrame,
    team: str,
    season: int,
    week: int,
    team_records: Optional[pd.DataFrame] = None,
    previous_rankings: Optional[pd.DataFrame] = None
) -> Dict[str, float]:
    """
    Compute quality wins and bad losses metrics.
    
    Args:
        games_df: Processed games DataFrame
        team: Team name
        season: Season year
        week: Week number (cutoff)
        team_records: Optional pre-computed team records
        previous_rankings: Optional previous week's rankings for Top 25 wins
        
    Returns:
        Dictionary with quality win/bad loss features
    """
    # Get team's wins and losses
    team_games = games_df[
        (games_df["team"] == team) &
        (games_df["season"] == season) &
        (games_df["week"] <= week) &
        (games_df["team_won"].notna())
    ]
    
    wins = team_games[team_games["team_won"] == True]
    losses = team_games[team_games["team_won"] == False]
    
    # Quality wins: wins vs teams with winning records
    wins_vs_winning = 0
    wins_vs_power5 = 0
    wins_vs_top25 = 0
    notable_wins = 0  # Wins vs teams with 8+ wins
    
    for _, game in wins.iterrows():
        opp = game["opponent"]
        
        # Check if opponent is Power 5
        if game.get("opp_conference") in POWER_5_CONFERENCES:
            wins_vs_power5 += 1
        
        # Check opponent's record
        if team_records is not None:
            opp_record = team_records[
                (team_records["team"] == opp) &
                (team_records["season"] == season) &
                (team_records["as_of_week"] <= game["week"])
            ]
            if not opp_record.empty:
                opp_wins = opp_record.iloc[-1]["wins"]
                opp_games = opp_record.iloc[-1]["games_played"]
                opp_win_pct = opp_wins / opp_games if opp_games > 0 else 0.0
                
                if opp_win_pct > 0.5:
                    wins_vs_winning += 1
                if opp_wins >= 8:
                    notable_wins += 1
        
        # Check if opponent was in previous week's Top 25
        if previous_rankings is not None:
            prev_week = week - 1 if week > 1 else week
            opp_ranked = previous_rankings[
                (previous_rankings["team_id"] == opp) &
                (previous_rankings["season"] == season) &
                (previous_rankings["week"] == prev_week)
            ]
            if not opp_ranked.empty:
                wins_vs_top25 += 1
    
    # Bad losses: losses to sub-.500 teams
    bad_losses = 0
    losses_vs_top10 = 0
    
    for _, game in losses.iterrows():
        opp = game["opponent"]
        
        # Check opponent's record
        if team_records is not None:
            opp_record = team_records[
                (team_records["team"] == opp) &
                (team_records["season"] == season) &
                (team_records["as_of_week"] <= game["week"])
            ]
            if not opp_record.empty:
                opp_wins = opp_record.iloc[-1]["wins"]
                opp_games = opp_record.iloc[-1]["games_played"]
                opp_win_pct = opp_wins / opp_games if opp_games > 0 else 0.0
                
                if opp_win_pct < 0.5:
                    bad_losses += 1
        
        # Check if opponent was in Top 10 (less penalized)
        if previous_rankings is not None:
            prev_week = week - 1 if week > 1 else week
            opp_ranked = previous_rankings[
                (previous_rankings["team_id"] == opp) &
                (previous_rankings["season"] == season) &
                (previous_rankings["week"] == prev_week) &
                (previous_rankings["rank"] <= 10)
            ]
            if not opp_ranked.empty:
                losses_vs_top10 += 1
    
    return {
        "wins_vs_winning_teams": float(wins_vs_winning),
        "wins_vs_power5": float(wins_vs_power5),
        "wins_vs_top25": float(wins_vs_top25),
        "notable_wins": float(notable_wins),
        "bad_losses": float(bad_losses),
        "losses_vs_top10": float(losses_vs_top10)
    }


def compute_record_strength(
    games_df: pd.DataFrame,
    team: str,
    season: int,
    week: int,
    team_records: Optional[pd.DataFrame] = None,
    previous_rankings: Optional[pd.DataFrame] = None
) -> Dict[str, float]:
    """
    Compute enhanced record strength metric (2025 committee enhancement).
    
    This metric rewards teams for beating high-quality opponents and minimizes
    penalty for losing to very strong teams, while imposing greater penalty
    for losing to lower-quality opponents.
    
    Args:
        games_df: Processed games DataFrame
        team: Team name
        season: Season year
        week: Week number (cutoff)
        team_records: Optional pre-computed team records
        previous_rankings: Optional previous week's rankings for Top 25 wins
        
    Returns:
        Dictionary with record strength features
    """
    # Get team's wins and losses
    team_games = games_df[
        (games_df["team"] == team) &
        (games_df["season"] == season) &
        (games_df["week"] <= week) &
        (games_df["team_won"].notna())
    ]
    
    wins = team_games[team_games["team_won"] == True]
    losses = team_games[team_games["team_won"] == False]
    
    # Record strength score (weighted by opponent quality)
    record_strength_score = 0.0
    
    # Weight wins by opponent quality
    # Top 10 win = +3, Top 25 win = +2, winning team = +1, other = +0.5
    for _, game in wins.iterrows():
        opp = game["opponent"]
        win_value = 0.5  # Base value for any win
        
        # Check if opponent was in Top 10
        if previous_rankings is not None:
            prev_week = week - 1 if week > 1 else week
            opp_ranked = previous_rankings[
                (previous_rankings["team_id"] == opp) &
                (previous_rankings["season"] == season) &
                (previous_rankings["week"] == prev_week)
            ]
            if not opp_ranked.empty:
                opp_rank = opp_ranked.iloc[0]["rank"]
                if opp_rank <= 10:
                    win_value = 3.0  # Top 10 win
                elif opp_rank <= 25:
                    win_value = 2.0  # Top 25 win
        else:
            # Fallback: check opponent's record
            if team_records is not None:
                opp_record = team_records[
                    (team_records["team"] == opp) &
                    (team_records["season"] == season) &
                    (team_records["as_of_week"] <= game["week"])
                ]
                if not opp_record.empty:
                    opp_win_pct = opp_record.iloc[-1]["win_pct"]
                    if opp_win_pct > 0.5:
                        win_value = 1.0  # Winning team
        
        record_strength_score += win_value
    
    # Weight losses by opponent quality
    # Top 10 loss = -0.5 (minimal penalty), sub-.500 loss = -3 (major penalty)
    # Other losses = -1 (standard penalty)
    for _, game in losses.iterrows():
        opp = game["opponent"]
        loss_value = -1.0  # Standard penalty for loss
        
        # Check if opponent was in Top 10 (minimal penalty)
        if previous_rankings is not None:
            prev_week = week - 1 if week > 1 else week
            opp_ranked = previous_rankings[
                (previous_rankings["team_id"] == opp) &
                (previous_rankings["season"] == season) &
                (previous_rankings["week"] == prev_week) &
                (previous_rankings["rank"] <= 10)
            ]
            if not opp_ranked.empty:
                loss_value = -0.5  # Minimal penalty for Top 10 loss
            else:
                # Check if bad loss (sub-.500)
                if team_records is not None:
                    opp_record = team_records[
                        (team_records["team"] == opp) &
                        (team_records["season"] == season) &
                        (team_records["as_of_week"] <= game["week"])
                    ]
                    if not opp_record.empty:
                        opp_win_pct = opp_record.iloc[-1]["win_pct"]
                        if opp_win_pct < 0.5:
                            loss_value = -3.0  # Major penalty for bad loss
        else:
            # Fallback: check opponent's record
            if team_records is not None:
                opp_record = team_records[
                    (team_records["team"] == opp) &
                    (team_records["season"] == season) &
                    (team_records["as_of_week"] <= game["week"])
                ]
                if not opp_record.empty:
                    opp_win_pct = opp_record.iloc[-1]["win_pct"]
                    if opp_win_pct < 0.5:
                        loss_value = -3.0  # Major penalty for bad loss
                    elif opp_win_pct > 0.7:  # Very strong opponent
                        loss_value = -0.5  # Minimal penalty
        
        record_strength_score += loss_value
    
    return {
        "record_strength_score": float(record_strength_score),
        "record_strength_per_game": float(record_strength_score / len(team_games)) if len(team_games) > 0 else 0.0
    }


def compute_conference_features(
    teams_df: pd.DataFrame,
    team: str,
    season: int,
    champions_df: Optional[pd.DataFrame] = None,
    is_final_week: bool = False
) -> Dict[str, any]:
    """
    Compute conference-related features.
    
    Args:
        teams_df: Processed teams DataFrame
        team: Team name
        season: Season year
        champions_df: Optional conference champions DataFrame
        is_final_week: Whether this is the final ranking (championship week)
        
    Returns:
        Dictionary with conference features
    """
    # Get team's conference
    team_info = teams_df[
        (teams_df["team_id"] == team) &
        (teams_df["season"] == season)
    ]
    
    if team_info.empty:
        # Try without season filter
        team_info = teams_df[teams_df["team_id"] == team]
    
    conference = team_info["conference"].iloc[0] if not team_info.empty and "conference" in team_info.columns else None
    is_power5 = conference in POWER_5_CONFERENCES if conference else False
    
    # Check if conference champion
    is_champion = False
    if champions_df is not None and is_final_week:
        champ_check = champions_df[
            (champions_df["season"] == season) &
            (champions_df["champion_team_id"] == team)
        ]
        is_champion = not champ_check.empty
    
    return {
        "conference": conference if conference else "Unknown",
        "is_power5": bool(is_power5),
        "is_conference_champion": bool(is_champion)
    }


def compute_momentum_features(
    games_df: pd.DataFrame,
    team: str,
    season: int,
    week: int
) -> Dict[str, float]:
    """
    Compute momentum and recency features.
    
    Args:
        games_df: Processed games DataFrame
        team: Team name
        season: Season year
        week: Week number (cutoff)
        
    Returns:
        Dictionary with momentum features
    """
    # Get team's games, sorted by week
    team_games = games_df[
        (games_df["team"] == team) &
        (games_df["season"] == season) &
        (games_df["week"] <= week) &
        (games_df["team_won"].notna())
    ].sort_values("week")
    
    if team_games.empty:
        return {
            "current_win_streak": 0.0,
            "last_game_result": 0.0,  # 0 = loss, 1 = win
            "last_game_opponent_quality": 0.0
        }
    
    # Current win streak (count backwards from most recent)
    win_streak = 0
    for _, game in team_games.iloc[::-1].iterrows():
        if game["team_won"]:
            win_streak += 1
        else:
            break
    
    # Last game result
    last_game = team_games.iloc[-1]
    last_result = 1.0 if last_game["team_won"] else 0.0
    
    # Last game opponent quality (simplified: Power 5 = 1, else 0.5)
    last_opp_quality = 0.5
    if last_game.get("opp_conference") in POWER_5_CONFERENCES:
        last_opp_quality = 1.0
    
    return {
        "current_win_streak": float(win_streak),
        "last_game_result": last_result,
        "last_game_opponent_quality": last_opp_quality
    }


def compute_elo_rating(
    games_df: pd.DataFrame,
    team: str,
    season: int,
    week: int,
    initial_elo: float = 1500.0,
    k_factor: float = 32.0
) -> float:
    """
    Compute Elo rating for a team as of a specific week.
    
    Args:
        games_df: Processed games DataFrame
        team: Team name
        season: Season year
        week: Week number (cutoff)
        initial_elo: Starting Elo rating
        k_factor: K-factor for Elo updates
        
    Returns:
        Elo rating as float
    """
    # Get team's games in order
    team_games = games_df[
        (games_df["team"] == team) &
        (games_df["season"] == season) &
        (games_df["week"] <= week) &
        (games_df["team_won"].notna())
    ].sort_values("week")
    
    if team_games.empty:
        return initial_elo
    
    # Simple Elo calculation (would need opponent Elo for full accuracy)
    # For now, use a simplified version
    elo = initial_elo
    
    for _, game in team_games.iterrows():
        # Simplified: win = +k, loss = -k (would need opponent Elo for proper calculation)
        if game["team_won"]:
            elo += k_factor * 0.5  # Simplified update
        else:
            elo -= k_factor * 0.5
    
    return float(elo)


def compute_head_to_head(
    games_df: pd.DataFrame,
    team: str,
    season: int,
    week: int,
    previous_rankings: Optional[pd.DataFrame] = None
) -> Dict[str, float]:
    """
    Compute head-to-head features.
    
    Tracks direct wins over other ranked/contending teams.
    This is a key tiebreaker when teams are comparable.
    
    Args:
        games_df: Processed games DataFrame
        team: Team name
        season: Season year
        week: Week number (cutoff)
        previous_rankings: Optional previous week's rankings
        all_teams: Optional set of all teams (for finding ranked opponents)
        
    Returns:
        Dictionary with head-to-head features
    """
    # Get team's wins
    team_games = games_df[
        (games_df["team"] == team) &
        (games_df["season"] == season) &
        (games_df["week"] <= week) &
        (games_df["team_won"] == True)
    ]
    
    head_to_head_wins_vs_ranked = 0
    head_to_head_wins_vs_top10 = 0
    head_to_head_wins_vs_top25 = 0
    
    if previous_rankings is not None:
        prev_week = week - 1 if week > 1 else week
        ranked_teams = set(previous_rankings[
            (previous_rankings["season"] == season) &
            (previous_rankings["week"] == prev_week)
        ]["team_id"].values)
        
        top10_teams = set(previous_rankings[
            (previous_rankings["season"] == season) &
            (previous_rankings["week"] == prev_week) &
            (previous_rankings["rank"] <= 10)
        ]["team_id"].values)
        
        top25_teams = set(previous_rankings[
            (previous_rankings["season"] == season) &
            (previous_rankings["week"] == prev_week) &
            (previous_rankings["rank"] <= 25)
        ]["team_id"].values)
        
        for _, game in team_games.iterrows():
            opp = game["opponent"]
            if opp in top10_teams:
                head_to_head_wins_vs_top10 += 1
                head_to_head_wins_vs_top25 += 1
                head_to_head_wins_vs_ranked += 1
            elif opp in top25_teams:
                head_to_head_wins_vs_top25 += 1
                head_to_head_wins_vs_ranked += 1
            elif opp in ranked_teams:
                head_to_head_wins_vs_ranked += 1
    
    return {
        "head_to_head_wins_vs_ranked": float(head_to_head_wins_vs_ranked),
        "head_to_head_wins_vs_top10": float(head_to_head_wins_vs_top10),
        "head_to_head_wins_vs_top25": float(head_to_head_wins_vs_top25)
    }


def compute_common_opponents(
    games_df: pd.DataFrame,
    team: str,
    season: int,
    week: int,
    comparison_teams: Optional[List[str]] = None,
    team_records: Optional[pd.DataFrame] = None
) -> Dict[str, float]:
    """
    Compute common opponents features.
    
    This is computationally expensive (O(n²) comparisons), so we'll
    compute a simplified version that looks at performance vs common opponents
    among top teams.
    
    Args:
        games_df: Processed games DataFrame
        team: Team name
        season: Season year
        week: Week number (cutoff)
        comparison_teams: Optional list of teams to compare against (e.g., top 25)
        team_records: Optional pre-computed team records
        
    Returns:
        Dictionary with common opponent features
    """
    # Get team's opponents
    team_games = games_df[
        (games_df["team"] == team) &
        (games_df["season"] == season) &
        (games_df["week"] <= week) &
        (games_df["team_won"].notna())
    ]
    
    team_opponents = set(team_games["opponent"].unique())
    
    if not comparison_teams or len(team_opponents) == 0:
        return {
            "common_opponents_count": 0.0,
            "common_opponents_win_pct": 0.0,
            "common_opponents_avg_margin": 0.0
        }
    
    # Find common opponents with comparison teams
    common_opponents = set()
    common_opponent_results = []
    
    for comp_team in comparison_teams[:25]:  # Limit to top 25 for performance
        if comp_team == team:
            continue
        
        comp_games = games_df[
            (games_df["team"] == comp_team) &
            (games_df["season"] == season) &
            (games_df["week"] <= week)
        ]
        comp_opponents = set(comp_games["opponent"].unique())
        
        common = team_opponents & comp_opponents
        common_opponents.update(common)
    
    # Calculate performance vs common opponents
    if common_opponents:
        common_games = team_games[team_games["opponent"].isin(common_opponents)]
        if not common_games.empty:
            wins_vs_common = common_games["team_won"].sum()
            common_win_pct = wins_vs_common / len(common_games) if len(common_games) > 0 else 0.0
            
            # Average margin vs common opponents (if scores available)
            margins = []
            for _, game in common_games.iterrows():
                if pd.notna(game.get("team_score")) and pd.notna(game.get("opp_score")):
                    margin = game["team_score"] - game["opp_score"]
                    margins.append(margin)
            
            avg_margin = float(np.mean(margins)) if margins else 0.0
            
            return {
                "common_opponents_count": float(len(common_opponents)),
                "common_opponents_win_pct": common_win_pct,
                "common_opponents_avg_margin": avg_margin
            }
    
    return {
        "common_opponents_count": 0.0,
        "common_opponents_win_pct": 0.0,
        "common_opponents_avg_margin": 0.0
    }


def compute_game_control(
    games_df: pd.DataFrame,
    team: str,
    season: int,
    week: int
) -> Dict[str, float]:
    """
    Compute subtle game control/dominance metrics.
    
    Committee mentions "game control" but explicitly avoids using margin of victory.
    This creates subtle metrics that hint at dominance without directly using MOV.
    
    Args:
        games_df: Processed games DataFrame
        team: Team name
        season: Season year
        week: Week number (cutoff)
        
    Returns:
        Dictionary with game control features
    """
    team_games = games_df[
        (games_df["team"] == team) &
        (games_df["season"] == season) &
        (games_df["week"] <= week) &
        (games_df["team_won"].notna()) &
        (games_df["team_score"].notna()) &
        (games_df["opp_score"].notna())
    ]
    
    if team_games.empty:
        return {
            "games_won_by_multiple_scores": 0.0,
            "games_never_trailing": 0.0,
            "dominant_wins_pct": 0.0
        }
    
    wins = team_games[team_games["team_won"] == True]
    
    # Games won by 2+ scores (14+ points)
    dominant_wins = 0
    for _, game in wins.iterrows():
        margin = game["team_score"] - game["opp_score"]
        if margin >= 14:  # 2+ scores
            dominant_wins += 1
    
    # Games never trailing (simplified: won by leading at half or won wire-to-wire)
    # Since we don't have play-by-play, we'll use a proxy: games won by 7+ points
    # where team scored first (we can't determine this, so we'll skip this metric)
    # Instead, use: games where final margin was comfortable (7+ points)
    comfortable_wins = 0
    for _, game in wins.iterrows():
        margin = game["team_score"] - game["opp_score"]
        if margin >= 7:
            comfortable_wins += 1
    
    dominant_wins_pct = dominant_wins / len(wins) if len(wins) > 0 else 0.0
    
    return {
        "games_won_by_multiple_scores": float(dominant_wins),
        "games_never_trailing": float(comfortable_wins),  # Proxy metric
        "dominant_wins_pct": dominant_wins_pct
    }


def compute_statistical_features(
    games_df: pd.DataFrame,
    team: str,
    season: int,
    week: int
) -> Dict[str, float]:
    """
    Compute basic statistical features (points, margins).
    
    Note: Committee explicitly avoids using margin of victory as primary factor,
    but we include it as a subtle feature.
    
    Args:
        games_df: Processed games DataFrame
        team: Team name
        season: Season year
        week: Week number (cutoff)
        
    Returns:
        Dictionary with statistical features
    """
    # Get team's games
    team_games = games_df[
        (games_df["team"] == team) &
        (games_df["season"] == season) &
        (games_df["week"] <= week) &
        (games_df["team_score"].notna()) &
        (games_df["opp_score"].notna())
    ]
    
    if team_games.empty:
        return {
            "points_per_game": 0.0,
            "points_allowed_per_game": 0.0,
            "point_differential": 0.0
        }
    
    points_scored = team_games["team_score"].sum()
    points_allowed = team_games["opp_score"].sum()
    games_played = len(team_games)
    
    return {
        "points_per_game": float(points_scored / games_played),
        "points_allowed_per_game": float(points_allowed / games_played),
        "point_differential": float((points_scored - points_allowed) / games_played)
    }

