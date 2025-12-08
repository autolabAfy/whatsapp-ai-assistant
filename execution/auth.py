"""
JWT Authentication for Mobile App API
Secures endpoints with token-based authentication
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from loguru import logger

from execution.config import settings
from execution.database import get_db


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token bearer
security = HTTPBearer()


class TokenData(BaseModel):
    """JWT token payload"""
    agent_id: str
    email: str
    exp: datetime


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(agent_id: str, email: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token

    Args:
        agent_id: Agent's UUID
        email: Agent's email
        expires_delta: Token expiration time

    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)

    to_encode = {
        "agent_id": agent_id,
        "email": email,
        "exp": expire
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verify JWT token and extract payload

    Args:
        token: JWT token string

    Returns:
        TokenData with agent_id and email

    Raises:
        HTTPException if token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        agent_id: str = payload.get("agent_id")
        email: str = payload.get("email")

        if agent_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        return TokenData(
            agent_id=agent_id,
            email=email,
            exp=datetime.fromtimestamp(payload.get("exp"))
        )

    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    FastAPI dependency to get current authenticated agent

    Usage:
        @app.get("/protected")
        async def protected_route(agent = Depends(get_current_agent)):
            return {"agent_id": agent['agent_id']}
    """
    token = credentials.credentials
    token_data = verify_token(token)

    # Verify agent exists in database
    db = get_db()
    agent = db.execute_one(
        "SELECT * FROM agents WHERE agent_id = %s AND is_active = TRUE",
        (token_data.agent_id,)
    )

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent not found or inactive"
        )

    return agent


def authenticate_agent(email: str, password: str) -> Optional[dict]:
    """
    Authenticate agent with email and password

    Args:
        email: Agent's email
        password: Plain text password

    Returns:
        Agent dict if authenticated, None otherwise
    """
    db = get_db()

    agent = db.execute_one(
        "SELECT * FROM agents WHERE email = %s AND is_active = TRUE",
        (email,)
    )

    if not agent:
        return None

    # Check password
    if not verify_password(password, agent.get('password_hash', '')):
        return None

    return agent


def register_agent(
    email: str,
    password: str,
    full_name: str,
    phone_number: Optional[str] = None
) -> dict:
    """
    Register new agent

    Args:
        email: Agent's email
        password: Plain text password (will be hashed)
        full_name: Agent's full name
        phone_number: Optional phone number

    Returns:
        Created agent dict
    """
    db = get_db()

    # Check if email already exists
    existing = db.execute_one(
        "SELECT agent_id FROM agents WHERE email = %s",
        (email,)
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    password_hash = hash_password(password)

    # Create agent
    agent_id = db.insert("agents", {
        "email": email,
        "password_hash": password_hash,
        "full_name": full_name,
        "phone_number": phone_number,
        "is_active": True,
        "assistant_name": "Alex",  # Default
        "speaking_style": "professional"
    })

    # Return agent
    return db.execute_one(
        "SELECT agent_id, email, full_name FROM agents WHERE agent_id = %s",
        (agent_id,)
    )


# Optional: Dependency for checking specific permissions
def require_agent_access(conversation_id: str):
    """
    Check if current agent has access to conversation

    Usage:
        @app.get("/conversations/{conversation_id}")
        async def get_conv(
            conversation_id: str,
            agent = Depends(get_current_agent),
            _ = Depends(lambda: require_agent_access(conversation_id))
        ):
            ...
    """
    async def _check_access(agent = Depends(get_current_agent)):
        db = get_db()
        conv = db.execute_one(
            "SELECT agent_id FROM conversations WHERE conversation_id = %s",
            (conversation_id,)
        )

        if not conv or conv['agent_id'] != agent['agent_id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation"
            )

    return _check_access


# Migration to add password_hash column to agents
ALTER_TABLE_SQL = """
ALTER TABLE agents ADD COLUMN IF NOT EXISTS password_hash TEXT;
"""


if __name__ == "__main__":
    # Test password hashing
    password = "test123"
    hashed = hash_password(password)
    print(f"Password: {password}")
    print(f"Hashed: {hashed}")
    print(f"Verified: {verify_password(password, hashed)}")

    # Test token creation
    token = create_access_token("test-agent-id", "test@example.com")
    print(f"\nToken: {token[:50]}...")

    # Test token verification
    try:
        data = verify_token(token)
        print(f"Verified: {data}")
    except Exception as e:
        print(f"Error: {e}")
