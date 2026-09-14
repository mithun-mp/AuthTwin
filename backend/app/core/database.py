from typing import Optional, Any
from urllib.parse import urlparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    poolclass=NullPool if "sqlite" in settings.DATABASE_URL else None
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_active_target_model(db) -> Optional[Any]:
    """
    SINGLE SOURCE OF TRUTH: Obtains the active Target model from the database.
    Filters out stale control plane targets. Returns None if no active valid target exists.
    """
    from app.models.models import Target
    targets = db.query(Target).order_by(Target.created_at.desc()).all()
    if not targets:
        return None

    control_endpoints = settings.get_control_plane_endpoints()
    for target in targets:
        if not target.base_url:
            continue
        try:
            parsed = urlparse(target.base_url.strip())
            hostname = (parsed.hostname or "").lower()
            port = parsed.port or (80 if parsed.scheme == "http" else 443)
            # If target base_url matches control plane endpoint, delete stale target
            if (hostname, port) in control_endpoints:
                db.delete(target)
                db.commit()
                continue
            return target
        except Exception:
            continue

    return None


def seed_demo_data(db=None):
    """
    EXPLICIT DEMO SEED: Seeds demonstration target and identities ONLY when explicitly invoked or when AUTHTWIN_DEMO_MODE=true.
    Standard application startup NEVER runs this automatically.
    """
    from app.models.models import Target, Identity
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True
    try:
        active_target = get_active_target_model(db)
        if not active_target:
            active_target = Target(
                id="target-default",
                name="Demo Reference Target",
                base_url="http://127.0.0.1:8001"
            )
            db.add(active_target)
            db.commit()
            db.refresh(active_target)

        alice = db.query(Identity).filter(Identity.role == "Primary").first()
        if not alice:
            alice = Identity(
                id="identity-alice",
                target_id=active_target.id,
                name="Alice (Primary User)",
                role="Primary",
                auth_type="Bearer"
            )
            db.add(alice)

        bob = db.query(Identity).filter(Identity.role == "Alternate").first()
        if not bob:
            bob = Identity(
                id="identity-bob",
                target_id=active_target.id,
                name="Bob (Alternate User)",
                role="Alternate",
                auth_type="Bearer"
            )
            db.add(bob)

        db.commit()
    except Exception:
        db.rollback()
    finally:
        if should_close:
            db.close()


def init_db():
    """Initializes database schema and conditionally seeds demo data if AUTHTWIN_DEMO_MODE is active."""
    import app.models.models
    app.models.models.Target.__table__.metadata.create_all(bind=engine)
    if settings.AUTHTWIN_DEMO_MODE:
        seed_demo_data()
