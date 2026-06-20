from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class ActivityBase(BaseModel):
    type: str
    subject: str
    description: Optional[str] = None
    duration: Optional[int] = None
    date: datetime = Field(default_factory=datetime.now)
    contact_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None

class ActivityCreate(ActivityBase):
    created_by: UUID

class ActivityUpdate(BaseModel):
    type: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    date: Optional[datetime] = None
    contact_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None

class Activity(ActivityBase):
    id: UUID
    created_by: UUID
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
