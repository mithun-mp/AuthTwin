import React, { useEffect, useState } from 'react';
import { Transaction } from '../types';
import { getTransactions } from '../api/client';
import { Badge } from '../components/Badge';
import { Layers, Eye, Code, X } from 'lucide-react';

export const Traffic: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [selectedTx, setSelectedTx] = useState<Transaction | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTransactions()
      .then(data => setTransactions(data))
      .catch(err => console.error("Error loading transactions:", err))
      .finally(() => setLoading(false));
  }, []);

  const getStatusBadge = (status: number) => {
    if (status >= 200 && status < 300) return <Badge variant="success">{status}</Badge>;
    if (status >= 300 && status < 400) return <Badge variant="info">{status}</Badge>;
    if (status >= 400 && status < 500) return <Badge variant="warning">{status}</Badge>;
    return <Badge variant="danger">{status}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-lg font-mono font-bold text-slate-100 flex items-center gap-2">
            <Layers size={20} className="text-emerald-400" />
            <span>NORMALIZED HTTP TRAFFIC LOG</span>
          </h1>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Ingested transactions with credential-redacted headers
          </p>
        </div>
        <span className="text-xs font-mono text-slate-500">{transactions.length} Transactions Ingested</span>
      </div>

      {/* Transactions Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-lg overflow-hidden">
        <table className="w-full text-left font-mono text-xs">
          <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase text-[10px] tracking-wider">
            <tr>
              <th className="px-4 py-3">Time</th>
              <th className="px-4 py-3">Method</th>
              <th className="px-4 py-3">Path</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Operation ID</th>
              <th className="px-4 py-3 text-right">Inspect</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {transactions.map((tx) => (
              <tr key={tx.id} className="hover:bg-slate-800/40 transition-colors">
                <td className="px-4 py-3 text-slate-500">{new Date(tx.timestamp).toLocaleTimeString()}</td>
                <td className="px-4 py-3">
                  <Badge variant={tx.method === 'GET' ? 'info' : tx.method === 'POST' ? 'success' : 'warning'}>
                    {tx.method}
                  </Badge>
                </td>
                <td className="px-4 py-3 font-medium text-slate-200">{tx.path}</td>
                <td className="px-4 py-3">{getStatusBadge(tx.res_status)}</td>
                <td className="px-4 py-3 text-cyan-400">{tx.operation_id || 'unmapped'}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => setSelectedTx(tx)}
                    className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                  >
                    <Eye size={14} />
                  </button>
                </td>
              </tr>
            ))}
            {transactions.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                  No HTTP transactions ingested yet. Import a HAR file from Overview screen.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Transaction Inspection Modal */}
      {selectedTx && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-950 border border-slate-800 rounded-lg max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2 font-mono text-sm font-bold text-slate-100">
                <Badge variant="info">{selectedTx.method}</Badge>
                <span>{selectedTx.url}</span>
              </div>
              <button onClick={() => setSelectedTx(null)} className="text-slate-400 hover:text-slate-200">
                <X size={18} />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-6 font-mono text-xs">
              {/* Request Headers & Body */}
              <div className="space-y-2">
                <h4 className="text-slate-400 font-semibold uppercase text-[10px]">Request Headers (Redacted)</h4>
                <pre className="p-3 rounded bg-slate-900 border border-slate-800 text-slate-300 overflow-x-auto">
                  {JSON.stringify(selectedTx.req_headers, null, 2)}
                </pre>
              </div>

              {selectedTx.req_body && (
                <div className="space-y-2">
                  <h4 className="text-slate-400 font-semibold uppercase text-[10px]">Request Body</h4>
                  <pre className="p-3 rounded bg-slate-900 border border-slate-800 text-cyan-300 overflow-x-auto">
                    {selectedTx.req_body}
                  </pre>
                </div>
              )}

              {/* Response Headers & Body */}
              <div className="space-y-2">
                <h4 className="text-slate-400 font-semibold uppercase text-[10px]">Response Body ({selectedTx.res_status})</h4>
                <pre className="p-3 rounded bg-slate-900 border border-slate-800 text-emerald-300 overflow-x-auto">
                  {selectedTx.res_body || '(empty response body)'}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
