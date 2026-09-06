import React, { useEffect, useState } from 'react';
import { Workflow, WorkflowGraphResponse, Identity } from '../types';
import {
  getWorkflows, getWorkflowGraph, getIdentities, cloneWorkflow,
  deleteWorkflow, deleteAllWorkflows
} from '../api/client';
import { GraphVisualizer } from '../components/GraphVisualizer';
import { Badge } from '../components/Badge';
import { GitBranch, Lock, Eye, Copy, ArrowRight, Trash2, RefreshCw } from 'lucide-react';

export const Workflows: React.FC = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedWf, setSelectedWf] = useState<Workflow | null>(null);
  const [graphData, setGraphData] = useState<WorkflowGraphResponse | null>(null);
  const [identities, setIdentities] = useState<Identity[]>([]);
  const [targetIdentityId, setTargetIdentityId] = useState<string>('');
  const [cloneMsg, setCloneMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchWorkflowsData = async () => {
    try {
      setLoading(true);
      const [wfList, idList] = await Promise.all([getWorkflows(), getIdentities()]);
      setWorkflows(wfList);
      setIdentities(idList);
      if (wfList.length > 0) {
        handleSelectWorkflow(wfList[0]);
      } else {
        setSelectedWf(null);
        setGraphData(null);
      }
      const alt = idList.find(i => i.role === 'Alternate') || idList[0];
      if (alt) setTargetIdentityId(alt.id);
    } catch (err) {
      console.error("Error loading workflows", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflowsData();
  }, []);

  const handleSelectWorkflow = async (wf: Workflow) => {
    setSelectedWf(wf);
    try {
      const g = await getWorkflowGraph(wf.id);
      setGraphData(g);
    } catch (err) {
      console.error("Error loading graph:", err);
    }
  };

  const handleClone = async () => {
    if (!selectedWf || !targetIdentityId) return;
    try {
      const shadow = await cloneWorkflow(selectedWf.id, targetIdentityId);
      setCloneMsg(`Shadow Workflow Cloned! ID: ${shadow.id.slice(0, 8)} (Status: MODEL_ONLY)`);
    } catch (err: any) {
      setCloneMsg(`Cloning error: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleDeleteWorkflow = async (wfId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this workflow?")) return;
    try {
      await deleteWorkflow(wfId);
      await fetchWorkflowsData();
    } catch (err) {
      console.error("Failed to delete workflow", err);
    }
  };

  const handleDeleteAll = async () => {
    if (!confirm("Delete all workflows from database?")) return;
    try {
      await deleteAllWorkflows();
      await fetchWorkflowsData();
    } catch (err) {
      console.error("Failed to delete all workflows", err);
    }
  };

  return (
    <div className="space-y-6 font-mono text-xs">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <GitBranch size={20} className="text-cyan-400" />
            <span>RECONSTRUCTED WORKFLOW STATE GRAPHS (WSG)</span>
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Directed per-session workflow state graphs and shadow model duplication
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchWorkflowsData}
            disabled={loading}
            className="px-3 py-1.5 rounded bg-slate-900 text-cyan-300 border border-slate-700 hover:bg-slate-800 font-bold flex items-center gap-1.5 transition-all text-xs"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            <span>Refresh Graphs</span>
          </button>
          {workflows.length > 0 && (
            <button
              onClick={handleDeleteAll}
              className="px-3 py-1.5 rounded bg-rose-950/80 text-rose-300 border border-rose-800 hover:bg-rose-900 font-bold flex items-center gap-1.5 transition-all text-xs"
            >
              <Trash2 size={13} />
              <span>Clear All Graphs</span>
            </button>
          )}
        </div>
      </div>

      {cloneMsg && (
        <div className="p-3 rounded bg-amber-950/60 border border-amber-700/60 text-amber-300 flex items-center justify-between">
          <span>{cloneMsg}</span>
          <button onClick={() => setCloneMsg(null)} className="text-slate-400 hover:text-slate-200">×</button>
        </div>
      )}

      {/* Workflow Selector & Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <h3 className="font-bold text-slate-200 uppercase text-[11px] mb-3 flex items-center justify-between">
            <span>SELECT RECONSTRUCTED WORKFLOW</span>
            <span className="text-cyan-400">({workflows.length})</span>
          </h3>
          <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
            {workflows.map((wf) => (
              <div
                key={wf.id}
                onClick={() => handleSelectWorkflow(wf)}
                className={`p-3 rounded cursor-pointer border transition-all flex items-center justify-between ${
                  selectedWf?.id === wf.id
                    ? 'bg-cyan-950/60 border-cyan-500 text-cyan-200 font-semibold'
                    : 'bg-slate-950 border-slate-800 hover:border-slate-700 text-slate-300'
                }`}
              >
                <div>
                  <div className="font-bold truncate max-w-[180px]">{wf.name}</div>
                  <div className="text-[10px] text-slate-500 mt-1">Nodes: {wf.node_count} | Edges: {wf.edge_count}</div>
                </div>
                <button
                  onClick={(e) => handleDeleteWorkflow(wf.id, e)}
                  className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-slate-900"
                  title="Delete workflow"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
            {workflows.length === 0 && (
              <div className="text-slate-500 text-center py-6">No workflows found. Record traffic in Interceptor tab.</div>
            )}
          </div>
        </div>

        {/* Clone to Shadow Workflow Box */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-lg p-4 flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-slate-200 uppercase text-[11px] mb-2 flex items-center gap-2">
              <Lock size={16} className="text-rose-400" />
              <span>CLONE SHADOW WORKFLOW MODEL</span>
            </h3>
            <p className="text-slate-400 text-[11px] mb-4">
              Duplicate selected workflow structure to an alternate identity under strict credential isolation invariant.
            </p>

            <div className="flex flex-col sm:flex-row items-center gap-3">
              <div className="w-full sm:w-auto flex-1">
                <label className="block text-slate-500 text-[10px] mb-1 uppercase">Target Alternate Identity</label>
                <select
                  value={targetIdentityId}
                  onChange={(e) => setTargetIdentityId(e.target.value)}
                  className="w-full p-2 rounded bg-slate-950 border border-slate-800 text-slate-200"
                >
                  {identities.map(i => (
                    <option key={i.id} value={i.id}>{i.name} ({i.role})</option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleClone}
                disabled={!selectedWf || !targetIdentityId}
                className="w-full sm:w-auto mt-4 sm:mt-0 px-4 py-2 rounded bg-rose-950/80 text-rose-300 border border-rose-700/80 hover:bg-rose-900/60 font-semibold flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
              >
                <Copy size={14} />
                <span>Clone Shadow Workflow</span>
              </button>
            </div>
          </div>

          <div className="mt-3 p-2.5 rounded bg-slate-950 border border-slate-800/80 text-[10px] text-slate-400 flex items-center gap-2">
            <Badge variant="warning">NOTICE</Badge>
            <span>Shadow workflow creation is MODEL-ONLY. No request replay or authorization verdict is executed.</span>
          </div>
        </div>
      </div>

      {/* Interactive WSG Canvas */}
      {graphData && (
        <div className="mt-6">
          <GraphVisualizer
            nodes={graphData.nodes}
            edges={graphData.edges}
            dependencies={graphData.dependencies}
          />
        </div>
      )}
    </div>
  );
};

