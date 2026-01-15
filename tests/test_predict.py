"""
Unit tests for prediction feature alignment.
"""

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder

from src.model.predict import predict_rankings


def test_predict_rankings_applies_conference_encoding():
    le = LabelEncoder().fit(["SEC", "Big Ten"])

    X_train = pd.DataFrame(
        {
            "win_pct": [1.0, 0.5, 0.8],
            "conference_encoded": le.transform(["SEC", "Big Ten", "SEC"]),
        }
    )
    y_train = [1.0, 10.0, 3.0]

    model = LinearRegression().fit(X_train, y_train)
    model.feature_names_ = list(X_train.columns)

    features_df = pd.DataFrame(
        {
            "team": ["A", "B", "C"],
            "win_pct": [0.9, 0.6, 0.7],
            "conference": ["SEC", "Big Ten", "Unknown Conf"],
        }
    )

    results = predict_rankings(
        features_df,
        model={"model": model, "encoders": {"conference": le}, "metadata": {}},
    )

    assert list(results.columns) == ["team", "predicted_score", "predicted_rank"]
    assert len(results) == 3
    assert results["predicted_rank"].min() == 1
    assert results["predicted_rank"].max() == 3

