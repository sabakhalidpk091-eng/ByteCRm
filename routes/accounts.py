from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from config.database import supabase
from utils.auth import get_current_user
from schemas.account import AccountCreate, AccountUpdate, Account
from datetime import datetime

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.post("/", status_code=201)
async def create_account(payload: AccountCreate, user: dict = Depends(get_current_user)):
    data = payload.dict()
    data["created_by"] = user["id"]
    
    res = supabase.table("accounts").insert(data).execute()
    if not res.data:
         raise HTTPException(status_code=500, detail="Error creating account")
    return {"success": True, "data": res.data[0], "message": "Account created successfully"}

@router.get("/")
async def get_accounts(
    page: int = 1,
    limit: int = 10,
    search: str = "",
    industry: str = "",
    size: str = "",
    status: str = "",
    user: dict = Depends(get_current_user)
):
    query = supabase.table("accounts").select("*, primary_contact_id(*)").eq("is_deleted", False).eq("created_by", user["id"])
    
    if search:
        # Supabase filtering for 'or' is a bit different
        query = query.or_(f"name.ilike.%{search}%,industry.ilike.%{search}%,domain.ilike.%{search}%")
    
    if industry:
        query = query.eq("industry", industry)
    if size:
        query = query.eq("size", size)
    if status:
        query = query.eq("status", status)
        
    # Pagination
    start = (page - 1) * limit
    end = start + limit - 1
    
    # Get total count
    count_res = supabase.table("accounts").select("id", count="exact").eq("is_deleted", False).eq("created_by", user["id"]).execute()
    total = count_res.count if hasattr(count_res, 'count') else len(count_res.data)

    res = query.order("created_at", desc=True).range(start, end).execute()
    
    return {
        "success": True,
        "data": {
            "accounts": res.data,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "limit": limit
        },
        "message": "Accounts fetched successfully"
    }

@router.get("/{id}")
async def get_account_by_id(id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("accounts").select("*, primary_contact_id(*)").eq("id", id).eq("is_deleted", False).eq("created_by", user["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"success": True, "data": res.data[0], "message": "Account fetched successfully"}

@router.put("/{id}")
async def update_account(id: str, payload: AccountUpdate, user: dict = Depends(get_current_user)):
    # Verify ownership
    exists = supabase.table("accounts").select("id").eq("id", id).eq("is_deleted", False).eq("created_by", user["id"]).execute()
    if not exists.data:
        raise HTTPException(status_code=404, detail="Account not found")
    
    update_data = payload.dict(exclude_unset=True)
    res = supabase.table("accounts").update(update_data).eq("id", id).execute()
    
    return {"success": True, "data": res.data[0], "message": "Account updated successfully"}

@router.delete("/{id}")
async def delete_account(id: str, user: dict = Depends(get_current_user)):
    # Soft delete
    res = supabase.table("accounts").update({
        "is_deleted": True,
        "deleted_at": datetime.utcnow().isoformat()
    }).eq("id", id).eq("created_by", user["id"]).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Account not found")
        
    return {"success": True, "message": "Account deleted successfully"}
