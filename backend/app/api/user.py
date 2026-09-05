from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import parse_supabase_jwt, get_current_user
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserCreateResponse,
)

router = APIRouter()


@router.post("/create", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: Optional[UserCreate] = None,
    token_payload: Dict[str, Any] = Depends(parse_supabase_jwt),
    db: Session = Depends(get_db),
):
    """
    Creates a new user record in the local database synced from the verified Supabase JWT payload.
    """
    supabase_uid = token_payload["sub"]
    existing_user = db.query(User).filter(User.supabase_uid == supabase_uid).first()
    if existing_user:
        return UserCreateResponse(
            message="User already exists",
            user_id=existing_user.user_id,
            supabase_uid=existing_user.supabase_uid,
            email=existing_user.email,
            name=existing_user.name,
            preferred_language=existing_user.preferred_language,
            home_port=existing_user.home_port,
            vessel_id=existing_user.vessel_id,
        )

    # Extract email from token payload or user metadata
    email = token_payload.get("email")
    if not email and "user_metadata" in token_payload:
        email = token_payload["user_metadata"].get("email")
    if not email:
        email = ""

    new_user = User(
        supabase_uid=supabase_uid,
        email=email,
        name=user_in.name if user_in else None,
        preferred_language=(user_in.preferred_language if user_in and user_in.preferred_language else "en"),
        home_port=user_in.home_port if user_in else None,
        vessel_id=user_in.vessel_id if user_in else None,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserCreateResponse(
        message="User created successfully",
        user_id=new_user.user_id,
        supabase_uid=new_user.supabase_uid,
        email=new_user.email,
        name=new_user.name,
        preferred_language=new_user.preferred_language,
        home_port=new_user.home_port,
        vessel_id=new_user.vessel_id,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Retrieves the currently authenticated user's profile details.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates the authenticated user's profile information.
    """
    if user_update.name is not None:
        current_user.name = user_update.name
    if user_update.preferred_language is not None:
        current_user.preferred_language = user_update.preferred_language
    if user_update.home_port is not None:
        current_user.home_port = user_update.home_port
    if user_update.vessel_id is not None:
        current_user.vessel_id = user_update.vessel_id

    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/token-info")
def get_token_info(token_payload: Dict[str, Any] = Depends(parse_supabase_jwt)):
    """
    Returns the parsed claims from the caller's verified Supabase JWT token.
    """
    return {
        "status": "valid",
        "claims": token_payload,
    }
