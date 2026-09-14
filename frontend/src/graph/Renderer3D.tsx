import React, { useState, useEffect, useRef } from 'react';
import { CanonicalNode, CanonicalEdge, Dependency } from '../types';
import { Move, Sparkles, RotateCcw, ZoomIn, ZoomOut, Sliders } from 'lucide-react';

interface Renderer3DProps {
  nodes: CanonicalNode[];
  edges: CanonicalEdge[];
  dependencies: Dependency[];
  selectedNode: CanonicalNode | null;
  selectedEdge?: CanonicalEdge | null;
  onSelectNode: (node: CanonicalNode) => void;
  onSelectEdge?: (edge: CanonicalEdge) => void;
  viewType: 'logical' | 'execution';
}

export const Renderer3D: React.FC<Renderer3DProps> = ({
  nodes,
  edges,
  dependencies,
  selectedNode,
  selectedEdge,
  onSelectNode,
  onSelectEdge,
  viewType
}) => {
  const canvas3DRef = useRef<HTMLCanvasElement | null>(null);

  // 3D Orbit Camera, Spatial Scale & Transformation State
  const [rotX, setRotX] = useState<number>(0.3);
  const [rotY, setRotY] = useState<number>(0.6);
  const [zoom, setZoom] = useState<number>(1.0);
  const [spatialScale, setSpatialScale] = useState<number>(1.0);
  const [panX, setPanX] = useState<number>(0);
  const [panY, setPanY] = useState<number>(0);

  const isDraggingRef = useRef<boolean>(false);
  const lastMouseRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  const getMethodColor = (method: string) => {
    switch (method.toUpperCase()) {
      case 'GET': return '#38bdf8';       // sky
      case 'POST': return '#34d399';      // emerald
      case 'PUT': case 'PATCH': return '#fbbf24';  // amber
      case 'DELETE': return '#f87171';    // rose
      default: return '#94a3b8';          // slate
    }
  };

  // 3D Canvas Spatial Renderer Loop
  useEffect(() => {
    if (!canvas3DRef.current || nodes.length === 0) return;

    const canvas = canvas3DRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animFrameId: number;
    let time = 0;

    // Map canonical nodes to 3D Spatial Coordinates (Layered 3D Spiral Helix)
    const spatial3DNodes = nodes.map((node, idx) => {
      const radius = 180 * spatialScale;
      const angle = (idx / Math.max(1, nodes.length)) * Math.PI * 2.5;
      const zHeight = (idx - nodes.length / 2) * 60 * spatialScale;
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

      const cx = canvas.width / 2 + panX;
      const cy = canvas.height / 2 + panY;

      // Project 3D Point (x, y, z) to 2D Screen (px, py)
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

      // Render 3D Edges & Animated Data Flow Packets
      edges.forEach(edge => {
        const src = projected.find(p => p.node.id === edge.source);
        const tgt = projected.find(p => p.node.id === edge.target);

        if (src && tgt && src.proj.isVisible && tgt.proj.isVisible) {
          const isSelected = selectedEdge?.id === edge.id;
          const isDep = edge.edge_type === 'DEPENDENCY_TRANSITION' || edge.types?.includes('DEPENDENCY_TRANSITION');
          const isBranch = edge.edge_type === 'BRANCH' || edge.types?.includes('BRANCH');
          const isMerge = edge.edge_type === 'MERGE' || edge.types?.includes('MERGE');

          ctx.beginPath();
          ctx.moveTo(src.proj.px, src.proj.py);
          ctx.lineTo(tgt.proj.px, tgt.proj.py);

          if (isSelected) {
            ctx.strokeStyle = '#38bdf8';
            ctx.lineWidth = Math.max(1.5, 4.0 * src.proj.scale);
            ctx.setLineDash([]);
          } else if (isDep) {
            ctx.strokeStyle = 'rgba(251, 191, 36, 0.85)';
            ctx.lineWidth = Math.max(0.5, 2.5 * src.proj.scale);
            ctx.setLineDash([6, 4]);
          } else if (isBranch) {
            ctx.strokeStyle = 'rgba(245, 158, 11, 0.75)';
            ctx.lineWidth = Math.max(0.5, 2.0 * src.proj.scale);
            ctx.setLineDash([]);
          } else if (isMerge) {
            ctx.strokeStyle = 'rgba(129, 140, 248, 0.75)';
            ctx.lineWidth = Math.max(0.5, 2.0 * src.proj.scale);
            ctx.setLineDash([]);
          } else {
            ctx.strokeStyle = 'rgba(56, 189, 248, 0.45)';
            ctx.lineWidth = Math.max(0.5, 1.5 * src.proj.scale);
            ctx.setLineDash([]);
          }

          ctx.stroke();
          ctx.setLineDash([]);

          // Animated glowing light packet moving along actual edge vector
          const packetProgress = (time * 0.8 + (src.node.occurrences[0]?.occurrence_index || 0) * 0.3) % 1;
          const packetX = src.proj.px + (tgt.proj.px - src.proj.px) * packetProgress;
          const packetY = src.proj.py + (tgt.proj.py - src.proj.py) * packetProgress;
          const packetRadius = Math.max(1.5, 4.5 * Math.max(0.1, src.proj.scale));

          ctx.beginPath();
          ctx.arc(packetX, packetY, packetRadius, 0, Math.PI * 2);
          ctx.fillStyle = isDep ? '#fbbf24' : isBranch ? '#f59e0b' : '#38bdf8';
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
        ctx.fillStyle = isSelected ? 'rgba(56, 189, 248, 0.35)' : 'rgba(15, 23, 42, 0.4)';
        ctx.fill();

        // Core Sphere
        ctx.beginPath();
        ctx.arc(proj.px, proj.py, nodeRadius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.shadowColor = color;
        ctx.shadowBlur = isSelected ? 18 : 6;
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.strokeStyle = '#0f172a';
        ctx.lineWidth = Math.max(0.5, 2 * safeScale);
        ctx.stroke();

        // Text Label
        const labelText = viewType === 'logical'
          ? `${node.method} ${node.path_template}`
          : `${node.method} ${node.actual_path}`;

        ctx.font = `${Math.max(10, Math.round(11 * safeScale))}px JetBrains Mono, monospace`;
        ctx.fillStyle = isSelected ? '#38bdf8' : '#e2e8f0';
        ctx.textAlign = 'center';
        ctx.fillText(labelText, proj.px, proj.py - nodeRadius - 8);

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
  }, [nodes, edges, rotX, rotY, zoom, spatialScale, panX, panY, selectedNode, selectedEdge, viewType]);

  // Orbit Mouse Drag Handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    isDraggingRef.current = true;
    lastMouseRef.current = { x: e.clientX, y: e.clientY };

    // Node selection click handler
    if (canvas3DRef.current && nodes.length > 0) {
      const rect = canvas3DRef.current.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const clickY = e.clientY - rect.top;

      const cx = canvas3DRef.current.width / 2 + panX;
      const cy = canvas3DRef.current.height / 2 + panY;

      let nodeHit = false;
      for (let i = nodes.length - 1; i >= 0; i--) {
        const idx = i;
        const radius = 180 * spatialScale;
        const angle = (idx / Math.max(1, nodes.length)) * Math.PI * 2.5;
        const zHeight = (idx - nodes.length / 2) * 60 * spatialScale;
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
        if (dist <= Math.max(12, 22 * scale)) {
          onSelectNode(nodes[idx]);
          nodeHit = true;
          break;
        }
      }

      // If no node hit, check edge proximity
      if (!nodeHit && onSelectEdge && edges.length > 0) {
        const project = (x: number, y: number, z: number) => {
          const x1 = x * Math.cos(rotY) - z * Math.sin(rotY);
          const z1 = x * Math.sin(rotY) + z * Math.cos(rotY);
          const y2 = y * Math.cos(rotX) - z1 * Math.sin(rotX);
          const z2 = y * Math.sin(rotX) + z1 * Math.cos(rotX);
          const fov = 400 * Math.max(0.1, zoom);
          const depth = fov + z2 + 400;
          const scale = Math.max(0.05, fov / Math.max(20, depth));
          return { px: cx + x1 * scale, py: cy + y2 * scale, isVisible: depth > 20 };
        };

        const spatial3DNodes = nodes.map((node, idx) => {
          const radius = 180 * spatialScale;
          const angle = (idx / Math.max(1, nodes.length)) * Math.PI * 2.5;
          const zHeight = (idx - nodes.length / 2) * 60 * spatialScale;
          return { ...node, x: Math.cos(angle) * radius, y: Math.sin(angle) * radius, z: zHeight };
        });

        for (const edge of edges) {
          const src = spatial3DNodes.find(n => n.id === edge.source);
          const tgt = spatial3DNodes.find(n => n.id === edge.target);
          if (src && tgt) {
            const pSrc = project(src.x, src.y, src.z);
            const pTgt = project(tgt.x, tgt.y, tgt.z);
            if (pSrc.isVisible && pTgt.isVisible) {
              const dx = pTgt.px - pSrc.px;
              const dy = pTgt.py - pSrc.py;
              const l2 = dx * dx + dy * dy;
              let t = l2 === 0 ? 0 : ((clickX - pSrc.px) * dx + (clickY - pSrc.py) * dy) / l2;
              t = Math.max(0, Math.min(1, t));
              const projX = pSrc.px + t * dx;
              const projY = pSrc.py + t * dy;
              const dist = Math.hypot(clickX - projX, clickY - projY);
              if (dist <= 10) {
                onSelectEdge(edge);
                break;
              }
            }
          }
        }
      }
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - lastMouseRef.current.x;
    const dy = e.clientY - lastMouseRef.current.y;

    if (e.shiftKey) {
      setPanX(prev => prev + dx);
      setPanY(prev => prev + dy);
    } else {
      setRotY(prev => prev + dx * 0.008);
      setRotX(prev => Math.max(-Math.PI / 2, Math.min(Math.PI / 2, prev + dy * 0.008)));
    }

    lastMouseRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    setZoom(prev => Math.max(0.4, Math.min(2.5, prev - e.deltaY * 0.001)));
  };

  const handleResetCamera = () => {
    setRotX(0.3);
    setRotY(0.6);
    setZoom(1.0);
    setSpatialScale(1.0);
    setPanX(0);
    setPanY(0);
  };

  return (
    <div className="relative w-full h-[580px] bg-slate-950 border border-slate-800 rounded-lg overflow-hidden flex items-center justify-center font-mono text-xs select-none shadow-2xl">
      {/* 3D Orbit & Scale Controls Overlay */}
      <div className="absolute top-3 left-3 z-10 flex flex-wrap items-center gap-2 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded border border-slate-800 text-[10px] text-slate-300 shadow-md">
        <Move size={13} className="text-cyan-400" />
        <span>Orbit: Drag Mouse • Pan: Shift + Drag</span>
        <div className="h-3 w-px bg-slate-800 mx-1"></div>
        <button onClick={() => setZoom(prev => Math.min(2.5, prev + 0.15))} className="p-1 hover:bg-slate-800 text-cyan-400" title="Zoom In">
          <ZoomIn size={14} />
        </button>
        <button onClick={() => setZoom(prev => Math.max(0.4, prev - 0.15))} className="p-1 hover:bg-slate-800 text-cyan-400" title="Zoom Out">
          <ZoomOut size={14} />
        </button>
        <div className="h-3 w-px bg-slate-800 mx-1"></div>
        <div className="flex items-center gap-1.5">
          <Sliders size={12} className="text-indigo-400" />
          <span>3D Scale:</span>
          <input
            type="range"
            min="0.5"
            max="2.0"
            step="0.1"
            value={spatialScale}
            onChange={e => setSpatialScale(parseFloat(e.target.value))}
            className="w-16 h-1 bg-slate-800 rounded accent-cyan-400 cursor-pointer"
          />
        </div>
        <div className="h-3 w-px bg-slate-800 mx-1"></div>
        <button onClick={handleResetCamera} className="p-1 rounded hover:bg-slate-800 text-slate-300 flex items-center gap-1">
          <RotateCcw size={12} />
          <span>Reset</span>
        </button>
      </div>

      <div className="absolute bottom-3 right-3 z-10 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded border border-slate-800 text-[10px] text-slate-400 flex items-center gap-2">
        <Sparkles size={12} className="text-amber-400" />
        <span>3D Cybernetic Topology Coordinates Synchronized</span>
      </div>

      <canvas
        ref={canvas3DRef}
        width={780}
        height={560}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        className="w-full h-full cursor-grab active:cursor-grabbing rounded-lg"
      />
    </div>
  );
};
