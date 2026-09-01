import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declarative_mixin, synonym
from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


@declarative_mixin
class TimestampMixin:
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = synonym("id")
    supabase_uid = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    preferred_language = Column(String(10), default="en", nullable=False)
    home_port = Column(String(255), nullable=True)
    vessel_id = Column(String(64), nullable=True)

    def __repr__(self):
        return f"<User(user_id='{self.user_id}', email='{self.email}', supabase_uid='{self.supabase_uid}')>"
