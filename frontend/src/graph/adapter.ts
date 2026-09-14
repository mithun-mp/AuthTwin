import { WorkflowGraphResponse, CanonicalGraph, CanonicalNode, CanonicalEdge } from '../types';

export const adaptWorkflowResponseToCanonicalGraph = (
  response: WorkflowGraphResponse
): CanonicalGraph => {
  if (response.canonical_graph && response.canonical_graph.nodes.length > 0) {
    return response.canonical_graph;
  }

  if (response.canonical_nodes && response.canonical_nodes.length > 0) {
    return {
      nodes: response.canonical_nodes,
      edges: response.canonical_edges || []
    };
  }

  // Fallback translation for legacy responses
  const nodes: CanonicalNode[] = (response.nodes || []).map(n => ({
    id: n.id,
    logical_node_id: n.operation_id || n.id,
    occurrence_id: `occ-${n.transaction_id.slice(0, 8)}`,
    linear_step_id: `step-${n.sequence_index}`,
    transaction_id: n.transaction_id,
    method: n.method,
    path_template: n.path_template,
    actual_path: n.actual_path,
    operation_id: n.operation_id,
    resource_type: n.resource_type,
    resource_identifier: n.resource_identifier,
    in_degree: 0,
    out_degree: 0,
    occurrences: [{
      occurrence_index: n.sequence_index,
      transaction_id: n.transaction_id,
      timestamp: new Date().toISOString(),
      res_status: 200
    }]
  }));

  const edges: CanonicalEdge[] = (response.edges || []).map(e => ({
    id: e.id,
    source: e.source_node_id,
    target: e.target_node_id,
    edge_type: (e.transition_type as any) || 'SEQUENCE',
    dependency_id: e.dependency_id,
    confidence: 1.0
  }));

  // Calculate degrees
  nodes.forEach(node => {
    node.in_degree = edges.filter(e => e.target === node.id).length;
    node.out_degree = edges.filter(e => e.source === node.id).length;
  });

  return { nodes, edges };
};
