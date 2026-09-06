import React, { useState } from 'react';
import { Terminal, ChevronUp, ChevronDown, Trash2, CheckCircle2, Shield, AlertCircle } from 'lucide-react';

export interface LogEntry {
  id: string;
  timestamp: string;
  type: 'INFO' | 'SUCCESS' | 'WARN' | 'SECURITY';
  module: string;
  message: string;
}

interface TerminalConsoleProps {
  logs: LogEntry[];
  onClear?: () => void;
}

export const TerminalConsole: React.FC<TerminalConsoleProps> = ({ logs, onClear }) => {
  const [isOpen, setIsOpen] = useState(false);

  const getLogBadge = (type: string) => {
    switch (type) {
      case 'SUCCESS': return <span className="text-emerald-400 font-bold">[SUCCESS]</span>;
      case 'SECURITY': return <span className="text-cyan-400 font-bold">[SECURITY]</span>;
      case 'WARN': return <span className="text-amber-400 font-bold">[WARNING]</span>;
      default: return <span className="text-indigo-400 font-bold">[INFO]</span>;
    }
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 bg-[#070a11]/95 border-t border-slate-800/90 shadow-2xl backdrop-blur-md transition-all font-mono text-xs">
      {/* Console Bar Header */}
      <div className="px-4 py-2 flex items-center justify-between border-b border-slate-800/60 bg-slate-950/60">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 text-slate-300 hover:text-cyan-400 font-semibold transition-colors text-xs"
        >
          <Terminal size={14} className="text-cyan-400" />
          <span>AUTHTWIN AUDIT TELEMETRY STREAM</span>
          <span className="px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-400 border border-cyan-800 text-[10px]">
            {logs.length} EVENTS
          </span>
          {isOpen ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
        </button>

        <div className="flex items-center gap-3 text-[11px] text-slate-400">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <CheckCircle2 size={12} />
            <span>CREDENTIAL ISOLATION GUARANTEED</span>
          </span>
          {onClear && (
            <button onClick={onClear} className="text-slate-500 hover:text-slate-300 transition-colors p-1">
              <Trash2 size={12} />
            </button>
          )}
        </div>
      </div>

      {/* Expandable Console Logs Body */}
      {isOpen && (
        <div className="p-3 max-h-56 overflow-y-auto space-y-1.5 bg-[#05070d] text-slate-300 text-[11px] font-mono">
          {logs.map((log) => (
            <div key={log.id} className="flex items-start gap-2 hover:bg-slate-900/50 p-1 rounded transition-colors">
              <span className="text-slate-500 shrink-0">{log.timestamp}</span>
              {getLogBadge(log.type)}
              <span className="text-slate-400 font-semibold uppercase shrink-0">[{log.module}]</span>
              <span className="text-slate-200 break-all">{log.message}</span>
            </div>
          ))}
          {logs.length === 0 && (
            <div className="text-slate-600 text-center py-3 italic">
              [SYSTEM] Telemetry log stream initialized. Awaiting workflow events...
            </div>
          )}
        </div>
      )}
    </div>
  );
};
