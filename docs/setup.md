# Environment Setup Guide

## Prerequisites

- **Python 3.11+** 
- **Node.js 18+**
- **npm 9+**
- **D-Wave Leap Account** (optional, for quantum hardware)

## Backend Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env and add your settings
```

**Required Environment Variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `DWAVE_API_TOKEN` | D-Wave API token (optional) | None (mock mode) |
| `API_HOST` | API host address | `0.0.0.0` |
| `API_PORT` | API port | `8000` |

### 4. Run Development Server

```bash
python -m uvicorn app.main:app --reload --port 8000
```

API available at: http://localhost:8000
API docs at: http://localhost:8000/docs

---

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure API URL

Edit `src/lib/config.ts`:

```typescript
export const API_CONFIG = {
  baseUrl: 'http://localhost:8000',  // Change if backend on different host
  // ...
};
```

### 3. Run Development Server

```bash
npm run dev
```

Frontend available at: http://localhost:5173

---

## D-Wave Leap Setup (Optional)

### 1. Create Leap Account

1. Go to https://cloud.dwavesys.com/leap/signup/
2. Sign up for a free account
3. You get free QPU time for testing

### 2. Get API Token

1. Log in to D-Wave Leap dashboard
2. Go to **API Tokens** section
3. Generate or copy your token

### 3. Configure Token

Add to `backend/.env`:

```
DWAVE_API_TOKEN=DEV-your-token-here
```

### Mock Mode

Without a token, the system runs in **mock mode**:
- Uses simulated quantum annealing
- Results are approximate but functional
- Good for testing UI and workflows

---

## Docker Setup

### Quick Start

```bash
# Build and run all services
docker-compose up --build

# Run in background
docker-compose up -d
```

### Environment Variables

Set in `docker-compose.yml` or `.env`:

```yaml
environment:
  - DWAVE_API_TOKEN=${DWAVE_API_TOKEN}
```

---

## Running Tests

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

### Run Experiments

```bash
cd backend
python experiments.py --nodes 8 10 12 --runs 5
```

Results saved to `results/experiment_results_TIMESTAMP.csv`

---

## Troubleshooting

### "uvicorn not found"

```bash
python -m uvicorn app.main:app --reload
```

### CORS errors

Check `CORS_ORIGINS` in backend `.env` includes your frontend URL.

### D-Wave connection issues

1. Verify token is correct
2. Check internet connection
3. Try mock mode first

### Frontend build errors

```bash
rm -rf node_modules
npm install
npm run dev
```
