from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List, Dict, Any
from config.database import supabase
from utils.auth import get_current_user, authorize
from schemas.ticket import TicketCreate, TicketUpdate, Ticket
from datetime import datetime, timedelta

router = APIRouter(prefix="/tickets", tags=["Tickets"])

def calculate_sla_deadlines(priority: str, created_at: datetime):
    # Simplified SLA logic
    if priority == "urgent":
        resp = 1
        res = 4
    elif priority == "high":
        resp = 4
        res = 24
    elif priority == "medium":
        resp = 24
        res = 72
    else:
        resp = 48
        res = 144
    return {
        "responseDeadline": (created_at + timedelta(hours=resp)).isoformat(),
        "resolutionDeadline": (created_at + timedelta(hours=res)).isoformat()
    }

@router.post("/", status_code=201)
async def create_ticket(payload: TicketCreate, user: dict = Depends(get_current_user)):
    data = payload.dict()
    priority = data.get("priority", "medium")
    now = datetime.utcnow()
    sla = calculate_sla_deadlines(priority, now)
    
    data["sla"] = {**sla, "breached": False}
    
    # Auto-assign to agent with lowest ticket count
    agents_res = supabase.table("users").select("id").eq("role", "agent").eq("is_active", True).eq("is_deleted", False).execute()
    assigned_to = None
    if agents_res.data:
        # Just pick the first one for now or implement logic
        assigned_to = agents_res.data[0]["id"]
    
    data["assigned_to"] = assigned_to
    res = supabase.table("tickets").insert(data).execute()
    return {"success": True, "data": res.data[0], "message": "Ticket created successfully"}

@router.get("/")
async def get_tickets(
    page: int = 1,
    limit: int = 10,
    status: str = "",
    priority: str = "",
    search: str = "",
    user: dict = Depends(get_current_user)
):
    query = supabase.table("tickets").select("*, contact_id(*), account_id(*), assigned_to(*)").eq("is_deleted", False)
    
    if user["role"] == "agent":
        query = query.eq("assigned_to", user["id"])
        
    if status: query = query.eq("status", status)
    if priority: query = query.eq("priority", priority)
    if search:
        query = query.or_(f"subject.ilike.%{search}%,description.ilike.%{search}%")

    start = (page - 1) * limit
    end = start + limit - 1
    
    # count
    count_query = supabase.table("tickets").select("id", count="exact").eq("is_deleted", False)
    if user["role"] == "agent": count_query = count_query.eq("assigned_to", user["id"])
    count_res = count_query.execute()
    total = count_res.count if hasattr(count_res, 'count') else len(count_res.data)

    res = query.order("created_at", desc=True).range(start, end).execute()
    
    return {
        "success": True,
        "data": {
            "tickets": res.data,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "limit": limit
        },
        "message": "Tickets fetched successfully"
    }

@router.get("/{id}")
async def get_ticket_by_id(id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("tickets").select("*, contact_id(*), account_id(*), assigned_to(*)").eq("id", id).eq("is_deleted", False).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket = res.data[0]
    if user["role"] == "agent" and ticket["assigned_to"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
        
    return {"success": True, "data": ticket, "message": "Ticket details fetched successfully"}

@router.post("/{id}/replies")
async def add_ticket_reply(id: str, payload: dict, user: dict = Depends(get_current_user)):
    res = supabase.table("tickets").select("*").eq("id", id).eq("is_deleted", False).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket = res.data[0]
    replies = ticket.get("replies", [])
    replies.append({
        "body": payload["body"],
        "author_id": user["id"],
        "created_at": datetime.utcnow().isoformat()
    })
    
    update_data = {"replies": replies}
    if user["role"] in ["agent", "manager"]:
        update_data["status"] = "in_progress"
        
    res = supabase.table("tickets").update(update_data).eq("id", id).execute()
    return {"success": True, "data": res.data[0], "message": "Reply added successfully"}
