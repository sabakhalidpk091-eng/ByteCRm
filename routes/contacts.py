from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional, List
import csv
import io
from config.database import supabase
from utils.auth import get_current_user
from schemas.contact import ContactCreate, ContactUpdate, Contact
from datetime import datetime

router = APIRouter(prefix="/contacts", tags=["Contacts"])

@router.post("/", status_code=201)
async def create_contact(payload: ContactCreate, user: dict = Depends(get_current_user)):
    data = payload.dict()
    data["created_by"] = user["id"]
    
    # Check duplicate email
    exists = supabase.table("contacts").select("id").eq("email", payload.email.lower()).eq("is_deleted", False).execute()
    if exists.data:
        raise HTTPException(status_code=400, detail="Contact email already exists")

    res = supabase.table("contacts").insert(data).execute()
    return {"success": True, "data": res.data[0], "message": "Contact created successfully"}

@router.get("/")
async def get_contacts(
    page: int = 1,
    limit: int = 10,
    search: str = "",
    status: str = "",
    account_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = supabase.table("contacts").select("*, account_id(*)").eq("is_deleted", False).eq("created_by", user["id"])
    
    if search:
        query = query.or_(f"first_name.ilike.%{search}%,last_name.ilike.%{search}%,email.ilike.%{search}%")
    
    if status:
        query = query.eq("status", status)
    if account_id:
        query = query.eq("account_id", account_id)
        
    start = (page - 1) * limit
    end = start + limit - 1
    
    count_res = supabase.table("contacts").select("id", count="exact").eq("is_deleted", False).eq("created_by", user["id"]).execute()
    total = count_res.count if hasattr(count_res, 'count') else len(count_res.data)

    res = query.order("created_at", desc=True).range(start, end).execute()
    
    return {
        "success": True,
        "data": {
            "contacts": res.data,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "limit": limit
        },
        "message": "Contacts fetched successfully"
    }

@router.get("/{id}")
async def get_contact_by_id(id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("contacts").select("*, account_id(*)").eq("id", id).eq("is_deleted", False).eq("created_by", user["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"success": True, "data": res.data[0], "message": "Contact fetched successfully"}

@router.put("/{id}")
async def update_contact(id: str, payload: ContactUpdate, user: dict = Depends(get_current_user)):
    exists = supabase.table("contacts").select("*").eq("id", id).eq("is_deleted", False).eq("created_by", user["id"]).execute()
    if not exists.data:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    contact = exists.data[0]
    update_data = payload.dict(exclude_unset=True)
    
    if "email" in update_data and update_data["email"].lower() != contact["email"]:
        dup = supabase.table("contacts").select("id").eq("email", update_data["email"].lower()).eq("is_deleted", False).eq("created_by", user["id"]).execute()
        if dup.data:
            raise HTTPException(status_code=400, detail="Contact email already exists")
    
    res = supabase.table("contacts").update(update_data).eq("id", id).execute()
    return {"success": True, "data": res.data[0], "message": "Contact updated successfully"}

@router.delete("/{id}")
async def delete_contact(id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("contacts").update({
        "is_deleted": True,
        "deleted_at": datetime.utcnow().isoformat()
    }).eq("id", id).eq("created_by", user["id"]).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Contact not found")
        
    return {"success": True, "message": "Contact deleted successfully"}
