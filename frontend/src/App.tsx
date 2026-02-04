/**
 * Quantum Priority Router - Main Application
 */

import { useEffect, useState } from 'react';
import { InteractiveMap, SolverControls, MetricsTable, RouteVisualizer } from './components';
import { useSolver, useCityGraph, useHealth } from './hooks/useSolver';
import type { SolverType, QUBOParams, CityGraph } from './lib/types';
import './App.css';

function App() {
  const [selectedSolver, setSelectedSolver] = useState<'quantum' | 'greedy' | 'both'>('both');
  const { health, check: checkHealth } = useHealth();
  const { graph, loading: graphLoading, error: graphError, generate, setGraph } = useCityGraph();
  const {
    loading: solverLoading,
    error: solverError,
    quantumResult,
    greedyResult,
    comparison,
    solve,
    compare,
    clear,
  } = useSolver();

  useEffect(() => {
    checkHealth();
    // Generate initial city on mount
    generate(8, 0.3, 'mixed');
  }, []);

  const handleSolve = async (solver: SolverType, params?: QUBOParams) => {
    if (!graph) return;
    setSelectedSolver(solver);
    await solve(graph, solver, params);
  };

  const handleCompare = async () => {
    if (!graph) return;
    setSelectedSolver('both');
    await compare(graph);
  };

  const handleGenerate = async (nodes: number, priorityRatio: number, traffic: string) => {
    clear();
    await generate(nodes, priorityRatio, traffic);
  };

  const handleGraphChange = (newGraph: CityGraph) => {
    setGraph(newGraph);
    clear(); // Clear previous results when graph changes
  };

  const displayRoute = selectedSolver === 'quantum' && quantumResult
    ? quantumResult.route
    : selectedSolver === 'greedy' && greedyResult
      ? greedyResult.route
      : quantumResult?.route || greedyResult?.route || [];

  const loading = graphLoading || solverLoading;
  const error = graphError || solverError;

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>⚛️ Quantum Priority Router</h1>
          <p className="subtitle">QAOA Quantum Optimization for Urban Logistics</p>
        </div>
        <div className="health-status">
          {health ? (
            <span className={`status-badge ${health.status === 'healthy' ? 'ok' : 'error'}`}>
              {health.status === 'healthy' ? '⚛️ QAOA' : '🔌 Mock Mode'}
            </span>
          ) : (
            <span className="status-badge loading">Connecting...</span>
          )}
        </div>
      </header>

      <main className="app-main">
        <div className="main-content">
          <section className="map-section">
            <h2>🗺️ Interactive City Map</h2>
            <p className="section-hint">Click on the map to add delivery points. Use the toolbar to set priority or delete nodes.</p>
            {error && <div className="error-message">⚠️ {error}</div>}

            <InteractiveMap
              graph={graph}
              route={displayRoute}
              highlightRoute={!!quantumResult || !!greedyResult}
              onGraphChange={handleGraphChange}
              editable={true}
            />

            {/* Results shown under the map */}
            {(quantumResult || greedyResult || comparison) && (
              <div className="map-results">
                <div className="results-grid">
                  <div className="results-section">
                    <MetricsTable
                      quantumResult={quantumResult}
                      greedyResult={greedyResult}
                      comparison={comparison}
                    />
                  </div>
                  <div className="routes-section">
                    {quantumResult && (
                      <RouteVisualizer
                        graph={graph}
                        result={quantumResult}
                        title="⚛️ Quantum Route"
                      />
                    )}
                    {greedyResult && (
                      <RouteVisualizer
                        graph={graph}
                        result={greedyResult}
                        title="🔢 Greedy Route"
                      />
                    )}
                  </div>
                </div>
              </div>
            )}
          </section>

          <aside className="controls-section">
            <SolverControls
              onSolve={handleSolve}
              onCompare={handleCompare}
              onGenerate={handleGenerate}
              loading={loading}
              graphLoaded={!!graph && graph.nodes.length > 0}
            />
          </aside>
        </div>
      </main>

      <footer className="app-footer">
        <p>Quantum-Annealing Mixed-Priority Routing | Built with Qiskit QAOA</p>
      </footer>
    </div>
  );
}

export default App;
