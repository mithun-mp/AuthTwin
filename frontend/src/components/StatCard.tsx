import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon: LucideIcon;
  accentColor?: string;
  glowColor?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  accentColor = 'text-cyan-400',
  glowColor = 'hover:border-cyan-500/50'
}) => {
  return (
    <div className={`glass-panel rounded-lg p-4 transition-all duration-300 ${glowColor} hover:shadow-lg relative overflow-hidden group`}>
      {/* Background Decorative Accent Line */}
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-cyan-500/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
      
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-widest">{title}</span>
        <div className={`p-2 rounded-lg bg-slate-900/90 border border-slate-800/80 ${accentColor} shadow-inner`}>
          <Icon size={16} />
        </div>
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-mono font-bold text-slate-100 tracking-tight group-hover:text-cyan-300 transition-colors">
          {value}
        </span>
        {subtitle && (
          <span className="text-[10px] text-amber-400 font-mono font-semibold px-1.5 py-0.5 rounded bg-amber-950/60 border border-amber-800/60">
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
};
