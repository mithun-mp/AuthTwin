import React, { useState } from 'react';
import {
  Shield, Activity, Users, GitBranch, Network, FileCode,
  Layers, Lock, Database, ArrowRight, Upload, Terminal, CheckCircle2, Cpu, Radio
} from 'lucide-react';
import { TerminalConsole, LogEntry } from './TerminalConsole';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  logs?: LogEntry[];
}

export const Layout: React.FC<LayoutProps> = ({ children, activeTab, setActiveTab, logs = [] }) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: Activity, tag: 'SOC' },
    { id: 'sandbox', label: 'Target Interceptor', icon: Radio, tag: 'LIVE' },
    { id: 'traffic', label: 'HTTP Traffic', icon: Layers, tag: 'LOGS' },
    { id: 'identities', label: 'Identities', icon: Users, tag: 'ACTORS' },
    { id: 'sessions', label: 'Sessions', icon: Database, tag: 'AUTH' },
    { id: 'openapi', label: 'OpenAPI Models', icon: FileCode, tag: 'SPEC' },
    { id: 'dependencies', label: 'Dependencies', icon: Network, tag: 'DATA' },
    { id: 'workflows', label: 'Workflows & WSG', icon: GitBranch, tag: 'GRAPH' },
    { id: 'shadow', label: 'Shadow Workflows', icon: Lock, tag: 'MODEL' },
  ];

  return (
    <div className="min-h-screen bg-[#070a11] text-slate-200 flex flex-col font-sans selection:bg-cyan-500/30">
      {/* Top Cyber Command Header */}
      <header className="h-14 bg-slate-950/90 border-b border-slate-800 px-5 flex items-center justify-between sticky top-0 z-50 backdrop-blur-md">
        {/* Brand & Project Identity */}
        <div className="flex items-center gap-3">
          <div className="p-1.5 rounded-lg bg-cyan-950/80 border border-cyan-500/50 text-cyan-400 shadow-md shadow-cyan-950">
            <Shield size={20} className="animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-display font-extrabold tracking-wider text-sm text-slate-100">AUTHTWIN</span>
              <span className="text-[9px] font-mono font-semibold px-2 py-0.5 rounded bg-cyan-950/90 text-cyan-300 border border-cyan-700/60 shadow-sm">
                DWA-SSA WORKSTATION v1.0
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-mono hidden sm:block">
              Deterministic Workflow-Aware Shadow-Session Architecture
            </p>
          </div>
        </div>

        {/* Global Operational Security Badges */}
        <div className="flex items-center gap-3 text-xs font-mono">
          <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-md bg-slate-900/90 border border-slate-800 text-slate-300">
            <Cpu size={14} className="text-cyan-400" />
            <span className="text-slate-400">ENGINE:</span>
            <span className="text-emerald-400 font-bold">ONLINE</span>
          </div>

          <div className="flex items-center gap-2 px-2.5 py-1 rounded-md bg-amber-950/50 border border-amber-800/60 text-amber-300">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping"></span>
            <span className="font-bold text-[11px]">M1: MODEL ONLY</span>
          </div>
        </div>
      </header>

      {/* Main Layout Container */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Command Navigation Rail */}
        <aside className="w-60 bg-slate-950/60 border-r border-slate-800/90 p-3 flex flex-col justify-between shrink-0">
          <div className="space-y-1">
            <div className="px-3 py-2 text-[10px] font-mono font-bold text-slate-500 uppercase tracking-widest flex items-center justify-between">
              <span>WORKSTATION MODULES</span>
              <span className="text-cyan-500">M1</span>
            </div>

            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-mono font-medium transition-all ${
                    isActive
                      ? 'bg-cyan-950/80 text-cyan-200 border border-cyan-500/50 font-bold shadow-md shadow-cyan-950/40'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/70 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon size={16} className={isActive ? 'text-cyan-400' : 'text-slate-500'} />
                    <span>{item.label}</span>
                  </div>
                  <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded ${
                    isActive ? 'bg-cyan-900 text-cyan-200' : 'bg-slate-900 text-slate-500'
                  }`}>
                    {item.tag}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Security Invariant Card */}
          <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 text-[11px] font-mono text-slate-400 space-y-2">
            <div className="flex items-center gap-1.5 text-cyan-400 font-bold text-[11px]">
              <CheckCircle2 size={14} />
              <span>ISOLATION GUARANTEE</span>
            </div>
            <p className="text-[10px] text-slate-400 leading-relaxed">
              Shadow Workflows explicitly strip all authentication tokens. No HTTP requests are replayed in M1.
            </p>
          </div>
        </aside>

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto p-6 bg-[#070a11] pb-16">
          {children}
        </main>
      </div>

      {/* Audit Telemetry Console Drawer */}
      <TerminalConsole logs={logs} />
    </div>
  );
};
