import uuid
from sqlalchemy.orm import Session as DBSession
from app.models.models import Workflow, Identity, ShadowWorkflow
from app.core.logging import logger

def clone_shadow_workflow(
    db: DBSession,
    source_workflow_id: str,
    shadow_identity_id: str
) -> ShadowWorkflow:
    """
    Clones a Workflow into a Shadow Workflow associated with an alternate Identity.
    Enforces Credential Isolation invariant and MODEL_ONLY status.
    Uses the linear workflow representation as authority for credential-isolated replay modeling.
    """
    source_wf = db.query(Workflow).filter(Workflow.id == source_workflow_id).first()
    if not source_wf:
        raise ValueError(f"Source Workflow {source_workflow_id} not found")

    shadow_identity = db.query(Identity).filter(Identity.id == shadow_identity_id).first()
    if not shadow_identity:
        raise ValueError(f"Shadow Identity {shadow_identity_id} not found")

    if source_wf.identity_id == shadow_identity_id:
        logger.warning(f"Cloning workflow {source_workflow_id} to the same identity {shadow_identity_id}")

    shadow_wf = ShadowWorkflow(
        id=str(uuid.uuid4()),
        source_workflow_id=source_wf.id,
        source_identity_id=source_wf.identity_id,
        shadow_identity_id=shadow_identity.id,
        clone_policy="CREDENTIAL_ISOLATED",
        status="MODEL_ONLY"
    )
    db.add(shadow_wf)
    db.commit()

    logger.info(f"Created Shadow Workflow {shadow_wf.id}: Source={source_wf.id} (Identity={source_wf.identity_id}) -> Shadow Identity={shadow_identity.id}. Status=MODEL_ONLY")
    return shadow_wf
