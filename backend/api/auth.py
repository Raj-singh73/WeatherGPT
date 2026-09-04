"""
auth.py - Authentication & Profile API Router for WeatherGPT
Endpoints for user registration, login, profile management, session tracking, and database telemetry.
"""

from fastapi import APIRouter, HTTPException, Header, Depends, status
from typing import Optional, Dict, Any

from models.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserProfileResponse,
    ProfileUpdateRequest,
    AuthTokenResponse,
    AdminRecordsResponse
)
from services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication & Profiles"])


def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Dependency to validate Bearer token and retrieve active user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token. Please sign in."
        )
    token = authorization.replace("Bearer ", "").strip()
    user = auth_service.get_user_by_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or token is invalid. Please log in again."
        )
    user["_current_token"] = token
    return user


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest):
    """
    Registers a new user account, stores profile attributes, records registration timestamp,
    and returns an authenticated session token.
    """
    try:
        user_row, token = auth_service.register_user(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            role=payload.role or "Farmer",
            phone=payload.phone,
            state=payload.state or "Uttar Pradesh",
            district=payload.district or "Lucknow",
            village=payload.village,
            primary_crop=payload.primary_crop or "Wheat",
            preferred_language=payload.preferred_language or "en"
        )
        return AuthTokenResponse(
            token=token,
            token_type="Bearer",
            user=UserProfileResponse(**user_row),
            message="Account created successfully and recorded into database."
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration failed: {e}")


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: UserLoginRequest):
    """
    Authenticates user credentials, updates last_login_at timestamp, logs login event,
    and issues a new session token.
    """
    try:
        user_row, token = auth_service.authenticate_user(
            email=payload.email,
            password=payload.password
        )
        return AuthTokenResponse(
            token=token,
            token_type="Bearer",
            user=UserProfileResponse(**user_row),
            message="Login successful."
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Login error: {e}")


@router.get("/me", response_model=UserProfileResponse)
def get_me(user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieves current user's profile and saved preferences."""
    return UserProfileResponse(**user)


@router.put("/profile", response_model=UserProfileResponse)
def update_user_profile(
    payload: ProfileUpdateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Updates user's profile information (location, crop, role, language),
    records updated_at timestamp, and logs activity to SQLite.
    """
    updates = payload.model_dump(exclude_unset=True)
    try:
        updated_row = auth_service.update_profile(user["id"], updates)
        return UserProfileResponse(**updated_row)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update profile: {e}")


@router.post("/logout")
def logout(user: Dict[str, Any] = Depends(get_current_user)):
    """Revokes current session token and logs logout event."""
    token = user.get("_current_token")
    if token:
        auth_service.logout_user(token)
    return {"status": "success", "message": "Successfully logged out."}


@router.get("/admin/records", response_model=AdminRecordsResponse)
def get_admin_records():
    """
    Admin & telemetry endpoint: Inspects all registered user records with exact
    creation timestamps, last login timestamps, and system activity logs in the database.
    """
    users = auth_service.get_all_users_for_admin()
    logs = auth_service.get_activity_logs(limit=50)
    return AdminRecordsResponse(
        total_users=len(users),
        users=users,
        recent_logs=logs
    )
