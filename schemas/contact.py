from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    account_id: Optional[UUID] = None
    status: str = "active"
    tags: List[str] = []
    notes: Optional[str] = None

class ContactCreate(ContactBase):
    created_by: UUID

class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    account_id: Optional[UUID] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None

class Contact(ContactBase):
    id: UUID
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
