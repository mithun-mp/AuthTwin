import React, { useState, useEffect, useRef } from 'react';
import { WorkflowNode, WorkflowEdge, Dependency, WorkflowGraphResponse, CanonicalNode, CanonicalEdge } from '../types';
import { adaptWorkflowResponseToCanonicalGraph } from '../graph/adapter';
import { Renderer2D } from '../graph/Renderer2D';
import { Renderer3D } from '../graph/Renderer3D';
import { NodeInspector } from './NodeInspector';
import { Badge } from './Badge';
import { Layers, Box, Info, Sparkles, Filter, ListOrdered, ChevronDown, ChevronUp, Link as LinkIcon, ArrowRight, Activity } from 'lucide-react';

interface GraphVisualizerProps {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  dependencies: Dependency[];
  rawGraphResponse?: WorkflowGraphResponse;
}

export const GraphVisualizer: React.FC<GraphVisualizerProps> = ({
  nodes,
  edges,
  dependencies,
  rawGraphResponse
}) => {
  const [renderMode, setRenderMode] = useState<'2D' | '3D'>('2D');
  const [viewType, setViewType] = useState<'logical' | 'execution'>('logical');
  const [selectedNode, setSelectedNode] = useState<CanonicalNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<CanonicalEdge | null>(null);
  const [showInspector, setShowInspector] = useState<boolean>(false);
  const [showLinearWorkflow, setShowLinearWorkflow] = useState<boolean>(false);
  const [highlightedStepIndex, setHighlightedStepIndex] = useState<number | null>(null);

  const stepRefs = useRef<Record<number, HTMLDivElement | null>>({});

  // Adapt backend payload into Canonical Graph
  const canonicalGraph = adaptWorkflowResponseToCanonicalGraph(
    rawGraphResponse || {
      workflow: { id: 'wf-1', session_id: 's-1', identity_id: 'i-1', name: 'Wf', node_count: nodes.length, edge_count: edges.length, created_at: new Date().toISOString() },
      linear_workflow: { workflow_id: 'wf-1', session_id: 's-1', identity_id: 'i-1', name: 'Wf', created_at: new Date().toISOString(), steps: [] },
      nodes,
      edges,
      canonical_nodes: [],
      canonical_edges: [],
      dependencies
    }
  );

  useEffect(() => {
    if (canonicalGraph.nodes.length > 0 && (!selectedNode || !canonicalGraph.nodes.find(n => n.id === selectedNode.id))) {
      setSelectedNode(canonicalGraph.nodes[0]);
    }
  }, [canonicalGraph.nodes]);

  const handleSelectNode = (node: CanonicalNode) => {
    setSelectedNode(node);
    setSelectedEdge(null);
    setShowInspector(true);

    if (node.occurrences.length > 0) {
      setHighlightedStepIndex(node.occurrences[0].occurrence_index);
    }
  };

  const handleSelectEdge = (edge: CanonicalEdge) => {
    setSelectedEdge(edge);
    setSelectedNode(null);
    setShowInspector(true);
  };

  const handleJumpToLinearStep = (stepIndex: number) => {
    setShowLinearWorkflow(true);
    setHighlightedStepIndex(stepIndex);
    setTimeout(() => {
      const el = stepRefs.current[stepIndex];
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 100);
  };

  const linearSteps = rawGraphResponse?.linear_workflow?.steps || [];

  const handleLinearStepClick = (stepIndex: number, nodeId: string) => {
    setHighlightedStepIndex(stepIndex);
    const targetNode = canonicalGraph.nodes.find(n => n.id === nodeId || n.occurrences.some(o => o.occurrence_index === stepIndex));
    if (targetNode) {
      setSelectedNode(targetNode);
      setSelectedEdge(null);
      setShowInspector(true);
    }
  };

  const getMethodBadgeVariant = (method: string) => {
    switch (method.toUpperCase()) {
      case 'GET': return 'info';
      case 'POST': return 'success';
      case 'PUT': case 'PATCH': return 'warning';
      case 'DELETE': return 'danger';
      default: return 'secondary';
    }
  };

  return (
    <div className="space-y-4 font-mono text-xs relative">
      {/* Visualizer Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900 p-3 rounded-lg border border-slate-800 shadow-md">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Layers size={16} className="text-cyan-400" />
            <span className="font-bold text-slate-200 uppercase text-xs">CANONICAL WORKFLOW GRAPH ENGINE</span>
          </div>
          <span className="text-slate-500 text-[11px]">
            ({canonicalGraph.nodes.length} States • {canonicalGraph.edges.length} Edges • {linearSteps.length} Total Execs)
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Toggle Linear Workflow Drawer Button */}
          <button
            onClick={() => setShowLinearWorkflow(prev => !prev)}
            className={`px-3 py-1.5 rounded font-bold flex items-center gap-1.5 transition-all text-[11px] ${
              showLinearWorkflow
                ? 'bg-amber-950 text-amber-300 border border-amber-500/70 shadow-md'
                : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200'
            }`}
          >
            <ListOrdered size={14} />
            <span>Authoritative Replay Workflow</span>
            {showLinearWorkflow ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>

          {/* View Type Toggle */}
          <div className="flex items-center bg-slate-950 p-1 rounded border border-slate-800">
            <button
              onClick={() => setViewType('logical')}
              className={`px-2.5 py-1 rounded text-[10px] font-bold transition-colors ${
                viewType === 'logical' ? 'bg-cyan-900 text-cyan-200' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Logical View
            </button>
            <button
              onClick={() => setViewType('execution')}
              className={`px-2.5 py-1 rounded text-[10px] font-bold transition-colors ${
                viewType === 'execution' ? 'bg-cyan-900 text-cyan-200' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Execution View
            </button>
          </div>

          {/* 2D vs 3D Render Mode Switcher */}
          <button
            onClick={() => setRenderMode('2D')}
            className={`px-3 py-1.5 rounded font-bold flex items-center gap-1.5 transition-all ${
              renderMode === '2D'
                ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/70 shadow-md'
                : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200'
            }`}
          >
            <Layers size={14} />
            <span>2D Flowchart</span>
          </button>

          <button
            onClick={() => setRenderMode('3D')}
            className={`px-3 py-1.5 rounded font-bold flex items-center gap-1.5 transition-all ${
              renderMode === '3D'
                ? 'bg-indigo-950 text-indigo-300 border border-indigo-500/70 shadow-md'
                : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200'
            }`}
          >
            <Box size={14} />
            <span>3D Cybernetic</span>
          </button>
        </div>
      </div>

      {/* Authoritative Linear Execution Workflow Drawer (Collapsible) */}
      {showLinearWorkflow && (
        <div className="bg-slate-900/90 border border-amber-800/60 rounded-lg p-4 space-y-3 animate-in slide-in-from-top duration-200">
          <div className="flex items-center justify-between border-b border-amber-900/40 pb-2">
            <div className="flex items-center gap-2">
              <ListOrdered size={16} className="text-amber-400" />
              <h3 className="font-bold text-slate-100 uppercase text-xs tracking-wider">
                AUTHORITATIVE LINEAR REPLAY WORKFLOW ({linearSteps.length} CHRONOLOGICAL STEPS)
              </h3>
            </div>
            <span className="text-[10px] text-amber-300 font-mono">
              Replay Engine Execution Sequence Target
            </span>
          </div>

          {linearSteps.length === 0 ? (
            <div className="p-4 text-center text-slate-500 font-mono">
              No linear execution steps registered. Execute target sandbox requests to populate replay sequence.
            </div>
          ) : (
            <div className="flex items-center gap-3 overflow-x-auto py-2 scrollbar-thin scrollbar-thumb-amber-800">
              {linearSteps.map((step) => {
                const isHighlighted = highlightedStepIndex === step.step_index;
                return (
                  <div
                    key={step.step_index}
                    ref={(el) => { stepRefs.current[step.step_index] = el; }}
                    onClick={() => handleLinearStepClick(step.step_index, step.canonical_node_id || '')}
                    className={`flex-shrink-0 w-64 p-3 rounded-lg border cursor-pointer transition-all space-y-2 select-none shadow-md ${
                      isHighlighted
                        ? 'bg-amber-950/80 border-amber-400 ring-2 ring-amber-500/80 shadow-amber-950/90'
                        : 'bg-slate-950 border-slate-800 hover:border-slate-700 hover:bg-slate-900/80'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-amber-400 px-1.5 py-0.5 rounded bg-amber-950 border border-amber-800">
                        Step #{step.step_index}
                      </span>
                      <Badge variant={getMethodBadgeVariant(step.method)}>{step.method}</Badge>
                    </div>

                    <div className="text-xs font-mono font-bold text-slate-200 truncate" title={step.path}>
                      {step.path}
                    </div>

                    <div className="text-[10px] text-slate-400 flex items-center justify-between border-t border-slate-800/80 pt-1.5">
                      <span>Status: <strong className="text-emerald-400">HTTP {step.res_status}</strong></span>
                      <span className="text-slate-500">{step.param_bindings?.length || 0} dep(s)</span>
                    </div>

                    {step.param_bindings && step.param_bindings.length > 0 && (
                      <div className="text-[9px] text-amber-300 font-mono bg-amber-950/40 p-1.5 rounded border border-amber-900/50 space-y-0.5">
                        {step.param_bindings.map((b, bIdx) => (
                          <div key={bIdx} className="truncate">
                            Dep: {b.consumer_parameter} ← {b.extracted_value}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Main Graph Area */}
      <div className="relative">
        {renderMode === '2D' ? (
          <Renderer2D
            nodes={canonicalGraph.nodes}
            edges={canonicalGraph.edges}
            dependencies={dependencies}
            selectedNode={selectedNode}
            selectedEdge={selectedEdge}
            onSelectNode={handleSelectNode}
            onSelectEdge={handleSelectEdge}
            viewType={viewType}
          />
        ) : (
          <Renderer3D
            nodes={canonicalGraph.nodes}
            edges={canonicalGraph.edges}
            dependencies={dependencies}
            selectedNode={selectedNode}
            selectedEdge={selectedEdge}
            onSelectNode={handleSelectNode}
            onSelectEdge={handleSelectEdge}
            viewType={viewType}
          />
        )}
      </div>

      {/* Slide-out Inspector (Node or Edge Evidence) */}
      {showInspector && (
        <NodeInspector
          node={selectedNode}
          edge={selectedEdge}
          dependencies={dependencies}
          onClose={() => setShowInspector(false)}
          onJumpToLinearStep={handleJumpToLinearStep}
        />
      )}
    </div>
  );
};

