from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from config.database import supabase
from utils.auth import get_current_user, authorize
from schemas.user import UserUpdate, User
from datetime import datetime

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/")
async def get_all_users(
    page: int = 1,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    query = supabase.table("users").select("id, name, email, role, is_active, title, avatar, last_login_at").eq("is_deleted", False).eq("is_active", True)
    
    start = (page - 1) * limit
    end = start + limit - 1
    
    res = query.order("name").range(start, end).execute()
    return {
        "success": True,
        "data": {
            "users": res.data,
            "total": len(res.data), # Simplified
            "page": page,
            "limit": limit
        },
        "message": "Users fetched successfully"
    }

@router.get("/{id}")
async def get_user_by_id(id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("users").select("id, name, email, role, is_active, title, avatar, last_login_at").eq("id", id).eq("is_deleted", False).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True, "data": res.data[0], "message": "User details fetched successfully"}

@router.put("/{id}/profile")
async def update_user_profile(id: str, payload: UserUpdate, user: dict = Depends(get_current_user)):
    # Only allow self-update or admin
    if user["id"] != id and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = payload.dict(exclude_unset=True)
    if "password" in update_data:
        # Re-hash password logic if needed
        pass
        
    res = supabase.table("users").update(update_data).eq("id", id).execute()
    return {"success": True, "data": res.data[0], "message": "Profile updated successfully"}

@router.post("/invite")
async def invite_team_member(payload: dict, user: dict = Depends(authorize(["admin"]))):
    # Simplified invite: Just create inactive user
    exists = supabase.table("users").select("id").eq("email", payload["email"]).eq("is_deleted", False).execute()
    if exists.data:
        raise HTTPException(status_code=400, detail="User with this email already exists")
        
    res = supabase.table("users").insert({
        "name": payload["name"],
        "email": payload["email"],
        "role": payload.get("role", "agent"),
        "password": "TempPassword@123", # Should be random
        "is_active": False
    }).execute()
    
    return {"success": True, "data": res.data[0], "message": "Team member invited successfully"}
