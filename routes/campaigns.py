from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from config.database import supabase
from utils.auth import get_current_user
from schemas.campaign import CampaignCreate, CampaignUpdate, Campaign
from schemas.campaign_logic import DripStepCreate, DripStepUpdate, DripStep
from datetime import datetime

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

@router.get("/")
async def get_campaigns(
    page: int = 1,
    limit: int = 20,
    status: str = "",
    type: str = "",
    user: dict = Depends(get_current_user)
):
    query = supabase.table("campaigns").select("*").eq("is_deleted", False).eq("created_by", user["id"])
    
    if status:
        query = query.eq("status", status)
    if type:
        query = query.eq("type", type)

    start = (page - 1) * limit
    end = start + limit - 1
    
    count_res = supabase.table("campaigns").select("id", count="exact").eq("is_deleted", False).eq("created_by", user["id"]).execute()
    total = count_res.count if hasattr(count_res, 'count') else len(count_res.data)

    res = query.order("created_at", desc=True).range(start, end).execute()
    
    return {
        "success": True,
        "data": {
            "campaigns": res.data,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "limit": limit
        },
        "message": "Campaigns retrieved successfully"
    }

@router.get("/{id}")
async def get_campaign_by_id(id: str, user: dict = Depends(get_current_user)):
    campaign_res = supabase.table("campaigns").select("*").eq("id", id).eq("is_deleted", False).eq("created_by", user["id"]).execute()
    if not campaign_res.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    steps_res = supabase.table("drip_steps").select("*").eq("campaign_id", id).order("order").execute()
    
    return {
        "success": True, 
        "data": {
            "campaign": campaign_res.data[0],
            "steps": steps_res.data
        }, 
        "message": "Campaign retrieved successfully"
    }

@router.post("/", status_code=201)
async def create_campaign(payload: CampaignCreate, user: dict = Depends(get_current_user)):
    data = payload.dict()
    data["created_by"] = user["id"]
    res = supabase.table("campaigns").insert(data).execute()
    return {"success": True, "data": res.data[0], "message": "Campaign created successfully"}

@router.put("/{id}")
async def update_campaign(id: str, payload: CampaignUpdate, user: dict = Depends(get_current_user)):
    exists = supabase.table("campaigns").select("id").eq("id", id).eq("is_deleted", False).eq("created_by", user["id"]).execute()
    if not exists.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    res = supabase.table("campaigns").update(payload.dict(exclude_unset=True)).eq("id", id).execute()
    return {"success": True, "data": res.data[0], "message": "Campaign updated successfully"}

@router.delete("/{id}")
async def delete_campaign(id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("campaigns").update({"is_deleted": True, "deleted_at": datetime.utcnow().isoformat()}).eq("id", id).eq("created_by", user["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"success": True, "message": "Campaign soft deleted successfully"}

@router.post("/{id}/steps", status_code=201)
async def add_drip_step(id: str, payload: DripStepCreate, user: dict = Depends(get_current_user)):
    # Verify campaign ownership
    camp = supabase.table("campaigns").select("id").eq("id", id).eq("is_deleted", False).eq("created_by", user["id"]).execute()
    if not camp.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Check duplicate order
    exists = supabase.table("drip_steps").select("id").eq("campaign_id", id).eq("order", payload.order).execute()
    if exists.data:
        raise HTTPException(status_code=400, detail=f"A step with order {payload.order} already exists")
    
    data = payload.dict()
    data["campaign_id"] = id
    res = supabase.table("drip_steps").insert(data).execute()
    return {"success": True, "data": res.data[0], "message": "Drip step added successfully"}

@router.post("/{id}/start")
async def start_campaign(id: str, user: dict = Depends(get_current_user)):
    campaign_res = supabase.table("campaigns").select("*").eq("id", id).eq("is_deleted", False).eq("created_by", user["id"]).execute()
    if not campaign_res.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_res.data[0]
    if campaign["status"] in ["active", "completed"]:
        raise HTTPException(status_code=400, detail=f"Campaign is already {campaign['status']}")

    # Simple logic: Enroll all active contacts if no audience filters, or mock direct blast
    steps_res = supabase.table("drip_steps").select("*").eq("campaign_id", id).execute()
    
    if not steps_res.data:
        # Direct blast logic (simplified)
        supabase.table("campaigns").update({
            "status": "completed",
            "sent_at": datetime.utcnow().isoformat()
        }).eq("id", id).execute()
        return {"success": True, "message": "Campaign direct blast completed (mocked)"}
    else:
        # Drip enrollment logic
        # For now, just mark active
        supabase.table("campaigns").update({
            "status": "active",
            "sent_at": datetime.utcnow().isoformat()
        }).eq("id", id).execute()
        return {"success": True, "message": "Campaign drip sequence initiated"}
