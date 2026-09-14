import React, { useState, useEffect } from 'react';
import { CanonicalNode, CanonicalEdge, Dependency, Transaction, CanonicalOccurrenceSummary } from '../types';
import { Badge } from './Badge';
import { getTransaction } from '../api/client';
import { X, Code, Database, Tag, Link as LinkIcon, Lock, Layers, Server, FileText, ArrowRight, ShieldCheck, GitBranch, GitMerge } from 'lucide-react';

interface NodeInspectorProps {
  node: CanonicalNode | null;
  edge?: CanonicalEdge | null;
  dependencies: Dependency[];
  onClose: () => void;
  onJumpToLinearStep?: (stepIndex: number) => void;
}

export const NodeInspector: React.FC<NodeInspectorProps> = ({
  node,
  edge,
  dependencies,
  onClose,
  onJumpToLinearStep
}) => {
  const [selectedOccurrence, setSelectedOccurrence] = useState<CanonicalOccurrenceSummary | null>(null);
  const [txDetails, setTxDetails] = useState<Transaction | null>(null);
  const [loadingTx, setLoadingTx] = useState(false);

  useEffect(() => {
    if (node && node.occurrences.length > 0) {
      setSelectedOccurrence(node.occurrences[0]);
    } else {
      setSelectedOccurrence(null);
    }
  }, [node]);

  useEffect(() => {
    const txId = selectedOccurrence?.transaction_id || node?.transaction_id;
    if (txId) {
      setLoadingTx(true);
      getTransaction(txId)
        .then(tx => setTxDetails(tx))
        .catch(err => console.error("Error fetching transaction details", err))
        .finally(() => setLoadingTx(false));
    } else {
      setTxDetails(null);
    }
  }, [node, selectedOccurrence]);

  if (!node && !edge) return null;

  const nodeDeps = dependencies.filter(
    d => d.producer_transaction_id === txDetails?.id || d.consumer_transaction_id === txDetails?.id
  );

  const getMethodBadgeVariant = (method: string) => {
    switch (method.toUpperCase()) {
      case 'GET': return 'info';
      case 'POST': return 'success';
      case 'PUT': case 'PATCH': return 'warning';
      case 'DELETE': return 'danger';
      default: return 'secondary';
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[480px] bg-slate-950 border-l border-slate-800 shadow-2xl z-50 flex flex-col font-mono text-xs text-slate-300 animate-in slide-in-from-right duration-200">
      {/* Drawer Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90 backdrop-blur-md">
        <div className="flex items-center gap-2">
          {edge ? <LinkIcon size={18} className="text-amber-400" /> : <Layers size={18} className="text-cyan-400" />}
          <div>
            <h3 className="font-bold text-slate-100 uppercase text-xs tracking-wider">
              {edge ? 'CANONICAL EDGE EVIDENCE INSPECTOR' : 'CANONICAL STATE INSPECTOR'}
            </h3>
            <span className="text-[10px] text-slate-500 font-mono">ID: {edge ? edge.id : node?.id}</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
        >
          <X size={16} />
        </button>
      </div>

      {/* Content Scroll Area */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {edge ? (
          /* Edge Evidence Mode */
          <div className="space-y-4">
            <div className="p-3.5 rounded-lg bg-amber-950/30 border border-amber-800/60 space-y-2">
              <div className="flex items-center justify-between">
                <Badge variant={edge.edge_type === 'DEPENDENCY_TRANSITION' ? 'warning' : 'info'}>
                  {edge.edge_type}
                </Badge>
                <span className="text-xs font-bold text-amber-300 font-mono">
                  Cardinality: {edge.cardinality || '1->1'}
                </span>
              </div>
              <div className="text-[11px] text-slate-300 space-y-1 pt-2 border-t border-amber-900/40">
                <div>Source Node: <strong className="text-cyan-400">{edge.source}</strong></div>
                <div>Target Node: <strong className="text-emerald-400">{edge.target}</strong></div>
              </div>
            </div>

            {/* Edge Bindings Payload */}
            <div>
              <h4 className="font-bold text-slate-200 uppercase text-[11px] mb-2 flex items-center gap-1.5">
                <LinkIcon size={14} className="text-amber-400" />
                <span>PARAMETER BINDINGS ({edge.bindings?.length || (edge.dependency_details ? 1 : 0)})</span>
              </h4>
              {edge.bindings && edge.bindings.length > 0 ? (
                <div className="space-y-2">
                  {edge.bindings.map((b, idx) => (
                    <div key={idx} className="p-3 rounded bg-slate-900 border border-slate-800 text-[11px] space-y-1">
                      <div className="flex items-center justify-between text-slate-400">
                        <span>Producer Path: <strong className="text-amber-300">{b.producer_path}</strong></span>
                        <span className="text-[10px] text-slate-500">{b.producer_location}</span>
                      </div>
                      <div className="flex items-center justify-between text-slate-400">
                        <span>Consumer Param: <strong className="text-cyan-300">{b.consumer_parameter}</strong></span>
                        <span className="text-[10px] text-slate-500">{b.consumer_location}</span>
                      </div>
                      <div className="pt-1 text-emerald-400 font-bold border-t border-slate-800/80">
                        Extracted Value: <code>{b.extracted_value}</code>
                      </div>
                    </div>
                  ))}
                </div>
              ) : edge.dependency_details ? (
                <div className="p-3 rounded bg-slate-900 border border-slate-800 text-[11px] space-y-1">
                  <div className="text-amber-300 font-bold">
                    Parameter: {edge.dependency_details.parameter}
                  </div>
                  <div className="text-slate-400">
                    Producer: {edge.dependency_details.producer_field} → Consumer: {edge.dependency_details.consumer_field}
                  </div>
                  <div className="text-emerald-400 font-bold pt-1 border-t border-slate-800">
                    Value: {edge.dependency_details.extracted_value}
                  </div>
                </div>
              ) : (
                <div className="p-3 text-slate-500 rounded bg-slate-900/50 border border-slate-800 text-center">
                  Sequence step transition (No data dependency payload)
                </div>
              )}
            </div>

            {/* Evidence & Confidence Metrics */}
            <div className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
              <h4 className="font-bold text-slate-200 uppercase text-[11px] flex items-center gap-1.5">
                <ShieldCheck size={14} className="text-emerald-400" />
                <span>EVIDENCE METRICS</span>
              </h4>
              <div className="text-[11px] text-slate-300 space-y-1">
                <div>Reason: <span className="text-slate-400">{edge.evidence?.reason || 'Chronological or value transition'}</span></div>
                <div>Confidence Score: <strong className="text-emerald-400">{Math.round((edge.confidence || 1.0) * 100)}%</strong></div>
                <div>Step Distance: <strong className="text-cyan-400">{edge.step_distance || 1} step(s)</strong></div>
              </div>
            </div>
          </div>
        ) : node ? (
          /* Node Inspection Mode */
          <>
            {/* Node Overview Card */}
            <div className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <Badge variant={getMethodBadgeVariant(node.method)}>{node.method}</Badge>
                <span className="text-xs font-bold text-cyan-400">{node.path_template}</span>
              </div>
              <div className="text-[11px] text-slate-400 flex items-center gap-2 pt-1 border-t border-slate-800">
                <Tag size={12} className="text-slate-500" />
                <span>Operation ID: <strong className="text-slate-200">{node.operation_id || 'unmapped'}</strong></span>
              </div>
              {node.resource_identifier && (
                <div className="text-[11px] text-amber-300 font-bold flex items-center gap-2 pt-1">
                  <Database size={12} />
                  <span>Inferred Resource: {node.resource_type}:{node.resource_identifier}</span>
                </div>
              )}
            </div>

            {/* Topographic Metrics */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded bg-slate-900/60 border border-slate-800">
                <span className="text-slate-500 text-[10px] uppercase block">In-Degree (Predecessors)</span>
                <span className="text-sm font-bold text-cyan-400">{node.in_degree}</span>
              </div>
              <div className="p-3 rounded bg-slate-900/60 border border-slate-800">
                <span className="text-slate-500 text-[10px] uppercase block">Out-Degree (Successors)</span>
                <span className="text-sm font-bold text-emerald-400">{node.out_degree}</span>
              </div>
            </div>

            {/* Execution Occurrences Hierarchy */}
            <div>
              <h4 className="font-bold text-slate-200 uppercase text-[11px] mb-2 flex items-center justify-between">
                <span className="flex items-center gap-1.5">
                  <FileText size={14} className="text-indigo-400" />
                  <span>EXECUTION OCCURRENCES ({node.occurrences.length})</span>
                </span>
                {selectedOccurrence && onJumpToLinearStep && (
                  <button
                    onClick={() => onJumpToLinearStep(selectedOccurrence.occurrence_index)}
                    className="text-[10px] text-cyan-400 hover:text-cyan-300 font-bold flex items-center gap-1 bg-slate-900 px-2 py-0.5 rounded border border-cyan-800"
                  >
                    <span>View Step #{selectedOccurrence.occurrence_index}</span>
                    <ArrowRight size={10} />
                  </button>
                )}
              </h4>
              <div className="space-y-1.5 max-h-36 overflow-y-auto">
                {node.occurrences.map((occ, idx) => {
                  const isSelectedOcc = selectedOccurrence?.transaction_id === occ.transaction_id;
                  return (
                    <div
                      key={idx}
                      onClick={() => setSelectedOccurrence(occ)}
                      className={`p-2 rounded cursor-pointer transition-all border text-[11px] flex items-center justify-between ${
                        isSelectedOcc
                          ? 'bg-cyan-950/80 border-cyan-500 text-cyan-200 font-bold'
                          : 'bg-slate-900 border-slate-800 hover:border-slate-700 text-slate-300'
                      }`}
                    >
                      <span>Occurrence #{occ.occurrence_index} ({occ.transaction_id.slice(0, 8)})</span>
                      <span className="text-emerald-400 font-bold">HTTP {occ.res_status}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Real HTTP Request Payload Details (Redacted Secrets) */}
            <div>
              <h4 className="font-bold text-slate-200 uppercase text-[11px] mb-2 flex items-center gap-1.5">
                <Code size={14} className="text-cyan-400" />
                <span>REQUEST METADATA (CREDENTIAL REDACTED)</span>
              </h4>
              {loadingTx ? (
                <div className="p-4 text-center text-slate-500 animate-pulse">Loading HTTP details...</div>
              ) : txDetails ? (
                <div className="space-y-2">
                  <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 text-[10px] block mb-1 uppercase">Request URL</span>
                    <span className="text-slate-200 font-bold break-all">{txDetails.url}</span>
                  </div>

                  {txDetails.req_headers && (
                    <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                      <span className="text-slate-500 text-[10px] block mb-1 uppercase">Headers (Redacted)</span>
                      <pre className="text-[10px] text-cyan-300 overflow-x-auto max-h-24 font-mono">
                        {JSON.stringify(txDetails.req_headers, null, 2)}
                      </pre>
                    </div>
                  )}

                  {txDetails.req_body && (
                    <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                      <span className="text-slate-500 text-[10px] block mb-1 uppercase">Request Body</span>
                      <pre className="text-[10px] text-emerald-300 overflow-x-auto max-h-24 font-mono">
                        {txDetails.req_body}
                      </pre>
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-3 text-slate-500 text-center">No raw HTTP transaction loaded</div>
              )}
            </div>

            {/* Real Response Payload Details */}
            {txDetails && (
              <div>
                <h4 className="font-bold text-slate-200 uppercase text-[11px] mb-2 flex items-center gap-1.5">
                  <Server size={14} className="text-emerald-400" />
                  <span>RESPONSE METADATA</span>
                </h4>
                <div className="p-2.5 rounded bg-slate-900 border border-slate-800 space-y-2">
                  <div>
                    <span className="text-slate-500 text-[10px] block uppercase">Status Code</span>
                    <span className="text-emerald-400 font-bold">HTTP {txDetails.res_status}</span>
                  </div>
                  {txDetails.res_body && (
                    <div>
                      <span className="text-slate-500 text-[10px] block uppercase mb-1">Response Body</span>
                      <pre className="text-[10px] text-cyan-300 overflow-x-auto max-h-32 font-mono">
                        {txDetails.res_body}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Dynamic Parameter Dependencies */}
            {nodeDeps.length > 0 && (
              <div>
                <h4 className="font-bold text-slate-200 uppercase text-[11px] mb-2 flex items-center gap-1.5">
                  <LinkIcon size={14} className="text-amber-400" />
                  <span>PARAMETER DEPENDENCIES ({nodeDeps.length})</span>
                </h4>
                <div className="space-y-2">
                  {nodeDeps.map(d => (
                    <div key={d.id} className="p-2.5 rounded bg-amber-950/40 border border-amber-800/60 text-[11px] space-y-1">
                      <div className="text-amber-300 font-bold">{d.dependency_type}</div>
                      <div className="text-slate-400 text-[10px]">
                        Extracted Value: <strong className="text-amber-400">{d.extracted_value}</strong>
                      </div>
                      <div className="text-slate-500 text-[10px]">
                        Field: {d.producer_field_path} → {d.consumer_field_location}:{d.consumer_field_name}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : null}
      </div>

      {/* Footer Security Badge */}
      <div className="p-3 border-t border-slate-800 bg-slate-900 text-[10px] text-slate-400 flex items-center gap-2">
        <Lock size={12} className="text-emerald-400" />
        <span>Plain-text authorization credentials redacted under Credential Isolation Policy.</span>
      </div>
    </div>
  );
};
