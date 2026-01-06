"""
Rankings display component for Streamlit app.
"""

import pandas as pd
import streamlit as st
from typing import Optional


def display_rankings(
    rankings_df: pd.DataFrame,
    title: str = "CFP Rankings",
    show_features: bool = False,
    highlight_playoff: bool = False,
    playoff_teams: Optional[set] = None,
    baseline_rankings: Optional[pd.DataFrame] = None
):
    """
    Display CFP rankings in a formatted table.
    
    Args:
        rankings_df: DataFrame with rankings (team, predicted_rank, predicted_score)
        title: Title for the display
        show_features: Whether to show additional feature columns
        highlight_playoff: Whether to highlight playoff teams
        playoff_teams: Optional set of playoff team names
        baseline_rankings: Optional baseline for comparison
    """
    st.subheader(title)
    
    if rankings_df.empty:
        st.warning("No rankings available.")
        return
    
    # Prepare display DataFrame
    display_df = rankings_df.copy()
    
    # Ensure sorted by rank
    if "predicted_rank" in display_df.columns:
        display_df = display_df.sort_values("predicted_rank").reset_index(drop=True)
        rank_col = "predicted_rank"
    elif "rank" in display_df.columns:
        display_df = display_df.sort_values("rank").reset_index(drop=True)
        rank_col = "rank"
    else:
        st.error("No rank column found in rankings DataFrame.")
        return
    
    # Select columns to display
    display_cols = ["team", rank_col]
    
    if "predicted_score" in display_df.columns:
        display_cols.append("predicted_score")
    
    if show_features:
        # Add any feature columns if present
        feature_cols = ["wins", "losses", "sos_rank", "wins_vs_winning_teams"]
        for col in feature_cols:
            if col in display_df.columns:
                display_cols.append(col)
    
    display_df = display_df[display_cols].head(25)  # Top 25
    
    # Add comparison if baseline provided
    if baseline_rankings is not None:
        baseline_dict = dict(zip(
            baseline_rankings["team"],
            baseline_rankings.get("predicted_rank", baseline_rankings.get("rank", []))
        ))
        
        display_df["baseline_rank"] = display_df["team"].map(baseline_dict)
        display_df["rank_change"] = (
            display_df["baseline_rank"] - display_df[rank_col]
        ).fillna(0)
        
        # Format rank change
        def format_change(change):
            if pd.isna(change) or change == 0:
                return "—"
            elif change > 0:
                return f"↑{int(change)}"
            else:
                return f"↓{int(abs(change))}"
        
        display_df["change"] = display_df["rank_change"].apply(format_change)
        display_cols.extend(["baseline_rank", "change"])
    
    # Rename columns for display
    rename_map = {
        "team": "Team",
        "predicted_rank": "Rank",
        "rank": "Rank",
        "predicted_score": "CFP Score",
        "wins": "Wins",
        "losses": "Losses",
        "sos_rank": "SOS Rank",
        "wins_vs_winning_teams": "Quality Wins",
        "baseline_rank": "Prev Rank",
        "change": "Change"
    }
    
    display_df = display_df.rename(columns=rename_map)
    display_cols = [rename_map.get(col, col) for col in display_cols if col in display_df.columns]
    
    # Style the DataFrame
    styled_df = display_df[display_cols].copy()
    
    # Highlight playoff teams
    if highlight_playoff and playoff_teams:
        def highlight_row(row):
            if row["Team"] in playoff_teams:
                return ['background-color: #90EE90'] * len(row)
            return [''] * len(row)
        
        styled_df = styled_df.style.apply(highlight_row, axis=1)
    
    # Display
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Show summary stats
    if highlight_playoff and playoff_teams:
        st.caption(f"🟢 Highlighted: {len(playoff_teams)} playoff teams")


def display_rankings_comparison(
    baseline: pd.DataFrame,
    scenario: pd.DataFrame,
    title: str = "Rankings Comparison"
):
    """
    Display side-by-side comparison of baseline vs scenario rankings.
    
    Args:
        baseline: Baseline rankings DataFrame
        scenario: Scenario rankings DataFrame
        title: Title for display
    """
    st.subheader(title)
    
    # Merge on team
    comparison = pd.merge(
        baseline[["team", "predicted_rank"]].rename(columns={"predicted_rank": "baseline_rank"}),
        scenario[["team", "predicted_rank"]].rename(columns={"predicted_rank": "scenario_rank"}),
        on="team",
        how="outer"
    )
    
    comparison["rank_change"] = comparison["baseline_rank"] - comparison["scenario_rank"]
    comparison = comparison.sort_values("scenario_rank")
    
    # Format for display
    comparison_display = comparison[["team", "baseline_rank", "scenario_rank", "rank_change"]].copy()
    comparison_display.columns = ["Team", "Baseline Rank", "Scenario Rank", "Change"]
    
    st.dataframe(comparison_display, use_container_width=True, hide_index=True)


def display_team_resume(
    team: str,
    features_df: pd.DataFrame,
    title: str = "Team Resume"
):
    """
    Display detailed team resume with all features.
    
    Args:
        team: Team name
        features_df: DataFrame with team features
        title: Title for display
    """
    st.subheader(f"{title}: {team}")
    
    team_features = features_df[features_df["team"] == team]
    
    if team_features.empty:
        st.warning(f"No data found for {team}")
        return
    
    features = team_features.iloc[0]
    
    # Group features by category
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Record**")
        st.write(f"Wins: {features.get('wins', 'N/A')}")
        st.write(f"Losses: {features.get('losses', 'N/A')}")
        st.write(f"Win %: {features.get('win_pct', 0):.3f}")
        
        st.write("**Strength of Schedule**")
        st.write(f"SOS Score: {features.get('sos_score', 0):.3f}")
        st.write(f"Weighted SOS: {features.get('weighted_sos_score', 0):.3f}")
        st.write(f"SOS Rank: {features.get('sos_rank', 'N/A')}")
        
        st.write("**Quality Wins**")
        st.write(f"vs Winning Teams: {features.get('wins_vs_winning_teams', 0)}")
        st.write(f"vs Top 25: {features.get('wins_vs_top25', 0)}")
        st.write(f"vs Power 5: {features.get('wins_vs_power5', 0)}")
    
    with col2:
        st.write("**Record Strength**")
        st.write(f"Record Strength Score: {features.get('record_strength_score', 0):.2f}")
        st.write(f"Per Game: {features.get('record_strength_per_game', 0):.2f}")
        
        st.write("**Head-to-Head**")
        st.write(f"vs Ranked Teams: {features.get('head_to_head_wins_vs_ranked', 0)}")
        st.write(f"vs Top 10: {features.get('head_to_head_wins_vs_top10', 0)}")
        
        st.write("**Conference**")
        st.write(f"Conference: {features.get('conference', 'N/A')}")
        st.write(f"Power 5: {features.get('is_power5', False)}")
        st.write(f"Champion: {features.get('is_conference_champion', False)}")
        
        st.write("**Momentum**")
        st.write(f"Win Streak: {features.get('current_win_streak', 0)}")
        st.write(f"Last Game: {'Win' if features.get('last_game_result', 0) == 1 else 'Loss'}")


def display_team_comparison(
    team1: str,
    team2: str,
    features_df: pd.DataFrame,
    title: str = "Team Comparison"
):
    """
    Display side-by-side comparison of two teams' resumes.
    
    Args:
        team1: First team name
        team2: Second team name
        features_df: DataFrame with team features
        title: Title for display
    """
    st.subheader(f"{title}: {team1} vs {team2}")
    
    t1_features = features_df[features_df["team"] == team1]
    t2_features = features_df[features_df["team"] == team2]
    
    if t1_features.empty or t2_features.empty:
        st.warning("One or both teams not found in data")
        return
    
    t1 = t1_features.iloc[0]
    t2 = t2_features.iloc[0]
    
    # Create comparison DataFrame
    comparison_data = {
        "Feature": [
            "Record", "Wins", "Losses", "Win %",
            "SOS Score", "Weighted SOS", "SOS Rank",
            "Quality Wins", "Top 25 Wins", "Power 5 Wins",
            "Bad Losses", "Record Strength",
            "Head-to-Head vs Ranked", "Conference",
            "Win Streak"
        ],
        team1: [
            f"{t1.get('wins', 0)}-{t1.get('losses', 0)}",
            t1.get('wins', 0),
            t1.get('losses', 0),
            f"{t1.get('win_pct', 0):.3f}",
            f"{t1.get('sos_score', 0):.3f}",
            f"{t1.get('weighted_sos_score', 0):.3f}",
            t1.get('sos_rank', 'N/A'),
            t1.get('wins_vs_winning_teams', 0),
            t1.get('wins_vs_top25', 0),
            t1.get('wins_vs_power5', 0),
            t1.get('bad_losses', 0),
            f"{t1.get('record_strength_score', 0):.2f}",
            t1.get('head_to_head_wins_vs_ranked', 0),
            t1.get('conference', 'N/A'),
            t1.get('current_win_streak', 0)
        ],
        team2: [
            f"{t2.get('wins', 0)}-{t2.get('losses', 0)}",
            t2.get('wins', 0),
            t2.get('losses', 0),
            f"{t2.get('win_pct', 0):.3f}",
            f"{t2.get('sos_score', 0):.3f}",
            f"{t2.get('weighted_sos_score', 0):.3f}",
            t2.get('sos_rank', 'N/A'),
            t2.get('wins_vs_winning_teams', 0),
            t2.get('wins_vs_top25', 0),
            t2.get('wins_vs_power5', 0),
            t2.get('bad_losses', 0),
            f"{t2.get('record_strength_score', 0):.2f}",
            t2.get('head_to_head_wins_vs_ranked', 0),
            t2.get('conference', 'N/A'),
            t2.get('current_win_streak', 0)
        ]
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    # Highlight key differences
    st.write("**Key Differences:**")
    if t1.get('wins', 0) != t2.get('wins', 0):
        st.write(f"- {team1} has {abs(t1.get('wins', 0) - t2.get('wins', 0))} {'more' if t1.get('wins', 0) > t2.get('wins', 0) else 'fewer'} wins")
    if t1.get('record_strength_score', 0) != t2.get('record_strength_score', 0):
        diff = t1.get('record_strength_score', 0) - t2.get('record_strength_score', 0)
        st.write(f"- {team1} has {'higher' if diff > 0 else 'lower'} record strength ({abs(diff):.2f} difference)")
    if t1.get('weighted_sos_score', 0) != t2.get('weighted_sos_score', 0):
        diff = t1.get('weighted_sos_score', 0) - t2.get('weighted_sos_score', 0)
        st.write(f"- {team1} has {'tougher' if diff > 0 else 'easier'} weighted SOS ({abs(diff):.3f} difference)")


def display_feature_importance(
    model,
    feature_names: list,
    top_n: int = 15
):
    """
    Display feature importance from the trained model.
    
    Args:
        model: Trained model object
        feature_names: List of feature names
        top_n: Number of top features to show
    """
    st.subheader("Feature Importance")
    
    try:
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'get_booster'):
            # XGBoost model
            booster = model.get_booster()
            importances = booster.get_score(importance_type='gain')
            # Convert to array matching feature_names
            importances = [importances.get(fname, 0) for fname in feature_names]
        else:
            st.warning("Model does not support feature importance extraction")
            return
        
        # Create DataFrame
        importance_df = pd.DataFrame({
            "Feature": feature_names,
            "Importance": importances
        }).sort_values("Importance", ascending=False).head(top_n)
        
        st.dataframe(importance_df, use_container_width=True, hide_index=True)
        
        # Optional: bar chart
        try:
            import plotly.express as px
            fig = px.bar(
                importance_df,
                x="Importance",
                y="Feature",
                orientation='h',
                title="Top Feature Importances"
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        except:
            pass  # Plotly not available or error
        
    except Exception as e:
        st.warning(f"Could not extract feature importance: {e}")

