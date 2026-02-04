# Coding Conventions

**Analysis Date:** 2026-02-04

## Naming Patterns

**Files:**
- TypeScript/React components: PascalCase with `.tsx` extension. Examples: `SolverControls.tsx`, `MetricsTable.tsx`, `InteractiveMap.tsx`
- Hooks: `use` prefix with camelCase. Example: `useSolver.ts`, `useCityGraph()`
- Libraries/utilities: lowercase with extension. Examples: `api.ts`, `config.ts`, `types.ts`
- Python modules: snake_case. Examples: `data_models.py`, `greedy_solver.py`, `qaoa_solver.py`
- Python functions: snake_case. Examples: `greedy_solve()`, `build_qubo()`, `generate_random_city()`

**Functions:**
- TypeScript: camelCase. Examples: `useSolver()`, `solveRoute()`, `generateCity()`, `checkHealth()`
- React components: PascalCase (named exports as const). Example: `export const SolverControls: React.FC<Props> = ({...})`
- Python: snake_case. Examples: `euclidean_distance()`, `find_nearest()`, `get_weighted_distance()`

**Variables:**
- TypeScript: camelCase. Examples: `numNodes`, `selectedSolver`, `displayRoute`, `solverLoading`
- Python: snake_case. Examples: `priority_nodes`, `normal_nodes`, `solve_time_ms`, `total_distance`
- State management: camelCase in React. Examples: `quantumResult`, `greedyResult`, `loading`, `error`
- Acronyms preserved: `QAOA`, `QUBO`, `API`, `CORS`

**Types:**
- TypeScript interfaces: PascalCase, prefixed with component name or domain-specific name. Examples:
  - `SolverControlsProps`, `MetricsTableProps`
  - `SolverRequest`, `SolverResponse`, `CityGraph`, `QUBOParams`
  - `NodeType`, `TrafficLevel`, `SolverType`
- Python Pydantic models: PascalCase. Examples: `Node`, `Edge`, `CityGraph`, `TrafficMultipliers`
- Python Enums: UPPERCASE constants within Enum class. Example: `NodeType.PRIORITY`, `TrafficLevel.LOW`

## Code Style

**Formatting:**
- TypeScript: 2-space indentation (Vite default)
- Python: 4-space indentation (PEP 8)
- No trailing semicolons in TypeScript imports (modern ESM)
- Triple-quoted docstrings for Python modules and functions

**Linting:**
- TypeScript: ESLint with `@eslint/js`, `typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`
- Config: `frontend/eslint.config.js` using flat config format
- Rules enforced: React hooks rules, React refresh compatibility
- Python: No explicit linter config found, but code follows PEP 8 conventions

**TypeScript Configuration:**
- Target: ES2022
- Strict mode enabled: `"strict": true`
- JSX handling: `"jsx": "react-jsx"` (React 17+ fast refresh)
- Module resolution: `"moduleResolution": "bundler"`
- Enforce type safety: `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`
- Location: `frontend/tsconfig.app.json`

## Import Organization

**Order:**
1. External dependencies (React, libraries from node_modules)
2. Type imports from libraries (`import type { ... }`)
3. Internal utilities and helpers
4. Internal types (`import type { ... } from '...'`)
5. CSS/styles (last for CSS modules or global styles)

**Examples from codebase:**

TypeScript:
```typescript
import { useEffect, useState } from 'react';
import { InteractiveMap, SolverControls } from './components';
import { useSolver, useCityGraph } from './hooks/useSolver';
import type { SolverType, QUBOParams, CityGraph } from './lib/types';
import './App.css';
```

Python:
```python
from pydantic import BaseModel, Field
from enum import Enum
from typing import Literal

from .data_models import CityGraph, NodeType
from .config import get_settings
```

**Path Aliases:**
- No path aliases configured; relative imports used throughout
- Barrel files (index.ts/index.py) used for component exports: `frontend/src/components/index.ts`

## Error Handling

**TypeScript/Frontend:**
- Custom error class: `ApiError extends Error` in `frontend/src/lib/api.ts` with status code property
- Error propagation: thrown in fetch wrapper, caught in React hooks with try-catch
- Errors converted to strings: `err instanceof Error ? err.message : 'Unknown error'`
- State management: error stored in component state, displayed in UI
- Pattern: `setState(prev => ({ ...prev, error: message }))`

**Python/Backend:**
- FastAPI HTTPException for API errors: `raise HTTPException(status_code=500, detail=str(e))`
- Bare `except Exception as e:` catches in route handlers
- Error passed to detail field as string
- No custom exception classes in solver modules
- Validation errors: handled by Pydantic models automatically

## Logging

**Framework:** `console` (built-in)

**Patterns:**
- TypeScript: None visible in source code (console methods not used in component/hook code)
- Python: Print statements used for startup/shutdown messages in `app/main.py`:
  ```python
  print("🚀 Quantum Priority Router API starting...")
  print("👋 Shutting down...")
  ```
- No structured logging library (Python logging module not imported)
- Emojis used in messages for visual distinction

## Comments

**When to Comment:**
- JSDoc/module-level documentation at file top with triple-slash comments
- Function purpose documentation: one-line summary above function
- Complex logic: inline comments explaining "why" not "what"
- Constraint explanations: especially in algorithm implementations

**JSDoc/TSDoc:**
- Used for module-level documentation: `/** Comment */` format
- Function documentation in Python (docstrings): triple quotes with Args/Returns sections
- Example from `useSolver.ts`:
  ```typescript
  /**
   * React hook for solver operations
   */
  ```
- Example from `greedy_solver.py`:
  ```python
  """
  Greedy Solver for Priority-Constrained Routing.

  Implements a nearest-neighbor heuristic...
  """
  ```

## Function Design

**Size:** Functions kept small and focused, typically 20-50 lines
- Examples: `useSolver()` hook has separate functions for different operations
- Nested helper functions used for internal logic: `find_nearest()`, `get_weighted_distance()` in greedy solver
- Callbacks extracted to separate functions in React components

**Parameters:**
- TypeScript: interface-based props for components and functions
- Optional parameters denoted with `?` for TypeScript, default values shown in function signature
- Python: type annotations included for all parameters
- Example: `async function generateCity(nNodes = 10, priorityRatio = 0.3, trafficProfile = 'mixed')`

**Return Values:**
- TypeScript: explicit return types on functions. Example: `Promise<SolverResponse | null>`
- Consistent return types: null returned on error, typed response on success
- Python: type-hinted return types. Example: `-> SolverResponse:`
- Pydantic models used as return types in API routes

## Module Design

**Exports:**
- TypeScript: named exports for components, types, functions
  ```typescript
  export const SolverControls: React.FC<Props> = (...) => ...
  export type SolverType = 'quantum' | 'greedy'
  export async function solveRoute(...): Promise<...>
  ```
- Barrel files aggregate exports: `frontend/src/components/index.ts` re-exports all components
- Default exports avoided

**Barrel Files:**
- Used for component collections: `frontend/src/components/index.ts`
- Simplifies imports: `import { InteractiveMap, SolverControls } from './components'`
- Python: standard `__init__.py` present but minimal usage in backend
- Benefits: reduces import path depth, centralizes what's public

## API Response Models

**Consistency Pattern:**
- All API responses wrapped in Pydantic models defined in `backend/src/data_models.py`
- Request/response shapes mirrored between frontend types and backend models
- Frontend types in `frontend/src/lib/types.ts` match Python Pydantic models exactly
- Field aliases handle naming mismatches: Python `from_node` → JSON `from`

**Example alignment:**
- Python `Edge` model: `from_node`, `to_node` with alias configuration
- Frontend `Edge` interface: `from`, `to` (JSON representation)
- Pydantic config: `populate_by_name = True` allows both names

---

*Convention analysis: 2026-02-04*
