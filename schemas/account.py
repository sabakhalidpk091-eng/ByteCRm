from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class AccountBase(BaseModel):
    name: str
    industry: Optional[str] = None
    domain: Optional[str] = None
    owner: Optional[str] = None
    status: str = "active"
    website: Optional[str] = None
    size: Optional[str] = None
    phone: Optional[str] = None
    address: Dict[str, Any] = Field(default_factory=dict)
    primary_contact_id: Optional[UUID] = None

class AccountCreate(AccountBase):
    created_by: UUID

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    domain: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    website: Optional[str] = None
    size: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    primary_contact_id: Optional[UUID] = None

class Account(AccountBase):
    id: UUID
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
