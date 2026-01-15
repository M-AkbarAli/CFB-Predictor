# FastAPI Backend

FastAPI backend that wraps the Python simulation logic and exposes it as REST APIs.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure the model is trained and available at `data/models/cfp_predictor.pkl`

3. Set environment variables (optional):
```bash
# CORS origins (comma-separated)
export CORS_ORIGINS="http://localhost:3000,https://your-vercel-app.vercel.app"
```

## Running

```bash
# Development
uvicorn api.main:app --reload --port 8000

# Production
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/season/{year}/data` - Get season data (games, teams, rankings, champions)
- `POST /api/simulate` - Run simulation with game outcomes
- `GET /api/season/{year}/week/{week}/rankings` - Get weekly rankings

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
