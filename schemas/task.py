from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = "medium"
    status: str = "pending"
    assigned_to: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None

class TaskCreate(TaskBase):
    created_by: UUID

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    completed_at: Optional[datetime] = None

class Task(TaskBase):
    id: UUID
    completed_at: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
