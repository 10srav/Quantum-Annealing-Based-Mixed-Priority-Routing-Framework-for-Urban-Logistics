/**
 * SolverControls - Controls for solver configuration and execution
 */

import React, { useState } from 'react';
import type { QUBOParams, SolverType } from '../lib/types';
import { DEFAULT_QUBO_PARAMS } from '../lib/config';

interface SolverControlsProps {
    onSolve: (solver: SolverType, params?: QUBOParams) => void;
    onCompare: () => void;
    onGenerate: (nodes: number, priorityRatio: number, traffic: string) => void;
    loading: boolean;
    graphLoaded: boolean;
}

export const SolverControls: React.FC<SolverControlsProps> = ({
    onSolve,
    onCompare,
    onGenerate,
    loading,
    graphLoaded,
}) => {
    const [numNodes, setNumNodes] = useState(10);
    const [priorityRatio, setPriorityRatio] = useState(0.3);
    const [trafficProfile, setTrafficProfile] = useState('mixed');
    const [showAdvanced, setShowAdvanced] = useState(false);
    const [params, setParams] = useState<QUBOParams>(DEFAULT_QUBO_PARAMS);

    return (
        <div className="solver-controls">
            <div className="controls-section">
                <h3>🏙️ City Generator</h3>
                <div className="control-group">
                    <label>
                        Nodes: {numNodes}
                        <input
                            type="range"
                            min="5"
                            max="25"
                            value={numNodes}
                            onChange={(e) => setNumNodes(parseInt(e.target.value))}
                        />
                    </label>
                </div>
                <div className="control-group">
                    <label>
                        Priority Ratio: {(priorityRatio * 100).toFixed(0)}%
                        <input
                            type="range"
                            min="0.1"
                            max="0.5"
                            step="0.1"
                            value={priorityRatio}
                            onChange={(e) => setPriorityRatio(parseFloat(e.target.value))}
                        />
                    </label>
                </div>
                <div className="control-group">
                    <label>
                        Traffic Profile
                        <select
                            value={trafficProfile}
                            onChange={(e) => setTrafficProfile(e.target.value)}
                        >
                            <option value="low">Low Traffic</option>
                            <option value="mixed">Mixed Traffic</option>
                            <option value="high">High Traffic</option>
                        </select>
                    </label>
                </div>
                <button
                    className="btn btn-secondary"
                    onClick={() => onGenerate(numNodes, priorityRatio, trafficProfile)}
                    disabled={loading}
                >
                    🎲 Generate City
                </button>
            </div>

            <div className="controls-section">
                <h3>⚛️ Quantum Solver</h3>

                <button
                    className="btn btn-toggle"
                    onClick={() => setShowAdvanced(!showAdvanced)}
                >
                    {showAdvanced ? '▼' : '▶'} QUBO Parameters
                </button>

                {showAdvanced && (
                    <div className="params-grid">
                        <label>
                            A (One-hot):
                            <input
                                type="number"
                                value={params.A}
                                onChange={(e) => setParams({ ...params, A: parseFloat(e.target.value) })}
                            />
                        </label>
                        <label>
                            B (Priority):
                            <input
                                type="number"
                                value={params.B}
                                onChange={(e) => setParams({ ...params, B: parseFloat(e.target.value) })}
                            />
                        </label>
                        <label>
                            Bp (Missing):
                            <input
                                type="number"
                                value={params.Bp}
                                onChange={(e) => setParams({ ...params, Bp: parseFloat(e.target.value) })}
                            />
                        </label>
                        <label>
                            C (Distance):
                            <input
                                type="number"
                                step="0.1"
                                value={params.C}
                                onChange={(e) => setParams({ ...params, C: parseFloat(e.target.value) })}
                            />
                        </label>
                    </div>
                )}
            </div>

            <div className="controls-section controls-section--actions">
                <h3>🚀 Run Solver</h3>
                <div className="solver-buttons">
                    <button
                        className="btn btn-quantum"
                        onClick={() => onSolve('quantum', params)}
                        disabled={loading || !graphLoaded}
                    >
                        {loading ? '⏳' : '⚛️'} Quantum
                    </button>
                    <button
                        className="btn btn-greedy"
                        onClick={() => onSolve('greedy')}
                        disabled={loading || !graphLoaded}
                    >
                        {loading ? '⏳' : '🔢'} Greedy
                    </button>
                </div>
                <button
                    className="btn btn-compare"
                    onClick={onCompare}
                    disabled={loading || !graphLoaded}
                >
                    {loading ? '⏳ Running...' : '⚔️ Compare Both'}
                </button>
            </div>
        </div>
    );
};
