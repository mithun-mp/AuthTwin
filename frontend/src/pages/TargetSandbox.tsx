import React, { useState, useEffect } from 'react';
import {
  verifyTargetServer, startLiveRecording, pauseLiveRecording, resumeLiveRecording,
  clearLiveBuffer, restartLiveRecording, stopLiveRecording, getLiveBuffer,
  getActiveTarget, setActiveTarget, getIdentities, createIdentity, getWorkflowGraph, getWorkflows
} from '../api/client';
import { Identity, WorkflowGraphResponse } from '../types';
import { AUTHTWIN_CONFIG } from '../config';
import { Badge } from '../components/Badge';
import { GraphVisualizer } from '../components/GraphVisualizer';
import {
  Globe, Radio, Play, Pause, Square, CheckCircle2, AlertCircle, RefreshCw, ExternalLink,
  Layers, ArrowRight, Zap, Code, Save, User, Trash2, RotateCcw, GitBranch
} from 'lucide-react';

interface TargetSandboxProps {
  onLogEvent?: (type: 'INFO' | 'SUCCESS' | 'WARN' | 'SECURITY', module: string, msg: string) => void;
  onNavigateToWorkflows?: () => void;
}

export const TargetSandbox: React.FC<TargetSandboxProps> = ({ onLogEvent, onNavigateToWorkflows }) => {
  const [targetUrl, setTargetUrl] = useState('');
  const [identities, setIdentities] = useState<Identity[]>([]);
  const [selectedIdentityId, setSelectedIdentityId] = useState<string>('');
  const [savingTarget, setSavingTarget] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<any>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [capturedTxs, setCapturedTxs] = useState<any[]>([]);
  const [buildingGraph, setBuildingGraph] = useState(false);
  const [graphMessage, setGraphMessage] = useState<string | null>(null);
  const [iframeKey, setIframeKey] = useState<number>(Date.now());
  const [embeddedGraphData, setEmbeddedGraphData] = useState<WorkflowGraphResponse | null>(null);

  // Load project target configuration, identities, live buffer, and latest workflow graph
  const syncState = async () => {
    try {
      const [target, idList, buf, wfList] = await Promise.all([
        getActiveTarget().catch(() => null),
        getIdentities().catch(() => []),
        getLiveBuffer().catch(() => null),
        getWorkflows().catch(() => [])
      ]);

      if (target?.base_url) {
        setTargetUrl(target.base_url);
      } else {
        setTargetUrl('');
      }
      setIdentities(idList || []);
      if (idList && idList.length > 0 && !selectedIdentityId) {
        setSelectedIdentityId(idList[0].id);
      }
      setIsRecording(Boolean(buf?.is_recording));
      setIsPaused(Boolean(buf?.is_paused));
      setCapturedTxs(buf?.transactions || []);

      if (wfList && wfList.length > 0) {
        try {
          const latestGraph = await getWorkflowGraph(wfList[0].id);
          setEmbeddedGraphData(latestGraph);
        } catch (e) {
          console.error("Failed to load latest graph preview", e);
        }
      }
    } catch (err) {
      console.error("Failed to sync project target state", err);
    }
  };

  useEffect(() => {
    syncState();
  }, []);

  // Poll live recording buffer every 1 second when recording is active
  useEffect(() => {
    let interval: any = null;
    if (isRecording) {
      interval = setInterval(async () => {
        try {
          const buf = await getLiveBuffer();
          setIsRecording(Boolean(buf.is_recording));
          setIsPaused(Boolean(buf.is_paused));
          if (buf.transactions) {
            setCapturedTxs(buf.transactions);
          }
        } catch (err) {
          console.error("Failed to poll live buffer", err);
        }
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRecording]);

  const handleSaveTarget = async () => {
    if (!targetUrl.trim()) return;
    try {
      setSavingTarget(true);
      const updated = await setActiveTarget(targetUrl);
      setTargetUrl(updated.base_url);
      setIframeKey(Date.now());
      setVerifyResult({
        target_url: updated.base_url,
        is_active: true,
        message: `Active Target saved: ${updated.base_url}`
      });
      onLogEvent?.('SUCCESS', 'TARGET_CONFIG', `Configured target application address: ${updated.base_url}`);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message;
      setVerifyResult({
        target_url: targetUrl,
        is_active: false,
        message: `Target Config Error: ${msg}`
      });
      onLogEvent?.('WARN', 'TARGET_CONFIG', msg);
    } finally {
      setSavingTarget(false);
    }
  };

  const handleVerify = async () => {
    if (!targetUrl.trim()) {
      setVerifyResult({
        target_url: targetUrl,
        is_active: false,
        message: 'Please enter a valid target server address.'
      });
      return;
    }
    try {
      setVerifying(true);
      setVerifyResult(null);
      const res = await verifyTargetServer(targetUrl);
      setVerifyResult(res);
      if (res.is_active) {
        onLogEvent?.('SUCCESS', 'TARGET_PROBE', res.message);
      } else {
        onLogEvent?.('WARN', 'TARGET_PROBE', res.message);
      }
    } catch (err: any) {
      const detailMsg = err.response?.data?.detail || err.message;
      setVerifyResult({
        target_url: targetUrl,
        is_active: false,
        message: `Probe Validation Error: ${detailMsg}`
      });
      onLogEvent?.('WARN', 'TARGET_PROBE', detailMsg);
    } finally {
      setVerifying(false);
    }
  };

  const startRecordingSession = async () => {
    if (!selectedIdentityId) {
      onLogEvent?.('WARN', 'INTERCEPTOR', 'Cannot start recording: No identity selected or configured.');
      alert('Please select or create an Identity before starting recording.');
      return;
    }
    try {
      setGraphMessage(null);
      setCapturedTxs([]);
      await startLiveRecording(selectedIdentityId);
      setIsRecording(true);
      setIsPaused(false);
      setIframeKey(Date.now());
      onLogEvent?.('SECURITY', 'INTERCEPTOR', `Started AuthTwin live proxy recording session`);
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || err.message;
      onLogEvent?.('WARN', 'INTERCEPTOR', `Failed to start recording: ${errMsg}`);
    }
  };

  const pauseRecordingSession = async () => {
    try {
      await pauseLiveRecording();
      setIsRecording(false);
      setIsPaused(true);
      onLogEvent?.('INFO', 'INTERCEPTOR', `Paused live proxy recording session`);
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || err.message;
      onLogEvent?.('WARN', 'INTERCEPTOR', `Failed to pause recording: ${errMsg}`);
    }
  };

  const resumeRecordingSession = async () => {
    try {
      await resumeLiveRecording();
      setIsRecording(true);
      setIsPaused(false);
      onLogEvent?.('INFO', 'INTERCEPTOR', `Resumed live proxy recording session`);
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || err.message;
      onLogEvent?.('WARN', 'INTERCEPTOR', `Failed to resume recording: ${errMsg}`);
    }
  };

  const clearBufferSession = async () => {
    try {
      await clearLiveBuffer();
      setIsRecording(false);
      setIsPaused(false);
      setCapturedTxs([]);
      onLogEvent?.('INFO', 'INTERCEPTOR', `Cleared live interceptor buffer memory`);
    } catch (err: any) {
      console.error("Failed to clear live buffer", err);
    }
  };

  const restartRecordingSession = async () => {
    if (!selectedIdentityId) {
      alert('Please select an Identity before restarting recording.');
      return;
    }
    try {
      setGraphMessage(null);
      setCapturedTxs([]);
      await restartLiveRecording(selectedIdentityId);
      setIsRecording(true);
      setIsPaused(false);
      setIframeKey(Date.now());
      onLogEvent?.('SECURITY', 'INTERCEPTOR', `Restarted live proxy recording session with fresh buffer`);
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || err.message;
      onLogEvent?.('WARN', 'INTERCEPTOR', `Failed to restart recording: ${errMsg}`);
    }
  };

  const stopAndBuildGraph = async () => {
    try {
      setBuildingGraph(true);
      const res = await stopLiveRecording();
      setIsRecording(false);
      setIsPaused(false);

      if (res.imported_count > 0 && res.session_id) {
        const msg = `Workflow State Graph Generated! Intercepted ${res.imported_count} live transactions into Session #${res.session_id.slice(0, 8)}.`;
        setGraphMessage(msg);
        onLogEvent?.('SUCCESS', 'WSG_GEN', msg);

        // Fetch new workflow graph directly for embedded visualizer preview
        try {
          const wfList = await getWorkflows();
          if (wfList && wfList.length > 0) {
            const newGraph = await getWorkflowGraph(wfList[0].id);
            setEmbeddedGraphData(newGraph);
          }
        } catch (gErr) {
          console.error("Failed to load newly generated workflow graph", gErr);
        }
      } else {
        const msg = `Recording stopped. No live transactions were captured.`;
        setGraphMessage(msg);
        onLogEvent?.('WARN', 'INTERCEPTOR', msg);
      }
    } catch (err: any) {
      const errMsg = `Graph Generation Failed: ${err.response?.data?.detail || err.message}`;
      setGraphMessage(errMsg);
      onLogEvent?.('WARN', 'WSG_FAIL', errMsg);
    } finally {
      setBuildingGraph(false);
    }
  };

  const handleQuickCreateIdentity = async () => {
    const name = prompt("Enter Identity Name (e.g. Alice Primary or Bob Alternate):", "Alice (Primary)");
    if (!name || !name.trim()) return;
    try {
      const newId = await createIdentity({
        name: name.trim(),
        role: 'Primary',
        auth_type: 'Bearer'
      });
      const updatedList = await getIdentities();
      setIdentities(updatedList || []);
      setSelectedIdentityId(newId.id);
      onLogEvent?.('SUCCESS', 'IDENTITY', `Registered new identity: ${newId.name}`);
    } catch (err: any) {
      alert("Failed to register identity: " + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="space-y-6 font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Radio size={20} className="text-cyan-400 animate-pulse" />
            <span>LIVE TARGET INTERCEPTOR & WORKFLOW BUILDER</span>
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Probe local software address, capture live API traffic, and build Workflow State Graphs
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIframeKey(Date.now())}
            className="px-3 py-1.5 rounded bg-slate-900 text-cyan-300 border border-slate-700 hover:bg-slate-800 font-bold flex items-center gap-1.5 transition-all text-xs"
          >
            <RefreshCw size={13} />
            <span>Refresh Workspace</span>
          </button>
        </div>
      </div>


      {/* Step 1: Target Probe & Server Verification */}
      <div className="glass-panel rounded-lg p-5 space-y-4">
        <h3 className="font-bold text-slate-200 uppercase tracking-wider text-xs flex items-center gap-2">
          <Globe size={16} className="text-cyan-400" />
          <span>STEP 1: TARGET SERVER ADDRESS & SCOPE PROBE</span>
        </h3>

        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="flex-1 w-full">
            <label className="block text-slate-400 text-[10px] uppercase mb-1">Target Application Address</label>
            <input
              type="text"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              placeholder="Enter target application address..."
              className="w-full p-2.5 rounded bg-slate-950 border border-slate-800 text-cyan-300 font-bold focus:border-cyan-500 outline-none"
            />
          </div>

          <div className="flex flex-wrap sm:flex-nowrap items-center gap-2 mt-4 sm:mt-0">
            <button
              onClick={handleSaveTarget}
              disabled={savingTarget}
              className="px-4 py-2.5 rounded bg-slate-900 text-slate-200 border border-slate-700 hover:bg-slate-800 font-bold flex items-center justify-center gap-2 transition-all shadow-md"
            >
              <Save size={14} className={savingTarget ? 'animate-spin' : ''} />
              <span>{savingTarget ? 'Saving...' : 'Save Target URL'}</span>
            </button>

            <button
              onClick={handleVerify}
              disabled={verifying}
              className="px-4 py-2.5 rounded bg-cyan-950/90 text-cyan-300 border border-cyan-500/60 hover:bg-cyan-900/80 font-bold flex items-center justify-center gap-2 transition-all shadow-md"
            >
              <RefreshCw size={14} className={verifying ? 'animate-spin' : ''} />
              <span>{verifying ? 'Probing Target...' : 'Probe & Verify Server'}</span>
            </button>
          </div>
        </div>

        {/* Probe Verification Status */}
        {verifyResult && (
          <div className={`p-4 rounded-lg border ${
            verifyResult.is_active ? 'bg-emerald-950/40 border-emerald-700/60 text-emerald-300' : 'bg-rose-950/40 border-rose-700/60 text-rose-300'
          } flex items-center justify-between`}>
            <div className="flex items-center gap-3">
              {verifyResult.is_active ? <CheckCircle2 size={20} className="text-emerald-400" /> : <AlertCircle size={20} className="text-rose-400" />}
              <div>
                <div className="font-bold text-sm">{verifyResult.message}</div>
                {verifyResult.is_active && (
                  <div className="text-[11px] text-slate-400 mt-0.5 space-x-3">
                    <span>Status: <strong className="text-emerald-400">{verifyResult.status_code}</strong></span>
                    <span>Latency: <strong className="text-cyan-400">{verifyResult.response_time_ms}ms</strong></span>
                    <span>Server: <strong className="text-slate-200">{verifyResult.server_header}</strong></span>
                  </div>
                )}
              </div>
            </div>
            {verifyResult.is_active && targetUrl && (
              <a
                href={targetUrl}
                target="_blank"
                rel="noreferrer"
                className="px-3 py-1.5 rounded bg-slate-900 text-cyan-400 border border-cyan-800 hover:bg-slate-800 font-semibold flex items-center gap-1.5 transition-colors"
              >
                <span>Open Direct Target App</span>
                <ExternalLink size={12} />
              </a>
            )}
          </div>
        )}
      </div>

      {/* Step 2: Guided Instructions & Session Recorder Controller */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass-panel rounded-lg p-5 space-y-3">
          <h3 className="font-bold text-slate-200 uppercase tracking-wider text-xs flex items-center gap-2">
            <Zap size={16} className="text-amber-400" />
            <span>GUIDED USAGE INSTRUCTIONS</span>
          </h3>

          <div className="space-y-2 text-slate-300 text-[11px] leading-relaxed">
            <div className="p-2 rounded bg-slate-950 border border-slate-800">
              <strong className="text-cyan-400">1. Verify Target:</strong> Ensure target software address is configured above.
            </div>
            <div className="p-2 rounded bg-slate-950 border border-slate-800">
              <strong className="text-emerald-400">2. Select Identity:</strong> Select or register a database identity below.
            </div>
            <div className="p-2 rounded bg-slate-950 border border-slate-800">
              <strong className="text-amber-400">3. Control Interceptor:</strong> Start, Pause, Resume, or Clear buffer anytime.
            </div>
            <div className="p-2 rounded bg-slate-950 border border-slate-800">
              <strong className="text-rose-400">4. Build WSG Graph:</strong> Click <strong>Stop & Build Workflow Graph</strong>.
            </div>
          </div>
        </div>

        {/* Live Recording Controller */}
        <div className="lg:col-span-2 glass-panel rounded-lg p-5 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
              <h3 className="font-bold text-slate-200 uppercase tracking-wider text-xs flex items-center gap-2">
                <Radio size={16} className={isRecording ? 'text-rose-400 animate-ping' : isPaused ? 'text-amber-400' : 'text-slate-500'} />
                <span>STEP 2: LIVE TRAFFIC INTERCEPTOR & CONTROL PANEL</span>
              </h3>
              <div className="flex items-center gap-2">
                <Badge variant={isRecording ? 'danger' : isPaused ? 'warning' : 'secondary'}>
                  {isRecording ? 'RECORDING LIVE' : isPaused ? 'PAUSED' : 'STOPPED'}
                </Badge>
              </div>
            </div>

            <div className="space-y-3">
              {/* Dynamic Identity Selection Dropdown */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded border border-slate-800">
                  <User size={14} className="text-indigo-400" />
                  <label className="text-[10px] text-slate-400 uppercase font-bold">Recording Identity:</label>
                  <select
                    value={selectedIdentityId}
                    onChange={(e) => setSelectedIdentityId(e.target.value)}
                    disabled={isRecording}
                    className="bg-transparent text-slate-200 font-bold text-xs outline-none cursor-pointer"
                  >
                    {identities.length === 0 ? (
                      <option value="">No Identities Registered</option>
                    ) : (
                      identities.map((id) => (
                        <option key={id.id} value={id.id} className="bg-slate-900 text-slate-200">
                          {id.name} ({id.role})
                        </option>
                      ))
                    )}
                  </select>
                </div>

                <button
                  onClick={handleQuickCreateIdentity}
                  disabled={isRecording}
                  className="px-2.5 py-1.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-700/70 hover:bg-indigo-900 font-bold flex items-center gap-1 text-[11px]"
                  title="Quick register new identity"
                >
                  <User size={12} />
                  <span>+ Quick Add Identity</span>
                </button>

                <span className="text-slate-400 font-mono text-xs ml-auto">
                  Captured Buffer: <strong className="text-cyan-400">{capturedTxs.length}</strong> txs
                </span>
              </div>


              {/* Comprehensive Control Buttons */}
              <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/80">
                {!isRecording && !isPaused && (
                  <button
                    onClick={startRecordingSession}
                    disabled={!selectedIdentityId}
                    className="px-3.5 py-2 rounded bg-emerald-950 text-emerald-300 border border-emerald-600/60 hover:bg-emerald-900 font-bold flex items-center gap-1.5 transition-all shadow-md disabled:opacity-50"
                  >
                    <Play size={13} />
                    <span>Start Recording</span>
                  </button>
                )}

                {isRecording && (
                  <button
                    onClick={pauseRecordingSession}
                    className="px-3.5 py-2 rounded bg-amber-950 text-amber-300 border border-amber-600/60 hover:bg-amber-900 font-bold flex items-center gap-1.5 transition-all shadow-md"
                  >
                    <Pause size={13} />
                    <span>Pause</span>
                  </button>
                )}

                {isPaused && (
                  <button
                    onClick={resumeRecordingSession}
                    className="px-3.5 py-2 rounded bg-emerald-950 text-emerald-300 border border-emerald-600/60 hover:bg-emerald-900 font-bold flex items-center gap-1.5 transition-all shadow-md"
                  >
                    <Play size={13} />
                    <span>Resume</span>
                  </button>
                )}

                {(isRecording || isPaused || capturedTxs.length > 0) && (
                  <button
                    onClick={stopAndBuildGraph}
                    disabled={buildingGraph}
                    className="px-3.5 py-2 rounded bg-rose-950 text-rose-300 border border-rose-600/60 hover:bg-rose-900 font-bold flex items-center gap-1.5 transition-all shadow-md"
                  >
                    <Square size={13} />
                    <span>{buildingGraph ? 'Building Graph...' : 'Stop & Build Graph'}</span>
                  </button>
                )}

                <button
                  onClick={clearBufferSession}
                  disabled={capturedTxs.length === 0 && !isRecording && !isPaused}
                  className="px-3 py-2 rounded bg-slate-900 text-slate-300 border border-slate-700 hover:bg-slate-800 font-bold flex items-center gap-1.5 transition-all disabled:opacity-40"
                  title="Wipe live buffer memory"
                >
                  <Trash2 size={13} />
                  <span>Clear Buffer</span>
                </button>

                <button
                  onClick={restartRecordingSession}
                  disabled={!selectedIdentityId}
                  className="px-3 py-2 rounded bg-slate-900 text-cyan-300 border border-cyan-800 hover:bg-slate-800 font-bold flex items-center gap-1.5 transition-all disabled:opacity-40"
                  title="Clear buffer and start a new recording session"
                >
                  <RotateCcw size={13} />
                  <span>Retry / New Session</span>
                </button>
              </div>
            </div>
          </div>

          {graphMessage && (
            <div className="p-3 rounded bg-cyan-950/60 border border-cyan-500/60 text-cyan-300 text-xs flex items-center justify-between">
              <span>{graphMessage}</span>
              {onNavigateToWorkflows && (
                <button
                  onClick={onNavigateToWorkflows}
                  className="px-2.5 py-1 rounded bg-cyan-900 text-cyan-200 font-bold hover:bg-cyan-800 flex items-center gap-1"
                >
                  <span>View Workflows Tab</span>
                  <ArrowRight size={12} />
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Captured Transactions Table */}
      <div className="glass-panel rounded-lg p-5 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <h3 className="font-bold text-slate-200 uppercase tracking-wider text-xs flex items-center gap-2">
            <Layers size={16} className="text-cyan-400" />
            <span>CAPTURED LIVE TRANSACTIONS ({capturedTxs.length})</span>
          </h3>
          {capturedTxs.length > 0 && (
            <button
              onClick={clearBufferSession}
              className="text-[10px] text-rose-400 hover:text-rose-300 font-bold flex items-center gap-1"
            >
              <Trash2 size={12} />
              <span>Clear Captured List</span>
            </button>
          )}
        </div>

        <div className="bg-slate-950 rounded-lg border border-slate-800 overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-slate-900 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-4 py-2.5">#</th>
                <th className="px-4 py-2.5">Method</th>
                <th className="px-4 py-2.5">Path</th>
                <th className="px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5">Response Payload</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {capturedTxs.map((tx, idx) => (
                <tr key={idx} className="hover:bg-slate-900/50">
                  <td className="px-4 py-2 text-slate-500">{idx + 1}</td>
                  <td className="px-4 py-2">
                    <Badge variant={tx.method === 'GET' ? 'info' : 'success'}>{tx.method}</Badge>
                  </td>
                  <td className="px-4 py-2 font-bold text-slate-200">{tx.path}</td>
                  <td className="px-4 py-2 font-semibold text-emerald-400">{tx.res_status}</td>
                  <td className="px-4 py-2 text-cyan-300 font-mono text-[11px] truncate max-w-xs">{tx.res_body}</td>
                </tr>
              ))}
              {capturedTxs.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-slate-500">
                    No live transactions recorded. Interact with the application in the workspace below.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Step 3: Embedded WSG Workflow State Graph Preview */}
      {embeddedGraphData && (
        <div className="glass-panel rounded-lg p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="font-bold text-slate-200 uppercase tracking-wider text-xs flex items-center gap-2">
              <GitBranch size={16} className="text-cyan-400" />
              <span>RECONSTRUCTED WORKFLOW STATE GRAPH PREVIEW</span>
            </h3>
            {onNavigateToWorkflows && (
              <button
                onClick={onNavigateToWorkflows}
                className="text-cyan-400 hover:text-cyan-300 text-[11px] font-bold flex items-center gap-1"
              >
                <span>Open Full Workflows Screen</span>
                <ArrowRight size={12} />
              </button>
            )}
          </div>

          <GraphVisualizer
            nodes={embeddedGraphData.nodes}
            edges={embeddedGraphData.edges}
            dependencies={embeddedGraphData.dependencies}
          />
        </div>
      )}

      {/* Step 4: Embedded Target Application Workspace */}
      <div className="glass-panel rounded-lg p-5 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h3 className="font-bold text-slate-200 uppercase tracking-wider text-xs flex items-center gap-2">
              <Code size={16} className="text-cyan-400" />
              <span>INTERCEPTED LOCAL TARGET APPLICATION WORKSPACE</span>
            </h3>
            <p className="text-slate-400 text-[10px] mt-0.5">
              Canonical Interceptor Proxy: <code className="text-cyan-300">{AUTHTWIN_CONFIG.INTERCEPTOR_PROXY_PREFIX}/</code> {targetUrl ? `(Proxying ${targetUrl})` : ''}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIframeKey(Date.now())}
              className="text-slate-300 hover:text-white font-bold flex items-center gap-1 text-[11px] px-3 py-1.5 bg-slate-900 rounded border border-slate-800"
            >
              <RefreshCw size={12} />
              <span>Reload Iframe</span>
            </button>
            {targetUrl && (
              <a
                href={targetUrl}
                target="_blank"
                rel="noreferrer"
                className="text-slate-400 hover:text-slate-200 font-bold flex items-center gap-1 text-[11px] px-3 py-1.5 bg-slate-900 rounded border border-slate-800"
              >
                <span>Direct Target</span>
                <ExternalLink size={12} />
              </a>
            )}
            <a
              href={`${AUTHTWIN_CONFIG.INTERCEPTOR_PROXY_PREFIX}/`}
              target="_blank"
              rel="noreferrer"
              className="text-cyan-400 hover:text-cyan-300 font-bold flex items-center gap-1 text-[11px] px-3 py-1.5 bg-slate-900 rounded border border-slate-800"
            >
              <span>Open Intercepted App in Tab</span>
              <ExternalLink size={12} />
            </a>
          </div>
        </div>

        <div className="w-full h-96 bg-slate-950 rounded-lg border border-slate-800 overflow-hidden relative flex flex-col justify-center items-center">
          {targetUrl ? (
            <iframe
              key={iframeKey}
              src={`${AUTHTWIN_CONFIG.INTERCEPTOR_PROXY_PREFIX}/`}
              title="Target Application Sandbox"
              className="w-full h-full border-none bg-white"
            />
          ) : (
            <div className="p-8 text-center space-y-3">
              <Radio size={36} className="text-slate-600 mx-auto animate-pulse" />
              <div className="text-slate-300 font-bold text-sm">
                TARGET WORKSPACE STANDING BY
              </div>
              <p className="text-slate-500 text-xs max-w-md mx-auto">
                Configure a target application address above and click <strong className="text-slate-200">Probe & Verify Server</strong> to load the live workspace.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

