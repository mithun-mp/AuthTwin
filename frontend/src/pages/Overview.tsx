import React, { useEffect, useState } from 'react';
import { StatCard } from '../components/StatCard';
import { Badge } from '../components/Badge';
import {
  Shield, Layers, Users, Database, FileCode, Network, GitBranch, Lock, Upload, CheckCircle2, ArrowRight
} from 'lucide-react';
import {
  getTargets, getIdentities, getSessions, getTransactions,
  getDependencies, getWorkflows, getShadowWorkflows, importHAR, importOpenAPI
} from '../api/client';
import { Workflow, ShadowWorkflow } from '../types';

interface OverviewProps {
  onLogEvent?: (type: 'INFO' | 'SUCCESS' | 'WARN' | 'SECURITY', module: string, msg: string) => void;
}

export const Overview: React.FC<OverviewProps> = ({ onLogEvent }) => {
  const [stats, setStats] = useState({
    targets: 0,
    identities: 0,
    sessions: 0,
    transactions: 0,
    dependencies: 0,
    workflows: 0,
    shadows: 0
  });
  const [recentWorkflows, setRecentWorkflows] = useState<Workflow[]>([]);
  const [recentShadows, setRecentShadows] = useState<ShadowWorkflow[]>([]);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [t, id, s, tx, dep, wf, sh] = await Promise.all([
        getTargets(), getIdentities(), getSessions(), getTransactions(),
        getDependencies(), getWorkflows(), getShadowWorkflows()
      ]);

      setStats({
        targets: t.length,
        identities: id.length,
        sessions: s.length,
        transactions: tx.length,
        dependencies: dep.length,
        workflows: wf.length,
        shadows: sh.length
      });

      setRecentWorkflows(wf.slice(0, 4));
      setRecentShadows(sh.slice(0, 4));
    } catch (err: any) {
      console.error("Failed loading stats:", err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>, type: 'har' | 'openapi') => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      if (type === 'har') {
        const res = await importHAR(file);
        const msg = `HAR Ingested: ${res.imported_count} HTTP Transactions parsed into Session #${res.session_id.slice(0, 8)}`;
        setMessage(msg);
        onLogEvent?.('SUCCESS', 'HAR_INGEST', msg);
      } else {
        const res = await importOpenAPI(file);
        const msg = `OpenAPI Loaded: ${res.title} (${res.operations.length} operations mapped)`;
        setMessage(msg);
        onLogEvent?.('INFO', 'OPENAPI_PARSE', msg);
      }
      await loadData();
    } catch (err: any) {
      const errMsg = `Import Error: ${err.response?.data?.detail || err.message}`;
      setMessage(errMsg);
      onLogEvent?.('WARN', 'IMPORT_FAIL', errMsg);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Ingestion Controls */}
      <div className="glass-panel rounded-lg p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative overflow-hidden">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Shield className="text-cyan-400" size={22} />
            <h1 className="text-lg font-display font-extrabold text-slate-100 tracking-wide">
              AUTHTWIN SECURITY COMMAND CENTER
            </h1>
          </div>
          <p className="text-xs font-mono text-slate-400">
            Black-box workflow-aware authorization analysis pipeline for web APIs
          </p>
        </div>

        {/* Upload Buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-950/90 text-cyan-300 border border-cyan-500/60 hover:bg-cyan-900/80 font-mono text-xs font-bold transition-all shadow-md shadow-cyan-950">
            <Upload size={14} />
            <span>IMPORT HAR TRAFFIC</span>
            <input type="file" accept=".har,.json" onChange={(e) => handleFileUpload(e, 'har')} className="hidden" />
          </label>

          <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-950/90 text-violet-300 border border-violet-500/60 hover:bg-violet-900/80 font-mono text-xs font-bold transition-all shadow-md shadow-violet-950">
            <FileCode size={14} />
            <span>IMPORT OPENAPI SPEC</span>
            <input type="file" accept=".json,.yaml,.yml" onChange={(e) => handleFileUpload(e, 'openapi')} className="hidden" />
          </label>
        </div>
      </div>

      {message && (
        <div className="p-3 rounded-lg bg-cyan-950/60 border border-cyan-500/60 text-xs font-mono text-cyan-300 flex items-center justify-between shadow-md">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={16} className="text-cyan-400" />
            <span>{message}</span>
          </div>
          <button onClick={() => setMessage(null)} className="text-slate-400 hover:text-slate-200">×</button>
        </div>
      )}

      {/* Main Stat Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Targets" value={stats.targets} icon={Shield} accentColor="text-cyan-400" glowColor="hover:border-cyan-500/60" />
        <StatCard title="Identities" value={stats.identities} icon={Users} accentColor="text-indigo-400" glowColor="hover:border-indigo-500/60" />
        <StatCard title="Sessions" value={stats.sessions} icon={Database} accentColor="text-purple-400" glowColor="hover:border-purple-500/60" />
        <StatCard title="Transactions" value={stats.transactions} icon={Layers} accentColor="text-emerald-400" glowColor="hover:border-emerald-500/60" />
        <StatCard title="Dependencies" value={stats.dependencies} icon={Network} accentColor="text-amber-400" glowColor="hover:border-amber-500/60" />
        <StatCard title="Workflows (WSG)" value={stats.workflows} icon={GitBranch} accentColor="text-cyan-400" glowColor="hover:border-cyan-500/60" />
        <StatCard title="Shadow Models" value={stats.shadows} subtitle="MODEL ONLY" icon={Lock} accentColor="text-rose-400" glowColor="hover:border-rose-500/60" />
      </div>

      {/* Pipeline Telemetry Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* WSG Workflows */}
        <div className="glass-panel rounded-lg p-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
            <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <GitBranch size={16} className="text-cyan-400" />
              <span>RECONSTRUCTED WORKFLOW STATE GRAPHS</span>
            </h3>
            <Badge variant="cyan">WSG GENERATED</Badge>
          </div>

          {recentWorkflows.length > 0 ? (
            <div className="space-y-3 font-mono text-xs">
              {recentWorkflows.map((wf) => (
                <div key={wf.id} className="p-3.5 rounded-lg bg-slate-950/80 border border-slate-800 flex items-center justify-between hover:border-slate-700 transition-colors">
                  <div>
                    <div className="text-slate-100 font-bold">{wf.name}</div>
                    <div className="text-[11px] text-slate-400 mt-1 space-x-3">
                      <span>Nodes: <span className="text-cyan-400 font-semibold">{wf.node_count}</span></span>
                      <span>Transitions: <span className="text-amber-400 font-semibold">{wf.edge_count}</span></span>
                    </div>
                  </div>
                  <Badge variant="info">WSG READY</Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-10 text-center font-mono text-xs text-slate-500">
              No workflows reconstructed yet. Import a HAR file above to generate workflow state graphs.
            </div>
          )}
        </div>

        {/* Shadow Workflow Models */}
        <div className="glass-panel rounded-lg p-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
            <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Lock size={16} className="text-rose-400" />
              <span>SHADOW WORKFLOW MODELS</span>
            </h3>
            <Badge variant="danger">MODEL ONLY</Badge>
          </div>

          {recentShadows.length > 0 ? (
            <div className="space-y-3 font-mono text-xs">
              {recentShadows.map((sh) => (
                <div key={sh.id} className="p-3.5 rounded-lg bg-slate-950/80 border border-slate-800 flex items-center justify-between hover:border-slate-700 transition-colors">
                  <div>
                    <div className="text-slate-100 font-bold">Shadow Model #{sh.id.slice(0, 8)}</div>
                    <div className="text-[11px] text-slate-400 mt-1">
                      Policy: <span className="text-emerald-400 font-semibold">{sh.clone_policy}</span>
                    </div>
                  </div>
                  <Badge variant="danger">MODEL ONLY</Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-10 text-center font-mono text-xs text-slate-500">
              No shadow workflows created yet. Go to Workflows tab to clone a model for an alternate identity.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
