from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class TicketBase(BaseModel):
    subject: str
    description: str
    status: str = "open"
    priority: str = "medium"
    contact_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    sla: Dict[str, Any] = Field(default_factory=lambda: {"breached": False, "responseDeadline": None, "resolutionDeadline": None})
    replies: List[Dict[str, Any]] = []
    tags: List[str] = []

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    contact_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    sla: Optional[Dict[str, Any]] = None
    replies: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None

class Ticket(TicketBase):
    id: UUID
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
