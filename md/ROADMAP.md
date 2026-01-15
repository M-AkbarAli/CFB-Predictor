# Roadmap (Next Steps)

This project already demonstrates an end-to-end ML workflow (data → features → model → simulation → UI). The highest-leverage next steps are productizing the simulator and upgrading the UI/UX beyond Streamlit’s styling limits.

## 1) Product + UX (Highest Impact)

**Goal**: Make the simulator feel like a polished consumer app: fast, visually strong, and easy to share.

- **Define the “core loop”**: pick outcomes → instantly see ranking + bracket deltas → understand *why* changes happened.
- **Add explanation UX**: for a selected team, show the top drivers (feature deltas, “resume cards”, comparisons).
- **Add shareable scenarios**: encode outcomes into a URL or save scenarios server-side and generate a link.
- **Add “game impact” ranking**: automatically rank remaining games by how much they swing the playoff field.

### Frontend Options (If Streamlit Can’t Match Your Vision)

**Option A: Keep Python, replace UI**
- **Frontend**: Next.js (React) + Tailwind CSS + shadcn/ui (or Mantine/Chakra)
- **Charts**: Plotly.js / Recharts / Visx
- **Hosting**: Vercel (frontend)
- **Backend**: FastAPI (Python) serving predictions + scenario evaluation
- **Hosting**: Render/Fly.io (backend)

**Option B: Full Python but more design control**
- Plotly Dash (more app-like layout control than Streamlit)
- Panel / Bokeh server (more customizable, steeper learning curve)

**Option C: Streamlit “max styling” (fastest path)**
- Streamlit themes + CSS injection + `streamlit-elements`/custom components
- Good for iteration, but still limited for “pixel-perfect” design

## 2) Backend/API Layer (Unlocks Better UI + Sharing)

If you move to a modern frontend, introduce an API boundary:

- **FastAPI** endpoints:
  - `GET /health`
  - `POST /simulate` (game_outcomes, season, week) → rankings + bracket + explanation payload
  - `POST /scenario` (save) / `GET /scenario/{id}` (load/share)
- **Pydantic** schemas for request/response stability
- **Caching**:
  - In-memory (LRU) for local dev
  - Redis if you deploy and want shared caching

## 3) Model + Evaluation Improvements (Keep the “89%” Metric, Improve Trust)

- **Fix evaluation to match the problem**:
  - Evaluate per-week Top-N overlap and per-team rank error *within a week* (current mean rank error is likely not meaningful as implemented).
- **Train to optimize ranking**:
  - Consider pairwise ranking loss (e.g., LightGBM ranker / XGBoost rank objectives) instead of pure regression.
- **Calibration & robustness**:
  - Quantify uncertainty (bootstrap scenarios, prediction intervals) so the UI can show “confidence”.
- **Interpretability**:
  - SHAP values for “why this team is here” explanations (works well for tree models).

## 4) Data Pipeline + Reliability (Make Updates Easy)

- **Incremental updates**: fetch only new games/rankings weekly instead of rebuilding everything.
- **Storage**:
  - Start with Parquet files in `data/processed/`
  - Graduate to Postgres if you want multi-user + scenario sharing
- **Reproducibility**:
  - Add a single command to rebuild artifacts (Makefile / task runner)
  - Track data/model versions (DVC or a lightweight “artifact manifest”)

## 5) Engineering Polish (Portfolio Signal)

- **CI**: GitHub Actions to run `pytest` on every PR
- **Formatting**: Ruff + Black (or Ruff-only) for consistent style
- **Packaging**: turn `src/` into an installable package (or use `uv`/Poetry)
- **Docker**: one Dockerfile for the API + model runtime; optional `docker-compose` with Redis/Postgres

## Suggested Milestone Plan

1. **Stabilize inference**: keep training/inference features aligned (including categorical encoding).
2. **Design a UI spec**: 2–3 screens, reusable components, interaction model.
3. **Add an API boundary**: FastAPI simulation endpoint + caching.
4. **Build the new frontend**: Next.js + Tailwind + charts + share links.
5. **Add explanations**: SHAP + “resume cards” + deltas vs baseline.

