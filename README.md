# Quantum-Annealing Mixed-Priority Routing Framework

A quantum-classical hybrid routing optimization system that solves urban logistics problems with mixed-priority nodes using D-Wave quantum annealing.

## Features

- **Priority-Constrained Routing**: All priority nodes are visited before any normal nodes
- **Quantum Optimization**: Uses D-Wave LeapHybridSampler for QUBO-based route optimization
- **Classical Baseline**: Greedy nearest-neighbor algorithm for comparison
- **Traffic-Aware**: Edge weights adjusted by traffic multipliers
- **Full-Stack**: FastAPI backend + React/TypeScript frontend

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- D-Wave Ocean SDK
- NetworkX
- Pydantic

### Frontend
- React 19 + TypeScript
- Vite
- TailwindCSS
- React Flow (graph visualization)
- Recharts

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- D-Wave Leap account (for quantum solver)

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Set D-Wave API token
set DWAVE_API_TOKEN=your-token-here  # Windows

# Run server
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Run Both (Docker)
```bash
docker-compose up
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/solve` | POST | Run quantum or greedy solver |
| `/graphs` | GET | List available city graphs |
| `/health` | GET | Health check |

## Project Structure

```
├── backend/
│   ├── src/
│   │   ├── data_models.py
│   │   ├── qubo_builder.py
│   │   ├── d_wave_solver.py
│   │   ├── greedy_solver.py
│   │   └── metrics.py
│   ├── app/
│   │   └── main.py
│   └── tests/
├── frontend/
│   └── src/
├── data/
│   └── example_city.json
└── docs/
```

## License

MIT
