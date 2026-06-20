from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from config.database import supabase
from utils.auth import get_current_user
from schemas.lead import LeadCreate, LeadUpdate, Lead
from datetime import datetime

router = APIRouter(prefix="/leads", tags=["Leads"])

@router.post("/", status_code=201)
async def create_lead(payload: LeadCreate, user: dict = Depends(get_current_user)):
    data = payload.dict()
    data["created_by"] = user["id"]
    res = supabase.table("leads").insert(data).execute()
    return {"success": True, "data": res.data[0], "message": "Lead created successfully"}

@router.get("/")
async def get_leads(
    page: int = 1,
    limit: int = 10,
    search: str = "",
    status: str = "",
    source: str = "",
    user: dict = Depends(get_current_user)
):
    query = supabase.table("leads").select("*, assigned_to(*)").eq("is_deleted", False).eq("created_by", user["id"])
    
    if search:
        query = query.or_(f"first_name.ilike.%{search}%,last_name.ilike.%{search}%,email.ilike.%{search}%,company.ilike.%{search}%")
    if status:
        query = query.eq("status", status)
    if source:
        query = query.eq("source", source)

    start = (page - 1) * limit
    end = start + limit - 1
    
    count_res = supabase.table("leads").select("id", count="exact").eq("is_deleted", False).eq("created_by", user["id"]).execute()
    total = count_res.count if hasattr(count_res, 'count') else len(count_res.data)

    res = query.order("created_at", desc=True).range(start, end).execute()
    
    return {
        "success": True,
        "data": {
            "leads": res.data,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "limit": limit
        },
        "message": "Leads fetched successfully"
    }

@router.get("/{id}")
async def get_lead_by_id(id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("leads").select("*, assigned_to(*), converted_contact_id(*), converted_opportunity_id(*)").eq("id", id).eq("is_deleted", False).eq("created_by", user["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"success": True, "data": res.data[0], "message": "Lead details fetched successfully"}

@router.put("/{id}")
async def update_lead(id: str, payload: LeadUpdate, user: dict = Depends(get_current_user)):
    exists = supabase.table("leads").select("id").eq("id", id).eq("is_deleted", False).eq("created_by", user["id"]).execute()
    if not exists.data:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    update_data = payload.dict(exclude_unset=True)
    res = supabase.table("leads").update(update_data).eq("id", id).execute()
    return {"success": True, "data": res.data[0], "message": "Lead updated successfully"}

@router.delete("/{id}")
async def delete_lead(id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("leads").update({"is_deleted": True, "deleted_at": datetime.utcnow().isoformat()}).eq("id", id).eq("created_by", user["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"success": True, "message": "Lead deleted successfully"}

@router.post("/{id}/convert")
async def convert_lead(id: str, payload: dict, user: dict = Depends(get_current_user)):
    # Complex conversion logic
    lead_res = supabase.table("leads").select("*").eq("id", id).eq("created_by", user["id"]).eq("is_deleted", False).execute()
    if not lead_res.data:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead = lead_res.data[0]
    if lead["status"] == "converted":
        raise HTTPException(status_code=400, detail="Lead is already converted")

    contact_data = payload.get("contactData", {})
    account_data = payload.get("accountData", {})
    opportunity_data = payload.get("opportunityData", {})

    # 1. Account
    account_name = account_data.get("name", lead.get("company") or f"{lead['last_name']} (Household)")
    acc_check = supabase.table("accounts").select("*").eq("name", account_name).eq("is_deleted", False).execute()
    if acc_check.data:
        account = acc_check.data[0]
    else:
        account = supabase.table("accounts").insert({
            "name": account_name,
            "industry": account_data.get("industry", "Other"),
            "size": account_data.get("size", "1-10"),
            "phone": account_data.get("phone", lead.get("phone")),
            "created_by": user["id"]
        }).execute().data[0]

    # 2. Contact
    email = contact_data.get("email", lead.get("email") or f"converted.{id}@bytecrm.com").lower()
    con_check = supabase.table("contacts").select("*").eq("email", email).eq("is_deleted", False).execute()
    if con_check.data:
        contact = con_check.data[0]
    else:
        contact = supabase.table("contacts").insert({
            "first_name": contact_data.get("first_name", lead["first_name"]),
            "last_name": contact_data.get("last_name", lead["last_name"]),
            "email": email,
            "phone": contact_data.get("phone", lead.get("phone")),
            "account_id": account["id"],
            "status": "prospect",
            "notes": contact_data.get("notes", lead.get("notes")),
            "created_by": user["id"]
        }).execute().data[0]

    # 3. Opportunity (Optional)
    opportunity = None
    if opportunity_data and opportunity_data.get("name"):
        opportunity = supabase.table("opportunities").insert({
            "name": opportunity_data["name"],
            "account_id": account["id"],
            "contact_id": contact["id"],
            "value": opportunity_data.get("value", 0),
            "stage": opportunity_data.get("stage", "prospecting"),
            "probability": opportunity_data.get("probability", 10),
            "close_date": opportunity_data.get("closeDate"),
            "assigned_to": opportunity_data.get("assignedTo", lead.get("assigned_to") or user["id"]),
            "created_by": user["id"]
        }).execute().data[0]

    # 4. Update Lead
    supabase.table("leads").update({
        "status": "converted",
        "converted_at": datetime.utcnow().isoformat(),
        "converted_contact_id": contact["id"],
        "converted_opportunity_id": opportunity["id"] if opportunity else None
    }).eq("id", id).execute()

    return {
        "success": True,
        "data": {
            "contact": contact,
            "account": account,
            "opportunity": opportunity
        },
        "message": "Lead converted successfully"
    }
