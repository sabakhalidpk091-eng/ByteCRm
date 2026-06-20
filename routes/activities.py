from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from config.database import supabase
from utils.auth import get_current_user
from schemas.activity import ActivityCreate, ActivityUpdate, Activity
from datetime import datetime

from utils.websocket import manager

router = APIRouter(prefix="/activities", tags=["Activities"])

@router.post("/", status_code=201)
async def create_activity(payload: ActivityCreate, user: dict = Depends(get_current_user)):
    data = payload.dict()
    data["created_by"] = user["id"]
    res = supabase.table("activities").insert(data).execute()
    
    # Broadcast to all users
    await manager.broadcast({"type": "activity:created", "data": res.data[0]})
    
    return {"success": True, "data": res.data[0], "message": "Activity logged successfully"}

@router.get("/")
async def get_activities(
    page: int = 1,
    limit: int = 10,
    type: str = "",
    contact_id: Optional[str] = None,
    account_id: Optional[str] = None,
    opportunity_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = supabase.table("activities").select("*, contact_id(*), account_id(*), opportunity_id(*), created_by(*)").eq("is_deleted", False).eq("created_by", user["id"])
    
    if type:
        query = query.eq("type", type)
    if contact_id:
        query = query.eq("contact_id", contact_id)
    if account_id:
        query = query.eq("account_id", account_id)
    if opportunity_id:
        query = query.eq("opportunity_id", opportunity_id)

    start = (page - 1) * limit
    end = start + limit - 1
    
    count_res = supabase.table("activities").select("id", count="exact").eq("is_deleted", False).eq("created_by", user["id"]).execute()
    total = count_res.count if hasattr(count_res, 'count') else len(count_res.data)

    res = query.order("date", desc=True).range(start, end).execute()
    
    return {
        "success": True,
        "data": {
            "activities": res.data,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "limit": limit
        },
        "message": "Activities fetched successfully"
    }

@router.get("/{id}")
async def get_activity_by_id(id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("activities").select("*, contact_id(*), account_id(*), opportunity_id(*), created_by(*)").eq("id", id).eq("is_deleted", False).eq("created_by", user["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Activity not found")
    return {"success": True, "data": res.data[0], "message": "Activity details fetched successfully"}

@router.put("/{id}")
async def update_activity(id: str, payload: ActivityUpdate, user: dict = Depends(get_current_user)):
    exists = supabase.table("activities").select("id").eq("id", id).eq("is_deleted", False).eq("created_by", user["id"]).execute()
    if not exists.data:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    update_data = payload.dict(exclude_unset=True)
    res = supabase.table("activities").update(update_data).eq("id", id).execute()
    return {"success": True, "data": res.data[0], "message": "Activity updated successfully"}

@router.delete("/{id}")
async def delete_activity(id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("activities").update({"is_deleted": True, "deleted_at": datetime.utcnow().isoformat()}).eq("id", id).eq("created_by", user["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Activity not found")
    return {"success": True, "message": "Activity deleted successfully"}
