import React, { useEffect, useState } from 'react';
import { ShadowWorkflow } from '../types';
import { getShadowWorkflows } from '../api/client';
import { Badge } from '../components/Badge';
import { Lock, AlertTriangle, ShieldAlert, CheckCircle2 } from 'lucide-react';

export const ShadowWorkflows: React.FC = () => {
  const [shadows, setShadows] = useState<ShadowWorkflow[]>([]);

  useEffect(() => {
    getShadowWorkflows().then(data => setShadows(data)).catch(console.error);
  }, []);

  return (
    <div className="space-y-6 font-mono text-xs">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Lock size={20} className="text-rose-400" />
            <span>SHADOW WORKFLOW MODELS (CLONED WORKFLOWS)</span>
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Structural workflow models duplicated for alternate identities under credential isolation
          </p>
        </div>
      </div>

      {/* Mandatory M1 Scope Boundary Banner */}
      <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-700/60 text-rose-200 flex items-start gap-3">
        <ShieldAlert size={24} className="text-rose-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold uppercase tracking-wider text-xs text-rose-300">
            MILESTONE 1 SAFETY INVARIANT — MODEL ONLY
          </div>
          <p className="text-[11px] leading-relaxed text-rose-200/90">
            Shadow Workflows are structural model clones of reference user workflows. Source identity authentication secrets (bearer tokens, cookies, auth headers) have been explicitly stripped to enforce <strong>Credential Isolation</strong>. No HTTP requests have been replayed to any server, and no authorization decision or vulnerability verdict has been rendered.
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {shadows.map((sh) => (
          <div key={sh.id} className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
            <div className="space-y-1">
              <div className="text-slate-100 font-bold flex items-center gap-2">
                <span>Shadow Model #{sh.id.slice(0, 8)}</span>
                <Badge variant="danger">{sh.status}</Badge>
              </div>
              <div className="text-[11px] text-slate-400 space-x-4">
                <span>Source Workflow: {sh.source_workflow_id.slice(0, 8)}</span>
                <span>Source Identity: {sh.source_identity_id.slice(0, 8)}</span>
                <span>Shadow Identity: {sh.shadow_identity_id.slice(0, 8)}</span>
              </div>
              <div className="text-[10px] text-slate-500">
                Policy: <span className="text-cyan-400">{sh.clone_policy}</span> | Created: {new Date(sh.created_at).toLocaleString()}
              </div>
            </div>

            <div className="flex flex-col items-end gap-1">
              <Badge variant="warning">NO REPLAY</Badge>
              <span className="text-[10px] text-slate-500">Structural Clone Only</span>
            </div>
          </div>
        ))}

        {shadows.length === 0 && (
          <div className="p-8 text-center text-slate-500 bg-slate-900 border border-slate-800 rounded-lg">
            No shadow workflows created yet. Go to Workflows tab to clone a workflow model for an alternate identity.
          </div>
        )}
      </div>
    </div>
  );
};
