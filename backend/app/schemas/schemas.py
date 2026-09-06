import datetime
from typing import Optional, Any, List, Dict
from pydantic import BaseModel, Field

# Target
class TargetBase(BaseModel):
    name: str
    base_url: str
    allowed_host_regex: Optional[str] = None

class TargetCreate(TargetBase):
    pass

class TargetResponse(TargetBase):
    id: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# Identity
class IdentityBase(BaseModel):
    name: str
    role: str = "Primary" # Primary or Alternate
    auth_type: str = "Bearer"

class IdentityCreate(IdentityBase):
    target_id: Optional[str] = None

class IdentityResponse(IdentityBase):
    id: str
    target_id: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# Session
class SessionResponse(BaseModel):
    id: str
    target_id: str
    identity_id: Optional[str] = None
    name: str
    token_fingerprint: Optional[str] = None
    status: str
    started_at: datetime.datetime

    class Config:
        from_attributes = True


# Transaction
class TransactionResponse(BaseModel):
    id: str
    session_id: str
    timestamp: datetime.datetime
    method: str
    url: str
    path: str
    query_params: Optional[Dict[str, Any]] = None
    req_headers: Optional[Dict[str, Any]] = None
    req_body: Optional[str] = None
    res_status: int
    res_headers: Optional[Dict[str, Any]] = None
    res_body: Optional[str] = None
    operation_id: Optional[str] = None

    class Config:
        from_attributes = True


# OpenAPI
class OpenAPIOperationSchema(BaseModel):
    id: str
    operation_id: str
    method: str
    path_template: str
    summary: Optional[str] = None

    class Config:
        from_attributes = True

class OpenAPISpecResponse(BaseModel):
    id: str
    target_id: str
    title: str
    version: str
    created_at: datetime.datetime
    operations: List[OpenAPIOperationSchema] = []

    class Config:
        from_attributes = True


# Dependency
class DependencyResponse(BaseModel):
    id: str
    producer_transaction_id: str
    consumer_transaction_id: str
    producer_field_path: str
    consumer_field_location: str
    consumer_field_name: str
    extracted_value: str
    dependency_type: str
    confidence: float

    class Config:
        from_attributes = True


# Workflow & Graph
class WorkflowNodeResponse(BaseModel):
    id: str
    workflow_id: str
    sequence_index: int
    transaction_id: str
    operation_id: Optional[str] = None
    method: str
    path_template: str
    actual_path: str
    resource_type: Optional[str] = None
    resource_identifier: Optional[str] = None

    class Config:
        from_attributes = True

class WorkflowEdgeResponse(BaseModel):
    id: str
    workflow_id: str
    source_node_id: str
    target_node_id: str
    transition_type: str
    dependency_id: Optional[str] = None

    class Config:
        from_attributes = True

class WorkflowResponse(BaseModel):
    id: str
    session_id: str
    identity_id: str
    name: str
    node_count: int
    edge_count: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class WorkflowGraphResponse(BaseModel):
    workflow: WorkflowResponse
    nodes: List[WorkflowNodeResponse]
    edges: List[WorkflowEdgeResponse]
    dependencies: List[DependencyResponse]


# Shadow Workflow
class ShadowWorkflowCreate(BaseModel):
    shadow_identity_id: str

class ShadowWorkflowResponse(BaseModel):
    id: str
    source_workflow_id: str
    source_identity_id: str
    shadow_identity_id: str
    clone_policy: str
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# HAR Import Result
class HARImportResult(BaseModel):
    target_id: str
    session_id: str
    imported_count: int
    skipped_count: int
    warnings: List[str]
    transactions: List[TransactionResponse]
