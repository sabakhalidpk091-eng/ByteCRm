from fastapi import APIRouter, Depends, HTTPException
from config.database import supabase
from utils.auth import get_current_user
from typing import List, Dict, Any

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

@router.get("/")
async def get_pipeline(user: dict = Depends(get_current_user)):
    try:
        # Retrieve all active opportunities for logged-in user
        # In Supabase, we use foreign key relations for populate
        res = supabase.table("opportunities") \
            .select("*, account:account_id(*), contact:contact_id(*), assigned_to_user:assigned_to(*)") \
            .eq("is_deleted", False) \
            .eq("created_by", user["id"]) \
            .execute()
        
        opportunities = res.data
        
        pipeline_stages = ['prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost']
        
        stage_columns = []
        for stage in pipeline_stages:
            deals = [o for o in opportunities if o.get("stage") == stage]
            total_value = sum(float(deal.get("value", 0)) for deal in deals)
            stage_columns.append({
                "stage": stage,
                "deals": deals,
                "totalValue": total_value,
                "count": len(deals),
            })
            
        return {"success": True, "data": stage_columns, "message": "Pipeline stages fetched successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
