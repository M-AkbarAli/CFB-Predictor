# Resume Notes (Draft Bullets + Keywords)

Use these as raw material to tailor 2–4 bullets depending on the role (ML, data, full-stack).

## Strong Resume Bullets (Pick 2–4)

- Built an end-to-end College Football Playoff ranking simulator: ingested historical rankings + game results, engineered committee-aligned “resume” features, trained gradient-boosted models, and shipped an interactive scenario UI.
- Integrated the CollegeFootballData (CFBD) API with local caching and a reproducible feature pipeline to generate team-week training samples across 10 seasons (2014–2023).
- Implemented a rules engine for the 12-team CFP format (auto-bids, seeding, bracket generation) and connected it to model-driven ranking projections.
- Engineered schedule- and resume-based signals (strength of schedule, quality wins/bad losses, head-to-head, common opponents, momentum, “record strength”) to mirror committee criteria and support explainable outputs.
- Trained and evaluated XGBoost/LightGBM models with temporal validation (train on earlier seasons, validate on later seasons) to reduce leakage and better reflect real-world forecasting.
- Built a “what-if” simulation engine that recomputes team features after hypothetical game outcomes and re-ranks teams in seconds for interactive exploration.

## Metrics (Use Carefully)

- Prefer phrasing like “Top-N overlap accuracy on held-out seasons” and include the exact definition (set overlap of Top N teams).
- The saved model bundle in `data/models/cfp_predictor.pkl` stores training/validation metrics in its metadata; metrics will change as you retrain with new features/seasons.

## Keywords (ATS-Friendly)

Python, pandas, NumPy, scikit-learn, XGBoost, LightGBM, feature engineering, temporal validation, ranking systems, simulation engine, API integration, caching, Streamlit, Plotly, unit testing (pytest), reproducible ML pipelines.

## How to Describe It in Interviews

- **Problem framing**: “Predict an ordinal ranking created by a committee using publicly available ‘resume’ evidence.”
- **Design choice**: “Used transparent, committee-aligned features over black-box approaches to keep outputs explainable.”
- **Product angle**: “Interactive scenario tool: users change outcomes and immediately see ranking/bracket deltas.”
- **Next step**: “Move beyond Streamlit into a FastAPI + modern frontend stack for design and shareable scenarios.”

