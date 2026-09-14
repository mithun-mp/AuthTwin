import React, { useState, useEffect, useRef } from 'react';
import { CanonicalNode, CanonicalEdge, Dependency } from '../types';
import { Badge } from '../components/Badge';
import { Tag, Database, Link as LinkIcon, GitBranch, GitMerge, Move, ZoomIn, ZoomOut, RotateCcw, Lock } from 'lucide-react';

interface Renderer2DProps {
  nodes: CanonicalNode[];
  edges: CanonicalEdge[];
  dependencies: Dependency[];
  selectedNode: CanonicalNode | null;
  selectedEdge?: CanonicalEdge | null;
  onSelectNode: (node: CanonicalNode) => void;
  onSelectEdge?: (edge: CanonicalEdge) => void;
  viewType: 'logical' | 'execution';
}

interface Point {
  x: number;
  y: number;
}

export const Renderer2D: React.FC<Renderer2DProps> = ({
  nodes,
  edges,
  dependencies,
  selectedNode,
  selectedEdge,
  onSelectNode,
  onSelectEdge,
  viewType
}) => {
  const [zoom, setZoom] = useState<number>(1.0);
  const [pan, setPan] = useState<Point>({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState<boolean>(false);
  const [nodePositions, setNodePositions] = useState<Record<string, Point>>({});
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement | null>(null);
  const lastMouseRef = useRef<Point>({ x: 0, y: 0 });
  const dragStartNodePosRef = useRef<Point>({ x: 0, y: 0 });

  const NODE_WIDTH = 260;
  const NODE_HEIGHT = 110;
  const X_GAP = 140;
  const Y_GAP = 140;

  // Compute Initial Topological 2D Layout Positions
  useEffect(() => {
    if (nodes.length === 0) return;

    // Calculate topological ranks using in-degree / step indices
    const ranks: Record<string, number> = {};
    nodes.forEach((n, idx) => {
      const occurrenceStep = n.occurrences[0]?.occurrence_index ?? idx;
      ranks[n.id] = occurrenceStep;
    });

    // Group nodes by rank
    const sortedRanks = Array.from(new Set(Object.values(ranks))).sort((a, b) => a - b);
    const rankColumns: Record<number, CanonicalNode[]> = {};

    sortedRanks.forEach((r, colIdx) => {
      rankColumns[colIdx] = nodes.filter(n => ranks[n.id] === r);
    });

    const initialPos: Record<string, Point> = {};

    Object.entries(rankColumns).forEach(([colIdxStr, colNodes]) => {
      const colIdx = parseInt(colIdxStr, 10);
      const x = 80 + colIdx * (NODE_WIDTH + X_GAP);
      const totalColHeight = colNodes.length * NODE_HEIGHT + (colNodes.length - 1) * Y_GAP;
      const startY = Math.max(80, 260 - totalColHeight / 2);

      colNodes.forEach((node, idxInCol) => {
        initialPos[node.id] = {
          x,
          y: startY + idxInCol * (NODE_HEIGHT + Y_GAP)
        };
      });
    });

    setNodePositions(initialPos);
  }, [nodes, edges]);

  const getMethodBadgeVariant = (method: string) => {
    switch (method.toUpperCase()) {
      case 'GET': return 'info';
      case 'POST': return 'success';
      case 'PUT': case 'PATCH': return 'warning';
      case 'DELETE': return 'danger';
      default: return 'secondary';
    }
  };

  // Canvas Mouse / Pan / Drag Handlers
  const handleCanvasMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.node-card')) return;
    setIsPanning(true);
    lastMouseRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleNodeMouseDown = (e: React.MouseEvent, nodeId: string) => {
    e.stopPropagation();
    setDraggingNodeId(nodeId);
    lastMouseRef.current = { x: e.clientX, y: e.clientY };
    dragStartNodePosRef.current = nodePositions[nodeId] || { x: 0, y: 0 };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const dx = e.clientX - lastMouseRef.current.x;
    const dy = e.clientY - lastMouseRef.current.y;

    if (draggingNodeId) {
      setNodePositions(prev => ({
        ...prev,
        [draggingNodeId]: {
          x: (prev[draggingNodeId]?.x || 0) + dx / zoom,
          y: (prev[draggingNodeId]?.y || 0) + dy / zoom
        }
      }));
      lastMouseRef.current = { x: e.clientX, y: e.clientY };
    } else if (isPanning) {
      setPan(prev => ({ x: prev.x + dx, y: prev.y + dy }));
      lastMouseRef.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handleMouseUp = () => {
    setIsPanning(false);
    setDraggingNodeId(null);
  };

  const handleZoomIn = () => setZoom(prev => Math.min(2.2, prev + 0.15));
  const handleZoomOut = () => setZoom(prev => Math.max(0.35, prev - 0.15));
  const handleReset = () => {
    setZoom(1.0);
    setPan({ x: 0, y: 0 });
  };

  return (
    <div className="relative w-full h-[580px] bg-slate-950 border border-slate-800 rounded-lg overflow-hidden flex flex-col font-mono text-xs select-none shadow-2xl">
      {/* Canvas Top Bar Controls */}
      <div className="absolute top-3 left-3 z-20 flex flex-wrap items-center gap-2 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded border border-slate-800 text-[11px] text-slate-300 shadow-md">
        <button onClick={handleZoomIn} className="p-1 rounded hover:bg-slate-800 text-cyan-400" title="Zoom In">
          <ZoomIn size={14} />
        </button>
        <button onClick={handleZoomOut} className="p-1 rounded hover:bg-slate-800 text-cyan-400" title="Zoom Out">
          <ZoomOut size={14} />
        </button>
        <span className="font-bold text-slate-400 px-1">{Math.round(zoom * 100)}%</span>
        <button onClick={handleReset} className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white" title="Reset Camera & Layout">
          <RotateCcw size={14} />
        </button>
        <div className="h-3 w-px bg-slate-800 mx-1"></div>
        <span className="text-slate-500 text-[10px] flex items-center gap-1">
          <Move size={12} className="text-cyan-400" />
          <span>Pan: Drag Canvas • Move: Drag Node Cards</span>
        </span>
      </div>

      {/* Main Interactive Canvas Area */}
      <div
        ref={containerRef}
        onMouseDown={handleCanvasMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className={`w-full h-full relative overflow-hidden ${
          isPanning ? 'cursor-grabbing' : 'cursor-grab'
        }`}
      >
        {/* Scaled & Panned Graphic Layer */}
        <div
          className="absolute inset-0 origin-top-left transition-transform duration-75"
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`
          }}
        >
          {/* SVG Connection Layer for Edge Curves */}
          <svg className="absolute inset-0 w-[5000px] h-[5000px] pointer-events-none z-0">
            <defs>
              <marker id="arrow-seq" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
                <path d="M0,0 L8,4 L0,8 Z" fill="#38bdf8" />
              </marker>
              <marker id="arrow-dep" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
                <path d="M0,0 L8,4 L0,8 Z" fill="#fbbf24" />
              </marker>
              <marker id="arrow-branch" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
                <path d="M0,0 L8,4 L0,8 Z" fill="#f59e0b" />
              </marker>
              <marker id="arrow-merge" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
                <path d="M0,0 L8,4 L0,8 Z" fill="#818cf8" />
              </marker>
            </defs>

            {edges.map(edge => {
              const srcPos = nodePositions[edge.source];
              const tgtPos = nodePositions[edge.target];
              if (!srcPos || !tgtPos) return null;

              const isSelected = selectedEdge?.id === edge.id;
              const isDep = edge.edge_type === 'DEPENDENCY_TRANSITION' || edge.types?.includes('DEPENDENCY_TRANSITION');
              const isBranch = edge.edge_type === 'BRANCH' || edge.types?.includes('BRANCH');
              const isMerge = edge.edge_type === 'MERGE' || edge.types?.includes('MERGE');

              // Right port of source -> Left port of target
              const startX = srcPos.x + NODE_WIDTH;
              const startY = srcPos.y + NODE_HEIGHT / 2;
              const endX = tgtPos.x;
              const endY = tgtPos.y + NODE_HEIGHT / 2;

              // Cubic Bezier Control Points
              const deltaX = Math.abs(endX - startX) * 0.5;
              const cp1X = startX + Math.max(40, deltaX);
              const cp1Y = startY;
              const cp2X = endX - Math.max(40, deltaX);
              const cp2Y = endY;

              const pathString = `M ${startX} ${startY} C ${cp1X} ${cp1Y}, ${cp2X} ${cp2Y}, ${endX} ${endY}`;
              const midX = (startX + endX) / 2;
              const midY = (startY + endY) / 2;

              let strokeColor = '#38bdf8';
              let markerId = 'arrow-seq';
              if (isDep) {
                strokeColor = '#fbbf24';
                markerId = 'arrow-dep';
              } else if (isBranch) {
                strokeColor = '#f59e0b';
                markerId = 'arrow-branch';
              } else if (isMerge) {
                strokeColor = '#818cf8';
                markerId = 'arrow-merge';
              }

              return (
                <g key={edge.id} className="pointer-events-auto cursor-pointer" onClick={() => onSelectEdge?.(edge)}>
                  {/* Invisible wide stroke for easy clicking */}
                  <path
                    d={pathString}
                    fill="none"
                    stroke="transparent"
                    strokeWidth={18}
                  />

                  {/* Visible Edge Line */}
                  <path
                    d={pathString}
                    fill="none"
                    stroke={isSelected ? '#38bdf8' : strokeColor}
                    strokeWidth={isSelected ? 3.5 : isDep ? 2.5 : 2}
                    strokeDasharray={isDep ? '6 4' : undefined}
                    markerEnd={`url(#${markerId})`}
                    className="transition-all hover:stroke-cyan-300"
                  />

                  {/* Edge Label Badge */}
                  <foreignObject x={midX - 70} y={midY - 14} width={140} height={28} className="pointer-events-none">
                    <div className="flex items-center justify-center h-full">
                      {isDep ? (
                        <div className="flex items-center gap-1 text-[9px] font-mono px-2 py-0.5 rounded bg-amber-950/90 border border-amber-500/80 text-amber-300 font-bold shadow-md">
                          <LinkIcon size={10} />
                          <span className="truncate">{edge.dependency_details?.parameter || 'DEP'}</span>
                        </div>
                      ) : isBranch ? (
                        <div className="flex items-center gap-1 text-[9px] font-mono px-2 py-0.5 rounded bg-amber-950/80 border border-amber-600/70 text-amber-300 font-bold">
                          <GitBranch size={10} />
                          <span>BRANCH</span>
                        </div>
                      ) : isMerge ? (
                        <div className="flex items-center gap-1 text-[9px] font-mono px-2 py-0.5 rounded bg-indigo-950/80 border border-indigo-600/70 text-indigo-300 font-bold">
                          <GitMerge size={10} />
                          <span>MERGE</span>
                        </div>
                      ) : (
                        <div className="text-[8px] font-mono px-1.5 py-0.5 rounded bg-slate-900/90 border border-slate-800 text-slate-400">
                          SEQ
                        </div>
                      )}
                    </div>
                  </foreignObject>
                </g>
              );
            })}
          </svg>

          {/* HTML Node Cards Layer */}
          <div className="relative z-10 w-[5000px] h-[5000px] pointer-events-none">
            {nodes.map(node => {
              const pos = nodePositions[node.id] || { x: 100, y: 100 };
              const isSelected = selectedNode?.id === node.id;
              const isBranch = node.out_degree > 1;
              const isMerge = node.in_degree > 1;

              return (
                <div
                  key={node.id}
                  onMouseDown={e => handleNodeMouseDown(e, node.id)}
                  onClick={e => {
                    e.stopPropagation();
                    onSelectNode(node);
                  }}
                  style={{
                    left: `${pos.x}px`,
                    top: `${pos.y}px`,
                    width: `${NODE_WIDTH}px`,
                    height: `${NODE_HEIGHT}px`
                  }}
                  className={`node-card absolute pointer-events-auto cursor-grab active:cursor-grabbing p-3.5 rounded-lg border transition-all select-none shadow-xl flex flex-col justify-between ${
                    isSelected
                      ? 'bg-cyan-950/85 border-cyan-400 ring-2 ring-cyan-500/70 shadow-cyan-950/80'
                      : 'bg-slate-900/95 border-slate-800 hover:border-slate-700 hover:shadow-2xl'
                  }`}
                >
                  {/* Card Header */}
                  <div className="flex items-center justify-between gap-1.5">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <Badge variant={getMethodBadgeVariant(node.method)}>{node.method}</Badge>
                      <span className="text-xs font-mono font-bold text-slate-100 truncate" title={node.path_template}>
                        {viewType === 'logical' ? node.path_template : node.actual_path}
                      </span>
                    </div>

                    <div className="flex items-center gap-1 flex-shrink-0">
                      {isBranch && (
                        <span className="px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-600/70 text-[9px] font-bold flex items-center gap-0.5">
                          <GitBranch size={9} />
                          <span>{node.out_degree}</span>
                        </span>
                      )}
                      {isMerge && (
                        <span className="px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-600/70 text-[9px] font-bold flex items-center gap-0.5">
                          <GitMerge size={9} />
                          <span>{node.in_degree}</span>
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Card Metadata Details */}
                  <div className="text-[10px] font-mono text-slate-400 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="truncate text-slate-400">
                        Op: <strong className="text-cyan-400">{node.operation_id || 'unmapped'}</strong>
                      </span>
                      <span className="text-[9px] text-slate-500 font-bold px-1 rounded bg-slate-950 border border-slate-800">
                        {node.occurrences.length} {node.occurrences.length === 1 ? 'occ' : 'occs'}
                      </span>
                    </div>

                    {node.resource_identifier ? (
                      <div className="flex items-center gap-1 text-amber-400 font-bold text-[10px] pt-1 border-t border-slate-800/80">
                        <Database size={11} />
                        <span className="truncate">{node.resource_type}:{node.resource_identifier}</span>
                      </div>
                    ) : (
                      <div className="text-[9px] text-slate-500 pt-1 border-t border-slate-800/50 flex justify-between">
                        <span>In: {node.in_degree}</span>
                        <span>Out: {node.out_degree}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
