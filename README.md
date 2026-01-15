# College Football Playoff Predictor

A machine learning system that predicts College Football Playoff (CFP) committee rankings and enables "what-if" scenario simulations. The system uses historical committee rankings (2014-2023) to train a gradient boosting model that emulates committee decision-making.

## Project Status

Work-in-progress portfolio project focused on (1) an end-to-end ML pipeline and (2) an interactive scenario simulator. The current UI is a Streamlit app; see `ROADMAP.md` for options if you want a more design-forward frontend.

## Features

- **Historical Data Integration**: Fetches game results, rankings, and team metadata from the CollegeFootballData API
- **Resume-Based Features**: Computes features that mirror CFP committee criteria (strength of schedule, quality wins, conference championships, etc.)
- **ML Model**: Trained XGBoost/LightGBM model predicts committee rankings
- **Scenario Simulation**: Interactive tool to simulate game outcomes and see projected rankings
- **12-Team Playoff Support**: Implements the new 12-team playoff format rules (auto-bids, seeding)

## Documentation

- `PROJECT_SUMMARY.md`: architecture + how the pipeline fits together
- `RESEARCH.md`: research + modeling rationale
- `ENHANCEMENTS_SUMMARY.md`: implemented feature upgrades
- `ROADMAP.md`: next steps + suggested technologies
- `RESUME_NOTES.md`: resume-ready bullet ideas + keywords

## Project Structure

```
CFB/
├── data/
│   ├── raw/              # Raw API responses
│   ├── processed/        # Cleaned, structured data
│   └── models/           # Saved trained models
├── src/
│   ├── data/             # Data fetching and processing
│   ├── features/         # Feature engineering
│   ├── model/            # ML model training and prediction
│   ├── simulation/       # Scenario simulation engine
│   └── app/              # Streamlit web application
├── tests/                # Unit tests
├── notebooks/            # Jupyter notebooks for exploration
├── requirements.txt      # Python dependencies
└── README.md
```

## Setup

### Prerequisites

- Python 3.8+ (use `python3` on macOS)
- CFBD API key (get one at [collegefootballdata.com](https://collegefootballdata.com))
- **macOS users**: OpenMP runtime (required for XGBoost)
  ```bash
  brew install libomp
  ```

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd CFB
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. **macOS users**: Install OpenMP runtime (if not already installed):
```bash
brew install libomp
```

5. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your CFBD_API_KEY
```

**Note**: If XGBoost fails to import on macOS, the training script will automatically fall back to LightGBM, which doesn't require OpenMP.

## Usage

### Training the Model

First, train the model on historical data:

```bash
python3 -m src.model.train
```

This will:
- Fetch historical data (2014-2023)
- Compute features for all team-week combinations
- Train an XGBoost model with temporal cross-validation
- Save the model to `data/models/cfp_predictor.pkl`

### Running the Web Application

#### Option 1: Next.js Frontend (Recommended)

1. **Start the FastAPI backend:**
   ```bash
   cd api
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000
   ```

2. **Start the Next.js frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Open `http://localhost:3000` in your browser.

The frontend provides:
- Interactive bracket visualization
- Rankings table with team information
- Game outcome selector for simulations
- "The Bubble" showing teams on the cusp

**Environment Variables:**
- Frontend: Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` (defaults to `http://localhost:8000`)
- Backend: Configure CORS origins in `api/main.py` or via environment variables

#### Option 2: Streamlit App (Legacy)

Launch the Streamlit app:

```bash
streamlit run src/app/main.py
```

The app will open in your browser where you can:
- Select outcomes for remaining games
- Choose simulation mode: Final Rankings or Weekly Rankings
- View projected CFP rankings
- See the projected 12-team playoff bracket
- Analyze team resumes and compare teams
- View feature importance to understand model decisions

### Using the API Programmatically

```python
from src.simulation.engine import SimulationEngine
from src.data.fetcher import CFBDFetcher
from src.data.processor import DataProcessor

# Load data
fetcher = CFBDFetcher()
processor = DataProcessor()

games = fetcher.fetch_games(2024)
games_df = processor.process_games(games)

# Run simulation
engine = SimulationEngine()
results = engine.simulate_scenario(
    base_games_df=games_df,
    base_teams_df=teams_df,
    game_outcomes={"game_123": "Alabama"},
    target_week=15,
    season=2024
)
```

## Methodology

### Feature Engineering

The model uses resume-based features that align with CFP committee criteria:

- **Record**: Wins, losses, win percentage, conference record
- **Strength of Schedule**: Opponent average win percentage, SOS rank, weighted SOS, SOS of SOS
- **Quality Wins**: Wins vs winning teams, Power 5 teams, Top 25 teams
- **Bad Losses**: Losses to sub-.500 teams
- **Record Strength** (2025 Enhancement): Weighted metric rewarding quality wins and minimizing penalty for strong losses
- **Head-to-Head**: Explicit tracking of wins over ranked teams with post-processing rule
- **Common Opponents**: Performance vs common opponents with top teams
- **Game Control**: Subtle dominance metrics (games won by multiple scores)
- **Conference**: Power 5 status, conference championship
- **Momentum**: Current win streak, recent game results
- **Statistics**: Points per game, point differential (used cautiously)
- **Elo Rating**: Background feature for tie-breaking

### Model Training

- **Algorithm**: XGBoost gradient boosting regressor
- **Target**: Ranking score (lower = better rank)
- **Training Split**: Temporal (2014-2020 train, 2021-2023 validate)
- **Evaluation Metrics**: Kendall's tau, Spearman correlation, top-N accuracy

### Playoff Selection Rules (12-Team Format)

1. Top 5 conference champions receive auto-bids
2. Remaining 7 spots go to highest-ranked teams
3. Seeds 1-4: Top 4 conference champions (get first-round byes)
4. Seeds 5-12: Remaining teams sorted by rank
5. First round: 12@5, 11@6, 10@7, 9@8

## Testing

Run unit tests:

```bash
python3 -m pytest tests/
```

## Limitations

- Model is trained on 4-team era data (2014-2023); committee behavior may evolve in 12-team era
- Does not account for injuries or player availability (committee explicitly considers this)
- Conference championship determination is simplified
- Some edge cases (ties, complex division scenarios) may not be fully handled
- Common opponents analysis is simplified (only compares vs top 25 teams for performance)
- Head-to-head post-processing uses a simple threshold; may not catch all cases

## Data Sources

- **CollegeFootballData API**: Game results, rankings, team metadata
- **CFP Committee Rankings**: Historical weekly rankings (2014-2023)

## License

No license selected yet (WIP).

## Contributing

Open an issue/PR with a clear description and reproduction steps (WIP).

## Acknowledgments

- CollegeFootballData for providing the API
- FiveThirtyEight for methodology insights on CFP prediction
