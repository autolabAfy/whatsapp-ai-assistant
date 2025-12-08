"""
Authentication Endpoints for Mobile App
Login, register, token refresh
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from loguru import logger

from execution.auth import (
    authenticate_agent,
    register_agent,
    create_access_token,
    get_current_agent,
    hash_password
)
from execution.push_notifications import register_device_token, unregister_device_token


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# Request/Response Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_token: Optional[str] = None  # For push notifications
    platform: Optional[str] = "ios"  # "ios" or "android"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone_number: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    agent_id: str
    email: str
    full_name: str


class DeviceTokenRequest(BaseModel):
    device_token: str
    platform: str = "ios"


# Endpoints
@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login with email and password

    Returns JWT access token for API authentication
    """
    try:
        # Authenticate
        agent = authenticate_agent(request.email, request.password)

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        # Create access token
        access_token = create_access_token(
            agent_id=agent['agent_id'],
            email=agent['email']
        )

        # Register device token for push notifications
        if request.device_token:
            register_device_token(
                agent_id=agent['agent_id'],
                device_token=request.device_token,
                platform=request.platform
            )

        return TokenResponse(
            access_token=access_token,
            agent_id=agent['agent_id'],
            email=agent['email'],
            full_name=agent['full_name']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """
    Register new agent account

    Creates agent and returns access token
    """
    try:
        # Register agent
        agent = register_agent(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            phone_number=request.phone_number
        )

        # Create access token
        access_token = create_access_token(
            agent_id=agent['agent_id'],
            email=agent['email']
        )

        return TokenResponse(
            access_token=access_token,
            agent_id=agent['agent_id'],
            email=agent['email'],
            full_name=agent['full_name']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/device-token")
async def register_device(
    request: DeviceTokenRequest,
    agent = Depends(get_current_agent)
):
    """
    Register device token for push notifications

    Requires authentication
    """
    try:
        register_device_token(
            agent_id=agent['agent_id'],
            device_token=request.device_token,
            platform=request.platform
        )

        return {"status": "registered", "device_token": request.device_token}

    except Exception as e:
        logger.error(f"Device token registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register device token"
        )


@router.delete("/device-token")
async def unregister_device(
    device_token: str,
    agent = Depends(get_current_agent)
):
    """
    Unregister device token (on logout)

    Requires authentication
    """
    try:
        unregister_device_token(device_token)

        return {"status": "unregistered"}

    except Exception as e:
        logger.error(f"Device token unregistration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unregister device token"
        )


@router.get("/me")
async def get_current_user(agent = Depends(get_current_agent)):
    """
    Get current authenticated agent info

    Requires authentication
    """
    return {
        "agent_id": agent['agent_id'],
        "email": agent['email'],
        "full_name": agent['full_name'],
        "phone_number": agent.get('phone_number'),
        "assistant_name": agent.get('assistant_name'),
        "speaking_style": agent.get('speaking_style')
    }


@router.post("/logout")
async def logout(
    device_token: Optional[str] = None,
    agent = Depends(get_current_agent)
):
    """
    Logout - unregister device token

    Requires authentication
    """
    if device_token:
        unregister_device_token(device_token)

    return {"status": "logged_out"}
