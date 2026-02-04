---
phase: 04-testing
plan: 03
subsystem: testing
tags: [qubo, solver, mock-sampler, correctness, one-hot, priority-ordering]

dependency-graph:
  requires:
    - 02-authentication (auth required for API)
    - 03-observability (logging for test debugging)
  provides:
    - QUBO constraint verification tests
    - Mock sampler completeness tests
    - Route validation edge case tests
  affects:
    - 05-deployment (test coverage gates)

tech-stack:
  added: []
  patterns:
    - verify_one_hot helper function for constraint checking
    - Graph fixtures for test isolation (small_graph, large_graph)

key-files:
  created:
    - backend/tests/test_solver_correctness.py
  modified: []

decisions:
  - id: test-penalty-comparison
    choice: Test relative penalty differences instead of absolute values
    reason: QUBO coefficients combine multiple terms; relative comparison is more robust

metrics:
  duration: ~3 min
  completed: 2026-02-05
---

# Phase 04 Plan 03: Solver Correctness Tests Summary

**One-liner:** QUBO one-hot constraint verification, priority ordering tests, mock sampler completeness with 25 passing tests

## What Was Built

Created comprehensive solver correctness test suite covering TEST-03 (QUBO constraints) and TEST-04 (mock sampler validation):

### Test Classes Created

| Class | Tests | Purpose |
|-------|-------|---------|
| TestQUBOOneHotConstraints | 4 | Verify one-hot constraint satisfaction |
| TestPriorityOrdering | 5 | Verify priority nodes ordered before normal |
| TestMockSamplerCompleteness | 7 | Verify mock sampler produces valid routes |
| TestMockSamplerDeterminism | 2 | Verify consistent mock sampler behavior |
| TestRouteValidationEdgeCases | 7 | Edge cases for validate_route function |

### Key Test Coverage

**QUBO One-Hot Constraints (TEST-03):**
- Position one-hot: Each position has exactly one node
- Node one-hot: Each node appears at exactly one position
- Verified with MockSampler on small and large graphs
- Helper function `verify_one_hot()` for constraint checking

**Priority Ordering (TEST-03):**
- Priority nodes appear before normal nodes in routes
- All priority nodes are visited
- QUBO penalties correctly favor correct positions
- validate_route returns correct priority_satisfied flag

**Mock Sampler Completeness (TEST-04):**
- Routes visit all nodes (no missing nodes)
- No duplicate nodes in routes
- feasible flag is True for valid routes
- priority_satisfied flag is True when priorities first
- Route length equals node count
- Distance and travel_time are finite positive values

**Route Validation Edge Cases:**
- Empty route returns infeasible
- Partial route (missing nodes) returns infeasible
- Duplicate nodes returns infeasible
- Unknown node returns infeasible
- Complete route with wrong order: feasible=True, priority_satisfied=False
- All-priority graph works correctly
- All-normal graph works correctly

## Commits

| Hash | Message |
|------|---------|
| 4905a13 | test(04-03): add solver correctness tests for QUBO constraints and mock sampler |

## Test Coverage Statistics

- **Total tests:** 25
- **All passing:** Yes
- **File lines:** 387 (requirement: 120+)

### Test Distribution

- QUBO one-hot: 4 tests
- Priority ordering: 5 tests
- Mock sampler completeness: 7 tests
- Mock sampler determinism: 2 tests
- Route validation edge cases: 7 tests

## Technical Decisions

### Test Relative Penalty Differences

The test `test_priority_constraint_penalty` was updated to compare relative coefficients instead of checking for positive values. The QUBO linear coefficients combine multiple penalty terms:
- One-hot constraints (negative contribution)
- Priority position penalties (positive contribution)

The correct test verifies that priority nodes have *higher* (less favorable) coefficients in wrong positions compared to correct positions.

```python
# Correct approach: compare relative penalties
priority_correct = bqm.get_linear("x_P1_0")  # Position 0 (correct)
priority_wrong = bqm.get_linear("x_P1_2")    # Position 2 (wrong)
assert priority_wrong > priority_correct
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_priority_constraint_penalty assertion logic**
- **Found during:** Task 1 verification
- **Issue:** Test checked for positive linear coefficient, but coefficients combine multiple terms
- **Fix:** Changed to compare relative penalties (wrong position > correct position)
- **Files modified:** backend/tests/test_solver_correctness.py
- **Commit:** 4905a13

## Issues Encountered

None beyond the penalty test fix.

## Next Phase Readiness

**Blockers:** None

**For Phase 5 (Deployment):**
- Test suite provides coverage gates for deployment
- All 25 solver correctness tests passing
- Combined with input validation tests (04-01) provides comprehensive test coverage
