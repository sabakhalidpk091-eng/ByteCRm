from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from config.database import supabase
from utils.auth import get_current_user
from schemas.opportunity import OpportunityCreate, OpportunityUpdate, Opportunity
from datetime import datetime

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])

@router.post("/", status_code=201)
async def create_opportunity(payload: OpportunityCreate, user: dict = Depends(get_current_user)):
    data = payload.dict()
    data["created_by"] = user["id"]
    res = supabase.table("opportunities").insert(data).execute()
    return {"success": True, "data": res.data[0], "message": "Opportunity created successfully"}

@router.get("/")
async def get_opportunities(
    page: int = 1,
    limit: int = 10,
    search: str = "",
    stage: str = "",
    account_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = supabase.table("opportunities").select("*, account_id(*), contact_id(*), assigned_to(*)").eq("is_deleted", False).eq("created_by", user["id"])
    
    if search:
        query = query.ilike("name", f"%{search}%")
    if stage:
        query = query.eq("stage", stage)
    if account_id:
        query = query.eq("account_id", account_id)

    start = (page - 1) * limit
    end = start + limit - 1
    
    count_res = supabase.table("opportunities").select("id", count="exact").eq("is_deleted", False).eq("created_by", user["id"]).execute()
    total = count_res.count if hasattr(count_res, 'count') else len(count_res.data)

    res = query.order("created_at", desc=True).range(start, end).execute()
    
    return {
        "success": True,
        "data": {
            "opportunities": res.data,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "limit": limit
        },
        "message": "Opportunities fetched successfully"
    }

@router.get("/pipeline")
async def get_pipeline(user: dict = Depends(get_current_user)):
    res = supabase.table("opportunities").select("*, account_id(*), contact_id(*), assigned_to(*)").eq("is_deleted", False).eq("created_by", user["id"]).execute()
    
    pipeline_stages = ['prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost']
    opportunities = res.data
    
    stage_columns = []
    for stage in pipeline_stages:
        deals = [o for o in opportunities if o["stage"] == stage]
        total_value = sum(float(o.get("value", 0)) for o in deals)
        stage_columns.append({
            "stage": stage,
            "deals": deals,
            "totalValue": total_value,
            "count": len(deals)
        })
        
    return {"success": True, "data": stage_columns, "message": "Pipeline stages fetched successfully"}

@router.get("/{id}")
async def get_opportunity_by_id(id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("opportunities").select("*, account_id(*), contact_id(*), assigned_to(*)").eq("id", id).eq("is_deleted", False).eq("created_by", user["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return {"success": True, "data": res.data[0], "message": "Opportunity details fetched successfully"}

@router.put("/{id}")
async def update_opportunity(id: str, payload: OpportunityUpdate, user: dict = Depends(get_current_user)):
    exists = supabase.table("opportunities").select("*").eq("id", id).eq("is_deleted", False).eq("created_by", user["id"]).execute()
    if not exists.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    opp = exists.data[0]
    update_data = payload.dict(exclude_unset=True)
    
    # Auto-update probability if stage changes
    if "stage" in update_data and update_data["stage"] != opp["stage"]:
        stage_probs = {
            'prospecting': 10, 'qualification': 20, 'proposal': 50,
            'negotiation': 80, 'closed_won': 100, 'closed_lost': 0
        }
        if "probability" not in update_data:
            update_data["probability"] = stage_probs.get(update_data["stage"], opp["probability"])
            
    res = supabase.table("opportunities").update(update_data).eq("id", id).execute()
    return {"success": True, "data": res.data[0], "message": "Opportunity updated successfully"}

@router.delete("/{id}")
async def delete_opportunity(id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("opportunities").update({"is_deleted": True, "deleted_at": datetime.utcnow().isoformat()}).eq("id", id).eq("created_by", user["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return {"success": True, "message": "Opportunity deleted successfully"}
