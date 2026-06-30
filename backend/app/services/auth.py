import re
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import User, Workspace, WorkspaceMembership
from app.models.enums import WorkspaceRole

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
settings = get_settings()
DEMO_PASSWORD = "grounded-demo"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise ValueError("Invalid token") from exc

    if payload.get("type") != "access":
        raise ValueError("Invalid token type")

    subject = payload.get("sub")
    if not subject:
        raise ValueError("Token subject missing")

    try:
        return uuid.UUID(subject)
    except ValueError as exc:
        raise ValueError("Invalid token subject") from exc


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return normalized.strip("-") or "workspace"


def unique_workspace_slug(db: Session, base_value: str) -> str:
    base_slug = slugify(base_value)
    candidate = base_slug
    counter = 1

    while db.scalar(select(Workspace).where(Workspace.slug == candidate)) is not None:
        counter += 1
        candidate = f"{base_slug}-{counter}"

    return candidate


def create_user_with_workspace(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
) -> User:
    normalized_email = email.strip().lower()
    if db.scalar(select(User).where(User.email == normalized_email)) is not None:
        raise ValueError("Email already registered")

    user = User(
        name=name.strip(),
        email=normalized_email,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.flush()

    workspace_name = f"{name.strip().split()[0]}'s Workspace"
    workspace = Workspace(
        name=workspace_name,
        slug=unique_workspace_slug(db, f"{normalized_email}-workspace"),
        created_by_user_id=user.id,
    )
    db.add(workspace)
    db.flush()

    db.add(
        WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=user.id,
            role=WorkspaceRole.OWNER,
        )
    )
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, *, email: str, password: str) -> User | None:
    normalized_email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == normalized_email))
    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user
