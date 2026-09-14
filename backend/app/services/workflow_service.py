import hashlib
import uuid
import datetime
import networkx as nx
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session as DBSession
from app.models.models import Session, Transaction, Dependency, Workflow, WorkflowNode, WorkflowEdge
from app.schemas.schemas import (
    LinearWorkflowResponse, LinearStepSchema,
    CanonicalNodeSchema, CanonicalEdgeSchema, CanonicalOccurrenceSummary,
    DependencyBindingSchema, EdgeEvidenceSchema, GraphMetadataSchema, CanonicalGraphSchema,
    WorkflowResponse, WorkflowGraphResponse, WorkflowNodeResponse,
    WorkflowEdgeResponse, DependencyResponse
)
from app.core.logging import logger

def hash_deterministic_id(prefix: str, *args: str) -> str:
    """Generates a 100% deterministic SHA-256 derived identifier for graph nodes and edges."""
    raw = ":".join(str(a) for a in args)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def infer_resource_info(tx: Transaction) -> Tuple[Optional[str], Optional[str]]:
    """Infers resource type (e.g. project, document) and resource ID from transaction path."""
    parts = [p for p in tx.path.split("/") if p]
    if not parts:
        return None, None

    resource_type = None
    resource_id = None

    for idx, part in enumerate(parts):
        if part.isdigit() or len(part) > 20 or "-" in part:
            resource_id = part
            if idx > 0:
                resource_type = parts[idx - 1].rstrip("s")  # singularize simple plural
            break

    if not resource_type and parts:
        resource_type = parts[0].rstrip("s")

    return resource_type, resource_id


def normalize_path_template(path: str, resource_type: Optional[str] = None) -> str:
    """Normalizes raw path segments (e.g. /projects/101 -> /projects/{id})."""
    parts = [p for p in path.split("/") if p]
    normalized = []
    for p in parts:
        if p.isdigit() or len(p) > 20 or "-" in p:
            placeholder = f"{{{resource_type}_id}}" if resource_type else "{id}"
            normalized.append(placeholder)
        else:
            normalized.append(p)
    return "/" + "/".join(normalized) if normalized else "/"


def build_linear_workflow(
    workflow_id: str,
    session_obj: Session,
    transactions: List[Transaction],
    dependencies: List[Dependency]
) -> LinearWorkflowResponse:
    """
    Constructs the authoritative Linear Workflow Representation for deterministic replay and shadow generation.
    Preserves exact chronological execution order and occurrence identities without collapsing steps.
    """
    dep_by_consumer = {}
    for d in dependencies:
        dep_by_consumer.setdefault(d.consumer_transaction_id, []).append({
            "dependency_id": d.id,
            "producer_transaction_id": d.producer_transaction_id,
            "producer_field_path": d.producer_field_path,
            "consumer_field_location": d.consumer_field_location,
            "consumer_field_name": d.consumer_field_name,
            "extracted_value": d.extracted_value,
            "dependency_type": d.dependency_type,
            "confidence": d.confidence
        })

    steps: List[LinearStepSchema] = []
    for idx, tx in enumerate(transactions):
        res_type, res_id = infer_resource_info(tx)
        step = LinearStepSchema(
            step_index=idx,
            occurrence_id=f"occ-{idx}-{hashlib.sha256(tx.id.encode()).hexdigest()[:8]}",
            transaction_id=tx.id,
            method=tx.method,
            path=tx.path,
            url=tx.url,
            operation_id=tx.operation_id or f"{tx.method.lower()}_{tx.path}",
            resource_type=res_type,
            resource_identifier=res_id,
            req_body=tx.req_body,
            res_status=tx.res_status,
            res_body=tx.res_body,
            dependencies=dep_by_consumer.get(tx.id, []),
            replay_eligible=True
        )
        steps.append(step)

    return LinearWorkflowResponse(
        workflow_id=workflow_id,
        session_id=session_obj.id,
        identity_id=session_obj.identity_id,
        name=f"Linear Workflow - {session_obj.name}",
        created_at=session_obj.started_at or datetime.datetime.utcnow(),
        steps=steps
    )


def validate_canonical_graph(nodes: List[CanonicalNodeSchema], edges: List[CanonicalEdgeSchema]) -> None:
    """Validates structural integrity, degree counts, and connectivity of the canonical graph."""
    node_ids = {n.id for n in nodes}
    for e in edges:
        if e.source not in node_ids:
            raise ValueError(f"Canonical Graph Edge {e.id} has invalid source node {e.source}")
        if e.target not in node_ids:
            raise ValueError(f"Canonical Graph Edge {e.id} has invalid target node {e.target}")

    for n in nodes:
        actual_in = sum(1 for e in edges if e.target == n.id)
        actual_out = sum(1 for e in edges if e.source == n.id)
        if n.in_degree != actual_in:
            raise ValueError(f"Node {n.id} in_degree mismatch: expected {n.in_degree}, got {actual_in}")
        if n.out_degree != actual_out:
            raise ValueError(f"Node {n.id} out_degree mismatch: expected {n.out_degree}, got {actual_out}")


def build_canonical_graph(
    workflow_id: str,
    transactions: List[Transaction],
    dependencies: List[Dependency]
) -> Tuple[List[CanonicalNodeSchema], List[CanonicalEdgeSchema], GraphMetadataSchema]:
    """
    Constructs the authoritative Canonical Hybrid Hierarchical Graph Representation for 2D/3D visualization.
    Distinguishes Logical Nodes from Execution Occurrences and preserves 1->1, 1->N (Branch), N->1 (Merge), N->N,
    and non-consecutive dependency transitions.
    """
    if not transactions:
        return [], [], GraphMetadataSchema()

    # Map transaction ID to step index
    tx_to_idx = {tx.id: idx for idx, tx in enumerate(transactions)}

    # Group occurrences into logical nodes based on method and normalized route template
    logical_nodes_map: Dict[str, Dict[str, Any]] = {}
    tx_to_logical_id: Dict[str, str] = {}

    for idx, tx in enumerate(transactions):
        res_type, res_id = infer_resource_info(tx)
        path_tmpl = tx.operation_id if (tx.operation_id and "/" in tx.operation_id) else normalize_path_template(tx.path, res_type)
        
        logical_key = f"{tx.method.upper()}:{path_tmpl}"
        
        if logical_key not in logical_nodes_map:
            logical_id = hash_deterministic_id("node", tx.method.upper(), path_tmpl)
            logical_nodes_map[logical_key] = {
                "id": logical_id,
                "logical_node_id": logical_id,
                "method": tx.method.upper(),
                "path_template": path_tmpl,
                "actual_path": tx.path,
                "operation_id": tx.operation_id or f"{tx.method.lower()}_{tx.path}",
                "resource_type": res_type,
                "resource_identifier": res_id,
                "occurrences": [],
                "first_tx_id": tx.id
            }
        
        node_entry = logical_nodes_map[logical_key]
        node_entry["occurrences"].append(CanonicalOccurrenceSummary(
            occurrence_index=idx,
            transaction_id=tx.id,
            timestamp=tx.timestamp or datetime.datetime.utcnow(),
            res_status=tx.res_status
        ))
        tx_to_logical_id[tx.id] = node_entry["id"]

    # Build graph edges between logical nodes
    G = nx.DiGraph()
    for n in logical_nodes_map.values():
        G.add_node(n["id"])

    edge_data_map: Dict[Tuple[str, str], Dict[str, Any]] = {}

    # 1. Add sequential step transitions between consecutive steps
    for idx in range(len(transactions) - 1):
        src_tx = transactions[idx]
        tgt_tx = transactions[idx + 1]
        
        src_logical = tx_to_logical_id[src_tx.id]
        tgt_logical = tx_to_logical_id[tgt_tx.id]

        if src_logical != tgt_logical:
            pair = (src_logical, tgt_logical)
            if pair not in edge_data_map:
                edge_data_map[pair] = {
                    "source": src_logical,
                    "target": tgt_logical,
                    "types": set(["SEQUENCE"]),
                    "source_occurrences": set([src_tx.id]),
                    "target_occurrences": set([tgt_tx.id]),
                    "bindings": [],
                    "dependency_id": None,
                    "dependency_details": None,
                    "confidence": 1.0,
                    "step_distance": 1
                }
            else:
                edge_data_map[pair]["source_occurrences"].add(src_tx.id)
                edge_data_map[pair]["target_occurrences"].add(tgt_tx.id)
            G.add_edge(src_logical, tgt_logical)

    # 2. Add Data Dependency Transitions (including non-consecutive transitions)
    for dep in dependencies:
        src_tx_id = dep.producer_transaction_id
        tgt_tx_id = dep.consumer_transaction_id
        src_logical = tx_to_logical_id.get(src_tx_id)
        tgt_logical = tx_to_logical_id.get(tgt_tx_id)

        if src_logical and tgt_logical and src_logical != tgt_logical:
            pair = (src_logical, tgt_logical)
            src_idx = tx_to_idx.get(src_tx_id, 0)
            tgt_idx = tx_to_idx.get(tgt_tx_id, 0)
            dist = max(1, tgt_idx - src_idx)

            binding = DependencyBindingSchema(
                producer_location="response.body",
                producer_path=dep.producer_field_path,
                consumer_location=dep.consumer_field_location,
                consumer_parameter=dep.consumer_field_name,
                extracted_value=dep.extracted_value
            )

            dep_details = {
                "parameter": dep.consumer_field_name,
                "producer_field": dep.producer_field_path,
                "consumer_field": f"{dep.consumer_field_location}:{dep.consumer_field_name}",
                "extracted_value": dep.extracted_value,
                "dependency_type": dep.dependency_type
            }

            if pair not in edge_data_map:
                edge_data_map[pair] = {
                    "source": src_logical,
                    "target": tgt_logical,
                    "types": set(["DEPENDENCY_TRANSITION"]),
                    "source_occurrences": set([src_tx_id]),
                    "target_occurrences": set([tgt_tx_id]),
                    "bindings": [binding],
                    "dependency_id": dep.id,
                    "dependency_details": dep_details,
                    "confidence": dep.confidence,
                    "step_distance": dist
                }
            else:
                edge_data_map[pair]["types"].add("DEPENDENCY_TRANSITION")
                edge_data_map[pair]["dependency_id"] = dep.id
                edge_data_map[pair]["dependency_details"] = dep_details
                edge_data_map[pair]["confidence"] = dep.confidence
                edge_data_map[pair]["step_distance"] = min(edge_data_map[pair]["step_distance"], dist)
                edge_data_map[pair]["source_occurrences"].add(src_tx_id)
                edge_data_map[pair]["target_occurrences"].add(tgt_tx_id)
                # Avoid duplicate bindings for same parameter
                existing_params = {b.consumer_parameter for b in edge_data_map[pair]["bindings"]}
                if dep.consumer_field_name not in existing_params:
                    edge_data_map[pair]["bindings"].append(binding)

            G.add_edge(src_logical, tgt_logical)

    # 3. Classify Branching and Merging topology edge types
    for node_id in G.nodes():
        out_deg = G.out_degree(node_id)
        in_deg = G.in_degree(node_id)
        
        if out_deg > 1:
            for _, target_id in G.out_edges(node_id):
                pair = (node_id, target_id)
                if pair in edge_data_map:
                    edge_data_map[pair]["types"].add("BRANCH")
                    
        if in_deg > 1:
            for source_id, _ in G.in_edges(node_id):
                pair = (source_id, node_id)
                if pair in edge_data_map:
                    edge_data_map[pair]["types"].add("MERGE")

    # Build Canonical Nodes
    canonical_nodes: List[CanonicalNodeSchema] = []
    for entry in logical_nodes_map.values():
        nid = entry["id"]
        c_node = CanonicalNodeSchema(
            id=nid,
            logical_node_id=entry["logical_node_id"],
            occurrence_id=f"occ-0-{entry['first_tx_id'][:8]}",
            transaction_id=entry["first_tx_id"],
            method=entry["method"],
            path_template=entry["path_template"],
            actual_path=entry["actual_path"],
            operation_id=entry["operation_id"],
            resource_type=entry["resource_type"],
            resource_identifier=entry["resource_identifier"],
            in_degree=G.in_degree(nid) if G.has_node(nid) else 0,
            out_degree=G.out_degree(nid) if G.has_node(nid) else 0,
            occurrences=entry["occurrences"]
        )
        canonical_nodes.append(c_node)

    # Build Canonical Edges
    canonical_edges: List[CanonicalEdgeSchema] = []
    branch_count = 0
    merge_count = 0
    dep_edge_count = 0
    seq_edge_count = 0

    for (src, tgt), edata in edge_data_map.items():
        types_list = sorted(list(edata["types"]))
        # Primary edge type precedence: DEPENDENCY_TRANSITION > BRANCH > MERGE > SEQUENCE
        if "DEPENDENCY_TRANSITION" in types_list:
            primary_type = "DEPENDENCY_TRANSITION"
            dep_edge_count += 1
        elif "BRANCH" in types_list:
            primary_type = "BRANCH"
            branch_count += 1
        elif "MERGE" in types_list:
            primary_type = "MERGE"
            merge_count += 1
        else:
            primary_type = "SEQUENCE"
            seq_edge_count += 1

        # Determine Topology Cardinality (1->1, 1->N, N->1, N->N)
        src_occ_cnt = len(edata["source_occurrences"])
        tgt_occ_cnt = len(edata["target_occurrences"])
        src_out_deg = G.out_degree(src) if G.has_node(src) else 1
        tgt_in_deg = G.in_degree(tgt) if G.has_node(tgt) else 1

        if src_occ_cnt > 1 and tgt_occ_cnt > 1:
            cardinality = "N->N"
        elif src_occ_cnt > 1 or src_out_deg > 1:
            cardinality = "1->N"
        elif tgt_occ_cnt > 1 or tgt_in_deg > 1:
            cardinality = "N->1"
        else:
            cardinality = "1->1"

        reason_text = "Parameter dependency payload binding" if edata["bindings"] else f"Proven transition from {src} to {tgt}"
        evidence = EdgeEvidenceSchema(
            reason=reason_text,
            confidence=edata["confidence"],
            step_distance=edata["step_distance"]
        )

        edge_id = hash_deterministic_id("edge", src, tgt, primary_type)
        c_edge = CanonicalEdgeSchema(
            id=edge_id,
            source=src,
            target=tgt,
            edge_type=primary_type,
            relation_type=primary_type,
            cardinality=cardinality,
            types=types_list,
            source_occurrences=sorted(list(edata["source_occurrences"])),
            target_occurrences=sorted(list(edata["target_occurrences"])),
            bindings=edata["bindings"],
            evidence=evidence,
            dependency_id=edata["dependency_id"],
            dependency_details=edata["dependency_details"],
            confidence=edata["confidence"],
            step_distance=edata["step_distance"]
        )
        canonical_edges.append(c_edge)

    # Validate graph integrity
    validate_canonical_graph(canonical_nodes, canonical_edges)

    # Calculate Graph Metadata
    max_in = max((n.in_degree for n in canonical_nodes), default=0)
    return canonical_nodes, canonical_edges


def generate_workflow_state_graph(db: DBSession, session_id: str) -> Workflow:
    """
    Generates Workflow State Graph (WSG) for a session, constructing BOTH:
    1. Linear Workflow Representation (replay authority)
    2. Canonical Hybrid Hierarchical Graph Representation (visualization authority)
    Persists Workflow, Nodes, and Edges to database.
    """
    session_obj = db.query(Session).filter(Session.id == session_id).first()
    if not session_obj:
        raise ValueError(f"Session {session_id} not found")

    transactions = (
        db.query(Transaction)
        .filter(Transaction.session_id == session_id)
        .order_by(Transaction.timestamp.asc())
        .all()
    )

    if not transactions:
        raise ValueError(f"No transactions found for session {session_id}")

    tx_ids = [t.id for t in transactions]
    dependencies = (
        db.query(Dependency)
        .filter(Dependency.producer_transaction_id.in_(tx_ids))
        .all()
    )

    # Remove existing workflow for this session if re-generating
    existing_wf = db.query(Workflow).filter(Workflow.session_id == session_id).first()
    if existing_wf:
        db.delete(existing_wf)
        db.commit()

    workflow_obj = Workflow(
        id=str(uuid.uuid4()),
        session_id=session_id,
        identity_id=session_obj.identity_id,
        name=f"Workflow - {session_obj.name}",
        node_count=len(transactions),
        edge_count=0
    )
    db.add(workflow_obj)
    db.flush()

    # Build DB nodes and edges
    created_nodes: List[WorkflowNode] = []
    tx_to_node_map: Dict[str, WorkflowNode] = {}

    for idx, tx in enumerate(transactions):
        res_type, res_id = infer_resource_info(tx)
        node_obj = WorkflowNode(
            id=str(uuid.uuid4()),
            workflow_id=workflow_obj.id,
            sequence_index=idx,
            transaction_id=tx.id,
            operation_id=tx.operation_id or f"{tx.method.lower()}_{tx.path}",
            method=tx.method,
            path_template=tx.path,
            actual_path=tx.path,
            resource_type=res_type,
            resource_identifier=res_id
        )
        db.add(node_obj)
        created_nodes.append(node_obj)
        tx_to_node_map[tx.id] = node_obj

    db.flush()

    created_edges: List[WorkflowEdge] = []
    dep_map = {(d.producer_transaction_id, d.consumer_transaction_id): d for d in dependencies}

    for idx in range(len(created_nodes) - 1):
        src_node = created_nodes[idx]
        tgt_node = created_nodes[idx + 1]
        dep = dep_map.get((src_node.transaction_id, tgt_node.transaction_id))

        edge_obj = WorkflowEdge(
            id=str(uuid.uuid4()),
            workflow_id=workflow_obj.id,
            source_node_id=src_node.id,
            target_node_id=tgt_node.id,
            transition_type="DEPENDENCY_TRANSITION" if dep else "SEQUENCE",
            dependency_id=dep.id if dep else None
        )
        db.add(edge_obj)
        created_edges.append(edge_obj)

    workflow_obj.edge_count = len(created_edges)
    db.commit()

    logger.info(f"Generated WSG Workflow {workflow_obj.id}: {workflow_obj.node_count} nodes, {workflow_obj.edge_count} edges.")
    return workflow_obj


def get_workflow_graph_details(db: DBSession, workflow_id: str) -> WorkflowGraphResponse:
    """
    Returns complete Workflow Graph payload containing BOTH Linear Workflow and Canonical Hybrid Graph.
    """
    wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not wf:
        raise ValueError(f"Workflow {workflow_id} not found")

    session_obj = db.query(Session).filter(Session.id == wf.session_id).first()
    nodes = db.query(WorkflowNode).filter(WorkflowNode.workflow_id == workflow_id).order_by(WorkflowNode.sequence_index.asc()).all()
    edges = db.query(WorkflowEdge).filter(WorkflowEdge.workflow_id == workflow_id).all()

    tx_ids = [n.transaction_id for n in nodes]
    transactions = db.query(Transaction).filter(Transaction.id.in_(tx_ids)).order_by(Transaction.timestamp.asc()).all()
    dependencies = db.query(Dependency).filter(Dependency.producer_transaction_id.in_(tx_ids)).all()

    linear_wf = build_linear_workflow(wf.id, session_obj, transactions, dependencies)
    c_nodes, c_edges = build_canonical_graph(wf.id, transactions, dependencies)
    c_metadata = GraphMetadataSchema(
        node_count=len(c_nodes),
        edge_count=len(c_edges),
        dependency_edge_count=sum(1 for e in c_edges if e.edge_type == "DEPENDENCY_TRANSITION"),
        sequence_edge_count=sum(1 for e in c_edges if e.edge_type == "SEQUENCE"),
        branch_count=sum(1 for e in c_edges if "BRANCH" in (e.types or []) or e.edge_type == "BRANCH"),
        merge_count=sum(1 for e in c_edges if "MERGE" in (e.types or []) or e.edge_type == "MERGE"),
        max_in_degree=max((n.in_degree for n in c_nodes), default=0),
        max_out_degree=max((n.out_degree for n in c_nodes), default=0)
    )
    c_graph = CanonicalGraphSchema(nodes=c_nodes, edges=c_edges, metadata=c_metadata)

    node_responses = [WorkflowNodeResponse.model_validate(n) for n in nodes]
    edge_responses = [WorkflowEdgeResponse.model_validate(e) for e in edges]
    dep_responses = [DependencyResponse.model_validate(d) for d in dependencies]

    return WorkflowGraphResponse(
        workflow=WorkflowResponse.model_validate(wf),
        linear_workflow=linear_wf,
        nodes=node_responses,
        edges=edge_responses,
        canonical_nodes=c_nodes,
        canonical_edges=c_edges,
        canonical_graph=c_graph,
        dependencies=dep_responses
    )
