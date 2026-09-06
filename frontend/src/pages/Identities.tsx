import React, { useEffect, useState } from 'react';
import { Identity, Target } from '../types';
import { getIdentities, getActiveTarget, createIdentity, deleteIdentity } from '../api/client';
import { Badge } from '../components/Badge';
import { Users, Plus, Shield, Trash2, RefreshCw } from 'lucide-react';

export const Identities: React.FC = () => {
  const [identities, setIdentities] = useState<Identity[]>([]);
  const [activeTarget, setActiveTarget] = useState<Target | null>(null);
  const [name, setName] = useState('');
  const [role, setRole] = useState<'Primary' | 'Alternate'>('Primary');
  const [submitting, setSubmitting] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadData = async () => {
    try {
      const [idList, target] = await Promise.all([
        getIdentities().catch(() => []),
        getActiveTarget().catch(() => null)
      ]);
      setIdentities(idList || []);
      setActiveTarget(target);
    } catch (err) {
      console.error("Error loading identities:", err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    try {
      setSubmitting(true);
      setStatusMsg(null);
      const newId = await createIdentity({
        target_id: activeTarget?.id,
        name: name.trim(),
        role,
        auth_type: 'Bearer'
      });
      setName('');
      setStatusMsg({ type: 'success', text: `Identity "${newId.name}" (${newId.role}) registered successfully!` });
      await loadData();
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || err.message;
      setStatusMsg({ type: 'error', text: `Failed to create identity: ${errMsg}` });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (identityId: string, idName: string) => {
    if (!confirm(`Delete identity "${idName}"?`)) return;
    try {
      await deleteIdentity(identityId);
      setStatusMsg({ type: 'success', text: `Identity "${idName}" deleted.` });
      await loadData();
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || err.message;
      setStatusMsg({ type: 'error', text: `Failed to delete identity: ${errMsg}` });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-lg font-mono font-bold text-slate-100 flex items-center gap-2">
            <Users size={20} className="text-indigo-400" />
            <span>REGISTERED TARGET IDENTITIES</span>
          </h1>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Registered test identity actors (Primary vs. Alternate Shadow Identities)
          </p>
        </div>
        <button
          onClick={loadData}
          className="px-3 py-1.5 rounded bg-slate-900 text-cyan-300 border border-slate-700 hover:bg-slate-800 font-bold flex items-center gap-1.5 text-xs font-mono"
        >
          <RefreshCw size={13} />
          <span>Refresh</span>
        </button>
      </div>

      {statusMsg && (
        <div className={`p-3 rounded font-mono text-xs border ${
          statusMsg.type === 'success' ? 'bg-emerald-950/60 border-emerald-700 text-emerald-300' : 'bg-rose-950/60 border-rose-700 text-rose-300'
        } flex items-center justify-between`}>
          <span>{statusMsg.text}</span>
          <button onClick={() => setStatusMsg(null)} className="text-slate-400 hover:text-slate-200">×</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Create Identity Form */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-5">
          <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Plus size={16} className="text-cyan-400" />
            <span>REGISTER NEW IDENTITY</span>
          </h3>

          <form onSubmit={handleCreate} className="space-y-4 font-mono text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Identity Name</label>
              <input
                type="text"
                placeholder="e.g. Alice (Primary User) or Bob (Alternate)"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full p-2.5 rounded bg-slate-950 border border-slate-800 text-slate-200 focus:border-cyan-500 outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Role Type</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as 'Primary' | 'Alternate')}
                className="w-full p-2.5 rounded bg-slate-950 border border-slate-800 text-slate-200 focus:border-cyan-500 outline-none"
              >
                <option value="Primary">Primary (Original Workflow Actor)</option>
                <option value="Alternate">Alternate (Replay / Shadow Identity)</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={submitting || !name.trim()}
              className="w-full py-2.5 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-700/80 hover:bg-cyan-900/60 font-semibold transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Plus size={14} className={submitting ? 'animate-spin' : ''} />
              <span>{submitting ? 'Registering...' : 'Register Identity'}</span>
            </button>
          </form>
        </div>

        {/* Identity List */}
        <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-lg p-5">
          <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider mb-4">
            EXISTING REGISTERED IDENTITIES ({identities.length})
          </h3>

          <div className="space-y-3 font-mono text-xs">
            {identities.map((id) => (
              <div key={id.id} className="p-3.5 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="text-slate-100 font-bold flex items-center gap-2">
                    <span>{id.name}</span>
                    <Badge variant={id.role === 'Primary' ? 'cyan' : 'warning'}>{id.role}</Badge>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">ID: {id.id}</div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant="info">{id.auth_type}</Badge>
                  <button
                    onClick={() => handleDelete(id.id, id.name)}
                    className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-slate-900"
                    title="Delete identity"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
            {identities.length === 0 && (
              <div className="py-8 text-center text-slate-500 font-mono">
                No registered identities found. Register one using the form on the left.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

