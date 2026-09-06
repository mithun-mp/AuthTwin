import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from app.database import Base

class Target(Base):
    __tablename__ = "targets"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    allowed_host_regex = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    identities = relationship("Identity", back_populates="target", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="target", cascade="all, delete-orphan")
    specs = relationship("OpenAPISpec", back_populates="target", cascade="all, delete-orphan")


class Identity(Base):
    __tablename__ = "identities"
    
    id = Column(String, primary_key=True, index=True)
    target_id = Column(String, ForeignKey("targets.id"), nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="Primary") # Primary or Alternate
    auth_type = Column(String, default="Bearer")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    target = relationship("Target", back_populates="identities")
    sessions = relationship("Session", back_populates="identity", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, index=True)
    target_id = Column(String, ForeignKey("targets.id"), nullable=False)
    identity_id = Column(String, ForeignKey("identities.id"), nullable=True)
    name = Column(String, nullable=False)
    token_fingerprint = Column(String, nullable=True)
    status = Column(String, default="ACTIVE")
    started_at = Column(DateTime, default=datetime.datetime.utcnow)

    target = relationship("Target", back_populates="sessions")
    identity = relationship("Identity", back_populates="sessions")
    transactions = relationship("Transaction", back_populates="session", cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="session", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    method = Column(String, nullable=False)
    url = Column(String, nullable=False)
    path = Column(String, nullable=False)
    query_params = Column(JSON, nullable=True)
    req_headers = Column(JSON, nullable=True) # Redacted
    req_body = Column(Text, nullable=True)
    res_status = Column(Integer, nullable=False)
    res_headers = Column(JSON, nullable=True)
    res_body = Column(Text, nullable=True)
    operation_id = Column(String, nullable=True)

    session = relationship("Session", back_populates="transactions")


class OpenAPISpec(Base):
    __tablename__ = "openapi_specs"
    
    id = Column(String, primary_key=True, index=True)
    target_id = Column(String, ForeignKey("targets.id"), nullable=False)
    title = Column(String, nullable=False)
    version = Column(String, nullable=False)
    spec_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    target = relationship("Target", back_populates="specs")
    operations = relationship("OpenAPIOperation", back_populates="spec", cascade="all, delete-orphan")


class OpenAPIOperation(Base):
    __tablename__ = "openapi_operations"
    
    id = Column(String, primary_key=True, index=True)
    spec_id = Column(String, ForeignKey("openapi_specs.id"), nullable=False)
    operation_id = Column(String, nullable=False)
    method = Column(String, nullable=False)
    path_template = Column(String, nullable=False)
    summary = Column(String, nullable=True)
    parameters_schema = Column(JSON, nullable=True)
    responses_schema = Column(JSON, nullable=True)

    spec = relationship("OpenAPISpec", back_populates="operations")


class Dependency(Base):
    __tablename__ = "dependencies"
    
    id = Column(String, primary_key=True, index=True)
    producer_transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    consumer_transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    producer_field_path = Column(String, nullable=False) # e.g. "response.body.id"
    consumer_field_location = Column(String, nullable=False) # e.g. "PATH", "QUERY", "BODY", "HEADER"
    consumer_field_name = Column(String, nullable=False) # e.g. "project_id"
    extracted_value = Column(String, nullable=False)
    dependency_type = Column(String, nullable=False) # RESPONSE_TO_PATH, RESPONSE_TO_QUERY, etc.
    confidence = Column(Float, default=1.0)


class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    identity_id = Column(String, ForeignKey("identities.id"), nullable=False)
    name = Column(String, nullable=False)
    node_count = Column(Integer, default=0)
    edge_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("Session", back_populates="workflows")
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    edges = relationship("WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowNode(Base):
    __tablename__ = "workflow_nodes"
    
    id = Column(String, primary_key=True, index=True)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    sequence_index = Column(Integer, nullable=False)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    operation_id = Column(String, nullable=True)
    method = Column(String, nullable=False)
    path_template = Column(String, nullable=False)
    actual_path = Column(String, nullable=False)
    resource_type = Column(String, nullable=True)
    resource_identifier = Column(String, nullable=True)

    workflow = relationship("Workflow", back_populates="nodes")


class WorkflowEdge(Base):
    __tablename__ = "workflow_edges"
    
    id = Column(String, primary_key=True, index=True)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    source_node_id = Column(String, ForeignKey("workflow_nodes.id"), nullable=False)
    target_node_id = Column(String, ForeignKey("workflow_nodes.id"), nullable=False)
    transition_type = Column(String, default="SEQUENCE") # SEQUENCE or DEPENDENCY_TRANSITION
    dependency_id = Column(String, ForeignKey("dependencies.id"), nullable=True)

    workflow = relationship("Workflow", back_populates="edges")


class ShadowWorkflow(Base):
    __tablename__ = "shadow_workflows"
    
    id = Column(String, primary_key=True, index=True)
    source_workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    source_identity_id = Column(String, ForeignKey("identities.id"), nullable=False)
    shadow_identity_id = Column(String, ForeignKey("identities.id"), nullable=False)
    clone_policy = Column(String, default="CREDENTIAL_ISOLATED")
    status = Column(String, default="MODEL_ONLY") # MODEL_ONLY
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
