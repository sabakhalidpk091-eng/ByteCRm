from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class LeadBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    source: str = "other"
    status: str = "new"
    score: int = 0
    assigned_to: Optional[UUID] = None
    notes: Optional[str] = None

class LeadCreate(LeadBase):
    created_by: Optional[UUID] = None

class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    score: Optional[int] = None
    assigned_to: Optional[UUID] = None
    notes: Optional[str] = None
    converted_at: Optional[datetime] = None
    converted_contact_id: Optional[UUID] = None
    converted_opportunity_id: Optional[UUID] = None

class Lead(LeadBase):
    id: UUID
    converted_at: Optional[datetime] = None
    converted_contact_id: Optional[UUID] = None
    converted_opportunity_id: Optional[UUID] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
