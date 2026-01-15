# Next.js Frontend

Modern React frontend for the CFP Predictor application.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set environment variables:
```bash
cp .env.local.example .env.local
# Edit .env.local and set NEXT_PUBLIC_API_URL
```

## Running

```bash
# Development
npm run dev

# Production build
npm run build
npm start
```

The app will be available at `http://localhost:3000`.

## Features

- Interactive bracket visualization
- Rankings table
- Game outcome selector
- "The Bubble" component showing teams on the cusp

## Environment Variables

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: `http://localhost:8000`)
