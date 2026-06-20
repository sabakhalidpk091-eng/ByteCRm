from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

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
