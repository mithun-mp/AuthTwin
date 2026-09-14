export interface Target {
  id: string;
  name: string;
  base_url: string;
  allowed_host_regex?: string;
  created_at: string;
}

export interface Identity {
  id: string;
  target_id: string;
  name: string;
  role: 'Primary' | 'Alternate';
  auth_type: string;
  created_at: string;
}

export interface Session {
  id: string;
  target_id: string;
  identity_id?: string;
  name: string;
  token_fingerprint?: string;
  status: string;
  started_at: string;
}

export interface Transaction {
  id: string;
  session_id: string;
  timestamp: string;
  method: string;
  url: string;
  path: string;
  query_params?: Record<string, any>;
  req_headers?: Record<string, any>;
  req_body?: string;
  res_status: number;
  res_headers?: Record<string, any>;
  res_body?: string;
  operation_id?: string;
}

export interface OpenAPIOperation {
  id: string;
  operation_id: string;
  method: string;
  path_template: string;
  summary?: string;
}

export interface OpenAPISpec {
  id: string;
  target_id: string;
  title: string;
  version: string;
  created_at: string;
  operations: OpenAPIOperation[];
}

export interface Dependency {
  id: string;
  producer_transaction_id: string;
  consumer_transaction_id: string;
  producer_field_path: string;
  consumer_field_location: string;
  consumer_field_name: string;
  extracted_value: string;
  dependency_type: string;
  confidence: number;
}

export interface LinearStep {
  step_index: number;
  occurrence_id: string;
  transaction_id: string;
  method: string;
  path: string;
  url: string;
  operation_id?: string;
  resource_type?: string;
  resource_identifier?: string;
  req_body?: string;
  res_status: number;
  res_body?: string;
  dependencies: Record<string, any>[];
  replay_eligible: boolean;
  param_bindings?: DependencyBinding[];
  canonical_node_id?: string;
}

export interface LinearWorkflow {
  workflow_id: string;
  session_id: string;
  identity_id: string;
  name: string;
  created_at: string;
  steps: LinearStep[];
}

export interface CanonicalOccurrenceSummary {
  occurrence_index: number;
  transaction_id: string;
  timestamp: string;
  res_status: number;
}

export interface CanonicalNode {
  id: string;
  logical_node_id: string;
  occurrence_id?: string;
  linear_step_id?: string;
  transaction_id?: string;
  method: string;
  path_template: string;
  actual_path: string;
  operation_id?: string;
  resource_type?: string;
  resource_identifier?: string;
  in_degree: number;
  out_degree: number;
  occurrences: CanonicalOccurrenceSummary[];
}

export interface DependencyBinding {
  producer_location: string;
  producer_path: string;
  consumer_location: string;
  consumer_parameter: string;
  extracted_value: string;
}

export interface EdgeEvidence {
  reason: string;
  confidence: number;
  step_distance: number;
}

export interface CanonicalEdge {
  id: string;
  source: string;
  target: string;
  edge_type: 'SEQUENCE' | 'DEPENDENCY_TRANSITION' | 'BRANCH' | 'MERGE' | 'RESOURCE_LINEAGE';
  relation_type?: string;
  cardinality?: '1->1' | '1->N' | 'N->1' | 'N->N';
  types?: string[];
  source_occurrences?: string[];
  target_occurrences?: string[];
  bindings?: DependencyBinding[];
  evidence?: EdgeEvidence;
  dependency_id?: string;
  dependency_details?: {
    parameter?: string;
    producer_field?: string;
    consumer_field?: string;
    extracted_value?: string;
    dependency_type?: string;
  };
  confidence?: number;
  step_distance?: number;
}

export interface GraphMetadata {
  node_count: number;
  edge_count: number;
  dependency_edge_count: number;
  sequence_edge_count: number;
  branch_count: number;
  merge_count: number;
  max_in_degree: number;
  max_out_degree: number;
}

export interface CanonicalGraph {
  nodes: CanonicalNode[];
  edges: CanonicalEdge[];
  metadata?: GraphMetadata;
}

export interface WorkflowNode {
  id: string;
  workflow_id: string;
  sequence_index: number;
  transaction_id: string;
  operation_id?: string;
  method: string;
  path_template: string;
  actual_path: string;
  resource_type?: string;
  resource_identifier?: string;
}

export interface WorkflowEdge {
  id: string;
  workflow_id: string;
  source_node_id: string;
  target_node_id: string;
  transition_type: string;
  dependency_id?: string;
}

export interface Workflow {
  id: string;
  session_id: string;
  identity_id: string;
  name: string;
  node_count: number;
  edge_count: number;
  created_at: string;
}

export interface WorkflowGraphResponse {
  workflow: Workflow;
  linear_workflow: LinearWorkflow;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  canonical_nodes: CanonicalNode[];
  canonical_edges: CanonicalEdge[];
  canonical_graph?: CanonicalGraph;
  dependencies: Dependency[];
}

export interface ShadowWorkflow {
  id: string;
  source_workflow_id: string;
  source_identity_id: string;
  shadow_identity_id: string;
  clone_policy: string;
  status: string;
  created_at: string;
}
