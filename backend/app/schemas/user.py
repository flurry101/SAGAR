import uuid
from datetime import datetime
from typing import Optional, Any, Dict, Union
from pydantic import BaseModel, ConfigDict, EmailStr

## attr: m1
class UserCreate(BaseModel):
    name: Optional[str] = None
    preferred_language: Optional[str] = "en"
    home_port: Optional[str] = None
    vessel_id: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    preferred_language: Optional[str] = None
    home_port: Optional[str] = None
    vessel_id: Optional[str] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: Union[str, uuid.UUID]
    supabase_uid: str
    email: str
    name: Optional[str] = None
    preferred_language: str = "en"
    home_port: Optional[str] = None
    vessel_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class UserCreateResponse(BaseModel):
    message: str
    user_id: Union[str, uuid.UUID]
    supabase_uid: str
    email: str
    name: Optional[str] = None
    preferred_language: str = "en"
    home_port: Optional[str] = None
    vessel_id: Optional[str] = None

class TokenPayload(BaseModel):
    sub: str
    email: Optional[str] = None
    aud: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None
    app_metadata: Optional[Dict[str, Any]] = None
    user_metadata: Optional[Dict[str, Any]] = None
## attr: m1