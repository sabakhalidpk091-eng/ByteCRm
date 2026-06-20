from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class CampaignBase(BaseModel):
    name: str
    type: str = "email"
    status: str = "draft"
    audience: Dict[str, Any] = Field(default_factory=dict)
    subject: Optional[str] = None
    body: Optional[str] = None
    sender_email: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    stats: Dict[str, int] = Field(default_factory=lambda: {"sent": 0, "opened": 0, "clicked": 0, "bounced": 0})

class CampaignCreate(CampaignBase):
    created_by: UUID

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    audience: Optional[Dict[str, Any]] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    sender_email: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    stats: Optional[Dict[str, int]] = None


class Campaign(CampaignBase):
    id: UUID
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Campaign Member Schemas
class CampaignMemberBase(BaseModel):
    campaign_id: UUID
    contact_id: UUID
    current_step: int = 0
    status: str = "active"
    last_sent_at: Optional[datetime] = None
    next_delivery_at: datetime

class CampaignMemberCreate(CampaignMemberBase):
    pass

class CampaignMemberUpdate(BaseModel):
    current_step: Optional[int] = None
    status: Optional[str] = None
    last_sent_at: Optional[datetime] = None
    next_delivery_at: Optional[datetime] = None

class CampaignMember(CampaignMemberBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Drip Step Schemas
class DripStepBase(BaseModel):
    campaign_id: UUID
    order: int
    delay_days: int = 0
    subject: str
    body: str
    sent_count: int = 0

class DripStepCreate(DripStepBase):
    pass

class DripStepUpdate(BaseModel):
    order: Optional[int] = None
    delay_days: Optional[int] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    sent_count: Optional[int] = None

class DripStep(DripStepBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
