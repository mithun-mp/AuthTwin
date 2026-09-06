import React, { useEffect, useState } from 'react';
import { Dependency } from '../types';
import { getDependencies } from '../api/client';
import { Badge } from '../components/Badge';
import { Network, Link as LinkIcon } from 'lucide-react';

export const Dependencies: React.FC = () => {
  const [dependencies, setDependencies] = useState<Dependency[]>([]);

  useEffect(() => {
    getDependencies().then(data => setDependencies(data)).catch(console.error);
  }, []);

  return (
    <div className="space-y-6 font-mono text-xs">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Network size={20} className="text-amber-400" />
            <span>PRODUCER-CONSUMER PARAMETER DEPENDENCIES</span>
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Dynamic dynamic links between output payload fields and downstream request parameters
          </p>
        </div>
        <span className="text-slate-500">{dependencies.length} Dependencies Detected</span>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
            <tr>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Producer Field</th>
              <th className="px-4 py-3">Consumer Param</th>
              <th className="px-4 py-3">Location</th>
              <th className="px-4 py-3">Extracted Value</th>
              <th className="px-4 py-3">Confidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {dependencies.map((dep) => (
              <tr key={dep.id} className="hover:bg-slate-800/40">
                <td className="px-4 py-3">
                  <Badge variant="warning">{dep.dependency_type}</Badge>
                </td>
                <td className="px-4 py-3 text-cyan-400">{dep.producer_field_path}</td>
                <td className="px-4 py-3 text-amber-400">{dep.consumer_field_name}</td>
                <td className="px-4 py-3 font-semibold">{dep.consumer_field_location}</td>
                <td className="px-4 py-3">
                  <code className="p-1 rounded bg-slate-950 text-slate-200 border border-slate-800">
                    {dep.extracted_value}
                  </code>
                </td>
                <td className="px-4 py-3 text-emerald-400">{(dep.confidence * 100).toFixed(0)}%</td>
              </tr>
            ))}
            {dependencies.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                  No producer-consumer dependencies detected yet. Import a HAR file containing multi-step workflow operations.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
