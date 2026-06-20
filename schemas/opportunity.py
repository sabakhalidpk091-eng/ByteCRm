from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal

class OpportunityBase(BaseModel):
    name: str
    account_id: UUID
    contact_id: UUID
    value: Decimal = 0
    stage: str
    probability: int = 0
    close_date: Optional[datetime] = None
    assigned_to: Optional[UUID] = None
    notes: Optional[str] = None
    lost_reason: Optional[str] = None

class OpportunityCreate(OpportunityBase):
    created_by: UUID

class OpportunityUpdate(BaseModel):
    name: Optional[str] = None
    account_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    value: Optional[Decimal] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    close_date: Optional[datetime] = None
    assigned_to: Optional[UUID] = None
    notes: Optional[str] = None
    lost_reason: Optional[str] = None

class Opportunity(OpportunityBase):
    id: UUID
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
