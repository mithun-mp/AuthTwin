import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'warning' | 'danger' | 'info' | 'success' | 'cyan' | 'violet';
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'primary' }) => {
  const styles: Record<string, string> = {
    primary: 'bg-cyan-950/80 text-cyan-400 border-cyan-700/50 shadow-sm shadow-cyan-950',
    cyan: 'bg-cyan-950/80 text-cyan-300 border-cyan-600/60 shadow-sm shadow-cyan-950',
    violet: 'bg-violet-950/80 text-violet-300 border-violet-600/60 shadow-sm shadow-violet-950',
    secondary: 'bg-slate-800/80 text-slate-300 border-slate-700',
    warning: 'bg-amber-950/80 text-amber-300 border-amber-600/60 shadow-sm shadow-amber-950',
    danger: 'bg-rose-950/80 text-rose-300 border-rose-600/60 shadow-sm shadow-rose-950',
    info: 'bg-indigo-950/80 text-indigo-300 border-indigo-600/60 shadow-sm shadow-indigo-950',
    success: 'bg-emerald-950/80 text-emerald-300 border-emerald-600/60 shadow-sm shadow-emerald-950',
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-semibold border tracking-wide uppercase ${styles[variant]}`}>
      {children}
    </span>
  );
};
