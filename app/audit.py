import json
import logging
from sqlalchemy.orm import Session
from app import models

logger = logging.getLogger(__name__)


def log_audit(
    db: Session,
    actor_user_id: int,
    action: str,
    entity: str,
    entity_id: int,
    details: dict | None = None,
) -> None:
    """Insert a row into audit_events for every state-changing action."""
    event = models.AuditEvent(
        actor_user_id=actor_user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        details=json.dumps(details or {}),
    )
    db.add(event)
    db.commit()
    logger.info("audit: %s %s#%s by user %s", action, entity, entity_id, actor_user_id)
