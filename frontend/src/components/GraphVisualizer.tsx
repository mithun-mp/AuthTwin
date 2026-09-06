import React, { useState, useEffect, useRef } from 'react';
import { WorkflowNode, WorkflowEdge, Dependency } from '../types';
import { Badge } from './Badge';
import { Layers, Database, Tag, Link as LinkIcon, Info, Box, Move, Sparkles } from 'lucide-react';

interface GraphVisualizerProps {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  dependencies: Dependency[];
}

export const GraphVisualizer: React.FC<GraphVisualizerProps> = ({ nodes, edges, dependencies }) => {
  const [viewMode, setViewMode] = useState<'2D' | '3D'>('2D');
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(nodes[0] || null);
  const canvas3DRef = useRef<HTMLCanvasElement | null>(null);

  // 3D Orbit Camera State
  const [rotX, setRotX] = useState<number>(0.3);
  const [rotY, setRotY] = useState<number>(0.6);
  const [zoom, setZoom] = useState<number>(1.0);
  const isDraggingRef = useRef<boolean>(false);
  const lastMouseRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  useEffect(() => {
    if (nodes.length > 0 && (!selectedNode || !nodes.find(n => n.id === selectedNode.id))) {
      setSelectedNode(nodes[0]);
    }
  }, [nodes]);

  const getMethodBadgeVariant = (method: string) => {
    switch (method.toUpperCase()) {
      case 'GET': return 'info';
      case 'POST': return 'success';
      case 'PUT': case 'PATCH': return 'warning';
      case 'DELETE': return 'danger';
      default: return 'secondary';
    }
  };

  const getMethodColor = (method: string) => {
    switch (method.toUpperCase()) {
      case 'GET': return '#38bdf8';     // cyan/sky
      case 'POST': return '#34d399';    // emerald
      case 'PUT': case 'PATCH': return '#fbbf24'; // amber
      case 'DELETE': return '#f87171';  // rose
      default: return '#94a3b8';        // slate
    }
  };

  const findDependencyForEdge = (edge: WorkflowEdge) => {
    if (!edge.dependency_id) return null;
    return dependencies.find(d => d.id === edge.dependency_id) || null;
  };

  // 3D Canvas Spatial Renderer Loop
  useEffect(() => {
    if (viewMode !== '3D' || !canvas3DRef.current || nodes.length === 0) return;

    const canvas = canvas3DRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animFrameId: number;
    let time = 0;

    // Map nodes to 3D Spatial Coordinates (Spiral Helix / Layered 3D Ring)
    const spatial3DNodes = nodes.map((node, idx) => {
      const radius = 180;
      const angle = (idx / Math.max(1, nodes.length)) * Math.PI * 2.5;
      const zHeight = (idx - nodes.length / 2) * 60;
      return {
        ...node,
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
        z: zHeight
      };
    });

    const render3D = () => {
      time += 0.02;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const cx = canvas.width / 2;
      const cy = canvas.height / 2;

      // Project 3D Point (x, y, z) to 2D Screen (px, py) using Rotations
      const project = (x: number, y: number, z: number) => {
        const x1 = x * Math.cos(rotY) - z * Math.sin(rotY);
        const z1 = x * Math.sin(rotY) + z * Math.cos(rotY);

        const y2 = y * Math.cos(rotX) - z1 * Math.sin(rotX);
        const z2 = y * Math.sin(rotX) + z1 * Math.cos(rotX);

        const fov = 400 * Math.max(0.1, zoom);
        const depth = fov + z2 + 400;
        const scale = Math.max(0.05, fov / Math.max(20, depth));
        const px = cx + x1 * scale;
        const py = cy + y2 * scale;

        return { px, py, scale, z: z2, isVisible: depth > 20 };
      };

      const projected = spatial3DNodes.map(n => ({
        node: n,
        proj: project(n.x, n.y, n.z)
      }));

      // Sort by Z for Depth Buffering
      projected.sort((a, b) => b.proj.z - a.proj.z);

      // Render 3D Edges & Animated Data Packets
      edges.forEach(edge => {
        const src = projected.find(p => p.node.id === edge.source_node_id);
        const tgt = projected.find(p => p.node.id === edge.target_node_id);

        if (src && tgt && src.proj.isVisible && tgt.proj.isVisible) {
          const isDep = Boolean(edge.dependency_id);

          ctx.beginPath();
          ctx.moveTo(src.proj.px, src.proj.py);
          ctx.lineTo(tgt.proj.px, tgt.proj.py);
          ctx.strokeStyle = isDep ? 'rgba(251, 191, 36, 0.85)' : 'rgba(56, 189, 248, 0.45)';
          ctx.lineWidth = Math.max(0.5, isDep ? 2.5 * src.proj.scale : 1.5 * src.proj.scale);
          ctx.setLineDash(isDep ? [6, 4] : []);
          ctx.stroke();

          // Animated glowing light packet moving along 3D edge
          const packetProgress = (time * 0.8 + src.node.sequence_index * 0.3) % 1;
          const packetX = src.proj.px + (tgt.proj.px - src.proj.px) * packetProgress;
          const packetY = src.proj.py + (tgt.proj.py - src.proj.py) * packetProgress;
          const packetRadius = Math.max(1, 4 * Math.max(0.1, src.proj.scale));

          ctx.beginPath();
          ctx.arc(packetX, packetY, packetRadius, 0, Math.PI * 2);
          ctx.fillStyle = isDep ? '#fbbf24' : '#38bdf8';
          ctx.shadowColor = isDep ? '#fbbf24' : '#38bdf8';
          ctx.shadowBlur = 10;
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      });

      // Render 3D Spheres & Labels
      projected.forEach(({ node, proj }) => {
        if (!proj.isVisible) return;

        const isSelected = selectedNode?.id === node.id;
        const color = getMethodColor(node.method);
        const safeScale = Math.max(0.1, proj.scale);
        const nodeRadius = Math.max(2, (isSelected ? 16 : 12) * safeScale);
        const haloRadius = Math.max(3, nodeRadius + 6);

        // Glowing Outer Halo
        ctx.beginPath();
        ctx.arc(proj.px, proj.py, haloRadius, 0, Math.PI * 2);
        ctx.fillStyle = isSelected ? 'rgba(56, 189, 248, 0.3)' : 'rgba(15, 23, 42, 0.4)';
        ctx.fill();

        // Core Sphere
        ctx.beginPath();
        ctx.arc(proj.px, proj.py, nodeRadius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.shadowColor = color;
        ctx.shadowBlur = isSelected ? 15 : 6;
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.strokeStyle = '#0f172a';
        ctx.lineWidth = Math.max(0.5, 2 * safeScale);
        ctx.stroke();

        // 3D Projected Text Label
        ctx.font = `${Math.max(10, Math.round(11 * safeScale))}px JetBrains Mono, monospace`;
        ctx.fillStyle = isSelected ? '#38bdf8' : '#e2e8f0';
        ctx.textAlign = 'center';
        ctx.fillText(`${node.method} ${node.path_template}`, proj.px, proj.py - nodeRadius - 8);

        if (node.resource_identifier) {
          ctx.font = `${Math.max(8, Math.round(9 * safeScale))}px JetBrains Mono, monospace`;
          ctx.fillStyle = '#fbbf24';
          ctx.fillText(`${node.resource_type}:${node.resource_identifier}`, proj.px, proj.py + nodeRadius + 14);
        }
      });

      animFrameId = requestAnimationFrame(render3D);
    };

    render3D();

    return () => {
      cancelAnimationFrame(animFrameId);
    };
  }, [viewMode, nodes, edges, rotX, rotY, zoom, selectedNode]);

  // Mouse Orbit & Canvas Click Event Handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    isDraggingRef.current = true;
    lastMouseRef.current = { x: e.clientX, y: e.clientY };

    // Handle 3D canvas node selection click
    if (canvas3DRef.current && nodes.length > 0) {
      const rect = canvas3DRef.current.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const clickY = e.clientY - rect.top;

      const cx = canvas3DRef.current.width / 2;
      const cy = canvas3DRef.current.height / 2;

      for (let i = nodes.length - 1; i >= 0; i--) {
        const idx = i;
        const radius = 180;
        const angle = (idx / Math.max(1, nodes.length)) * Math.PI * 2.5;
        const zHeight = (idx - nodes.length / 2) * 60;
        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius;
        const z = zHeight;

        const x1 = x * Math.cos(rotY) - z * Math.sin(rotY);
        const z1 = x * Math.sin(rotY) + z * Math.cos(rotY);
        const y2 = y * Math.cos(rotX) - z1 * Math.sin(rotX);
        const z2 = y * Math.sin(rotX) + z1 * Math.cos(rotX);

        const fov = 400 * Math.max(0.1, zoom);
        const depth = fov + z2 + 400;
        if (depth <= 20) continue;

        const scale = Math.max(0.05, fov / Math.max(20, depth));
        const px = cx + x1 * scale;
        const py = cy + y2 * scale;

        const dist = Math.hypot(clickX - px, clickY - py);
        if (dist <= Math.max(10, 20 * scale)) {
          setSelectedNode(nodes[idx]);
          break;
        }
      }
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - lastMouseRef.current.x;
    const dy = e.clientY - lastMouseRef.current.y;

    setRotY(prev => prev + dx * 0.008);
    setRotX(prev => Math.max(-Math.PI / 2, Math.min(Math.PI / 2, prev + dy * 0.008)));

    lastMouseRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    setZoom(prev => Math.max(0.4, Math.min(2.5, prev - e.deltaY * 0.001)));
  };


  return (
    <div className="space-y-4 font-mono text-xs">
      {/* View Switcher Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900 p-3 rounded-lg border border-slate-800">
        <div className="flex items-center gap-2">
          <Layers size={16} className="text-cyan-400" />
          <span className="font-bold text-slate-200 uppercase text-xs">WORKFLOW STATE GRAPH VISUALIZER</span>
          <span className="text-slate-500 text-[11px] ml-2">({nodes.length} States • {edges.length} Transitions)</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('2D')}
            className={`px-3 py-1.5 rounded font-bold flex items-center gap-1.5 transition-all ${
              viewMode === '2D'
                ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/70 shadow-md'
                : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200'
            }`}
          >
            <Layers size={14} />
            <span>2D Flow Diagram</span>
          </button>

          <button
            onClick={() => setViewMode('3D')}
            className={`px-3 py-1.5 rounded font-bold flex items-center gap-1.5 transition-all ${
              viewMode === '3D'
                ? 'bg-indigo-950 text-indigo-300 border border-indigo-500/70 shadow-md'
                : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200'
            }`}
          >
            <Box size={14} />
            <span>3D Cybernetic Spatial</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Canvas Area */}
        <div className="lg:col-span-2 bg-slate-950 border border-slate-800 rounded-lg p-5 min-h-[520px] flex flex-col justify-between relative overflow-hidden">
          {viewMode === '2D' ? (
            /* 2D Directed Graph Flowchart */
            <div className="flex-1 flex flex-col gap-5 items-center justify-center py-4 overflow-y-auto max-h-[600px] pr-2">
              {nodes.map((node, idx) => {
                const isSelected = selectedNode?.id === node.id;
                const outgoingEdge = edges.find(e => e.source_node_id === node.id);
                const dep = outgoingEdge ? findDependencyForEdge(outgoingEdge) : null;

                return (
                  <React.Fragment key={node.id}>
                    {/* Node Card */}
                    <div
                      onClick={() => setSelectedNode(node)}
                      className={`w-full max-w-lg cursor-pointer transition-all p-4 rounded-lg border ${
                        isSelected
                          ? 'bg-cyan-950/60 border-cyan-500 shadow-lg shadow-cyan-950/60 ring-1 ring-cyan-500/60'
                          : 'bg-slate-900/90 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-bold">
                            #{node.sequence_index}
                          </span>
                          <Badge variant={getMethodBadgeVariant(node.method)}>{node.method}</Badge>
                          <span className="text-xs font-mono font-bold text-slate-100 truncate">
                            {node.path_template}
                          </span>
                        </div>
                      </div>

                      <div className="text-[11px] font-mono text-slate-400 space-y-1">
                        <div className="flex items-center gap-1.5">
                          <Tag size={12} className="text-slate-500" />
                          <span>Operation ID: <span className="text-cyan-400 font-bold">{node.operation_id || 'unmapped'}</span></span>
                        </div>
                        {node.resource_identifier && (
                          <div className="flex items-center gap-1.5 text-amber-400 font-bold">
                            <Database size={12} />
                            <span>Resource: {node.resource_type}:{node.resource_identifier}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Transition Indicator */}
                    {idx < nodes.length - 1 && (
                      <div className="flex flex-col items-center gap-1 my-1">
                        <div className="w-0.5 h-6 bg-slate-700 animate-pulse"></div>
                        {dep ? (
                          <div className="flex items-center gap-1.5 text-[10px] font-mono px-3 py-1 rounded bg-amber-950/90 border border-amber-500/70 text-amber-300 font-bold shadow-md">
                            <LinkIcon size={11} />
                            <span>DEPENDENCY LINK: {dep.dependency_type} ({dep.extracted_value})</span>
                          </div>
                        ) : (
                          <div className="text-[9px] font-mono text-slate-500 uppercase tracking-widest bg-slate-900 px-2.5 py-0.5 rounded border border-slate-800">
                            SEQUENCE TRANSITION
                          </div>
                        )}
                        <div className="w-0.5 h-6 bg-slate-700"></div>
                      </div>
                    )}
                  </React.Fragment>
                );
              })}

              {nodes.length === 0 && (
                <div className="p-8 text-center text-slate-500 font-bold">
                  No nodes available to visualize.
                </div>
              )}
            </div>
          ) : (
            /* 3D Cybernetic Spatial Visualizer Canvas */
            <div className="relative w-full h-[520px] flex items-center justify-center cursor-grab active:cursor-grabbing select-none">
              <canvas
                ref={canvas3DRef}
                width={700}
                height={500}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
                onWheel={handleWheel}
                className="w-full h-full rounded-lg"
              />

              <div className="absolute top-3 left-3 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded border border-slate-800 text-[10px] text-slate-400 flex items-center gap-2">
                <Move size={12} className="text-cyan-400" />
                <span>Drag to Rotate 3D Spatial Canvas • Scroll to Zoom</span>
              </div>

              <div className="absolute bottom-3 right-3 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded border border-slate-800 text-[10px] text-slate-400 flex items-center gap-2">
                <Sparkles size={12} className="text-amber-400" />
                <span>3D Node Coordinates Projected in Real-Time</span>
              </div>
            </div>
          )}
        </div>

        {/* Node Inspector Sidebar */}
        <div className="bg-slate-950 border border-slate-800 rounded-lg p-5 flex flex-col justify-between">
          {selectedNode ? (
            <div className="space-y-4">
              <div className="border-b border-slate-800 pb-3">
                <span className="text-[10px] font-mono font-bold text-slate-500 uppercase tracking-wider block">
                  SELECTED STATE INSPECTOR
                </span>
                <h3 className="text-xs font-mono font-bold text-slate-100 mt-1 flex items-center gap-2">
                  <Badge variant={getMethodBadgeVariant(selectedNode.method)}>{selectedNode.method}</Badge>
                  <span className="truncate">{selectedNode.actual_path}</span>
                </h3>
              </div>

              <div className="space-y-3 text-xs font-mono">
                <div>
                  <span className="text-slate-500 text-[10px] uppercase block mb-1">Sequence Index</span>
                  <span className="text-slate-200 font-bold">Step #{selectedNode.sequence_index}</span>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] uppercase block mb-1">OpenAPI Path Template</span>
                  <span className="text-cyan-400 font-bold">{selectedNode.path_template}</span>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] uppercase block mb-1">Operation ID</span>
                  <span className="text-slate-200 font-bold">{selectedNode.operation_id || 'unmapped'}</span>
                </div>
                {selectedNode.resource_type && (
                  <div>
                    <span className="text-slate-500 text-[10px] uppercase block mb-1">Inferred Resource</span>
                    <div className="p-2.5 rounded bg-slate-900 border border-slate-800 text-amber-300 font-bold">
                      {selectedNode.resource_type}:{selectedNode.resource_identifier}
                    </div>
                  </div>
                )}
                <div>
                  <span className="text-slate-500 text-[10px] uppercase block mb-1">Source Transaction ID</span>
                  <span className="text-slate-400 text-[10px] break-all font-mono">{selectedNode.transaction_id}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 font-mono text-xs text-center p-6 space-y-2">
              <Info size={28} className="text-slate-600 animate-pulse" />
              <div className="font-bold text-slate-400">STATE INSPECTOR STANDING BY</div>
              <p className="text-[11px] text-slate-500">
                Select a WSG node on the 2D or 3D canvas to inspect state parameters & transaction evidence.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
