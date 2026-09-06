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
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
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
