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
    generate(8, 0.3, 'mixed');
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  const handleGenerate = async (nodes: number, priorityRatio: number, traffic: string, includeDepot: boolean = false) => {
    clear();
    await generate(nodes, priorityRatio, traffic, includeDepot);
  };

  const handleGraphChange = (newGraph: CityGraph) => {
    setGraph(newGraph);
    clear();
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
          <h1>
            <span className="header-icon">
              <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3" /><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" /></svg>
            </span>
            Quantum Priority Router
          </h1>
          <p className="subtitle">QAOA Quantum Optimization for Urban Logistics</p>
        </div>
        <div className="health-status">
          {health ? (
            <span className={`status-badge ${health.status === 'healthy' ? 'ok' : 'error'}`}>
              <span className="status-indicator" />
              {health.status === 'healthy' ? 'QAOA Active' : 'Mock Mode'}
            </span>
          ) : (
            <span className="status-badge loading">
              <span className="status-indicator" />
              Connecting
            </span>
          )}
        </div>
      </header>

      <main className="app-main">
        <div className="main-content">
          <section className="map-section">
            <div className="section-header">
              <span className="section-icon section-icon--map">M</span>
              <h2>Interactive City Map</h2>
            </div>
            <p className="section-hint">Click on the map to add delivery points. Use the toolbar to set priority or delete nodes.</p>

            {error && (
              <div className="error-message">
                <span className="error-icon">!</span>
                {error}
              </div>
            )}

            <InteractiveMap
              graph={graph}
              route={displayRoute}
              highlightRoute={!!quantumResult || !!greedyResult}
              onGraphChange={handleGraphChange}
              editable={true}
            />

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
                        title="Quantum Route"
                      />
                    )}
                    {greedyResult && (
                      <RouteVisualizer
                        graph={graph}
                        result={greedyResult}
                        title="Greedy Route"
                      />
                    )}
                  </div>
                </div>
              </div>
            )}
          </section>

          <aside className="controls-sidebar">
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
        <p>Quantum-Annealing Mixed-Priority Routing Framework | Built with Qiskit QAOA</p>
      </footer>
    </div>
  );
}

export default App;
