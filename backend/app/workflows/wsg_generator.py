import uuid
import networkx as nx
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session as DBSession
from app.models import Session, Transaction, Dependency, Workflow, WorkflowNode, WorkflowEdge
from app.logging import logger

def infer_resource_info(tx: Transaction) -> Tuple[Optional[str], Optional[str]]:
    """Infers resource type (e.g. project, document) and resource ID from transaction path."""
    parts = [p for p in tx.path.split("/") if p]
    if not parts:
        return None, None

    # Common pattern: /resources/{id} or /resources
    resource_type = None
    resource_id = None

    for idx, part in enumerate(parts):
        if part.isdigit() or len(part) > 20 or "-" in part:
            resource_id = part
            if idx > 0:
                resource_type = parts[idx - 1].rstrip("s") # singularize simple plural
            break

    if not resource_type and parts:
        resource_type = parts[0].rstrip("s")

    return resource_type, resource_id


def generate_workflow_state_graph(db: DBSession, session_id: str) -> Workflow:
    """
    Generates a Workflow State Graph (WSG) for a session using NetworkX and persists to DB.
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

    # Fetch existing dependencies for this session
    tx_ids = [t.id for t in transactions]
    dependencies = (
        db.query(Dependency)
        .filter(Dependency.producer_transaction_id.in_(tx_ids))
        .all()
    )
    dep_map = {(d.producer_transaction_id, d.consumer_transaction_id): d for d in dependencies}

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

    # Build NetworkX DiGraph
    G = nx.DiGraph()

    created_nodes: List[WorkflowNode] = []
    tx_to_node_map: Dict[str, WorkflowNode] = {}

    for idx, tx in enumerate(transactions):
        res_type, res_id = infer_resource_info(tx)
        path_template = tx.path # Default to actual path if operation mapping not available

        node_obj = WorkflowNode(
            id=str(uuid.uuid4()),
            workflow_id=workflow_obj.id,
            sequence_index=idx,
            transaction_id=tx.id,
            operation_id=tx.operation_id or f"{tx.method.lower()}_{tx.path}",
            method=tx.method,
            path_template=path_template,
            actual_path=tx.path,
            resource_type=res_type,
            resource_identifier=res_id
        )
        db.add(node_obj)
        created_nodes.append(node_obj)
        tx_to_node_map[tx.id] = node_obj

        G.add_node(
            node_obj.id,
            sequence=idx,
            method=tx.method,
            path=tx.path,
            operation=node_obj.operation_id
        )

    db.flush()

    # Track created edges to prevent duplicate identical edges
    created_edges: List[WorkflowEdge] = []
    edge_pairs: Dict[Tuple[str, str], WorkflowEdge] = {}

    # 1. Add Sequential Transition Edges between consecutive steps
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
        edge_pairs[(src_node.id, tgt_node.id)] = edge_obj
        G.add_edge(src_node.id, tgt_node.id, dependency_id=dep.id if dep else None)

    # 2. Add Dependency Transition Edges for ALL data dependencies (including non-consecutive)
    for dep in dependencies:
        src_node = tx_to_node_map.get(dep.producer_transaction_id)
        tgt_node = tx_to_node_map.get(dep.consumer_transaction_id)

        if src_node and tgt_node and src_node.id != tgt_node.id:
            pair = (src_node.id, tgt_node.id)
            if pair in edge_pairs:
                # Upgrade existing sequential edge to DEPENDENCY_TRANSITION
                existing_edge = edge_pairs[pair]
                existing_edge.transition_type = "DEPENDENCY_TRANSITION"
                existing_edge.dependency_id = dep.id
            else:
                # Add new non-consecutive dependency edge (multi-degree branch)
                edge_obj = WorkflowEdge(
                    id=str(uuid.uuid4()),
                    workflow_id=workflow_obj.id,
                    source_node_id=src_node.id,
                    target_node_id=tgt_node.id,
                    transition_type="DEPENDENCY_TRANSITION",
                    dependency_id=dep.id
                )
                db.add(edge_obj)
                created_edges.append(edge_obj)
                edge_pairs[pair] = edge_obj
                G.add_edge(src_node.id, tgt_node.id, dependency_id=dep.id)

    workflow_obj.edge_count = len(created_edges)
    db.commit()

    logger.info(f"Generated Multi-Degree WSG Workflow {workflow_obj.id}: {workflow_obj.node_count} nodes, {workflow_obj.edge_count} edges.")
    return workflow_obj

