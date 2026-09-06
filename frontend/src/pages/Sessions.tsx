import React, { useEffect, useState } from 'react';
import { Session } from '../types';
import { getSessions } from '../api/client';
import { Badge } from '../components/Badge';
import { Database, Shield } from 'lucide-react';

export const Sessions: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    getSessions().then(data => setSessions(data)).catch(console.error);
  }, []);

  return (
    <div className="space-y-6 font-mono text-xs">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Database size={20} className="text-purple-400" />
            <span>AUTHENTICATED LOGICAL SESSIONS</span>
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Grouped interaction journeys with token fingerprints
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {sessions.map((s) => (
          <div key={s.id} className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
            <div>
              <div className="text-slate-100 font-bold text-sm">{s.name}</div>
              <div className="text-slate-500 text-[11px] mt-1 space-x-3">
                <span>Fingerprint: {s.token_fingerprint ? s.token_fingerprint.slice(0, 10) : 'none'}</span>
                <span>Started: {new Date(s.started_at).toLocaleString()}</span>
              </div>
            </div>
            <Badge variant="success">{s.status}</Badge>
          </div>
        ))}
        {sessions.length === 0 && (
          <div className="p-8 text-center text-slate-500 bg-slate-900 border border-slate-800 rounded-lg">
            No active sessions recorded. Import a HAR file to generate sessions.
          </div>
        )}
      </div>
    </div>
  );
};
