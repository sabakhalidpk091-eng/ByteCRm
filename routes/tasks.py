from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from config.database import supabase
from utils.auth import get_current_user
from schemas.task import TaskCreate, TaskUpdate, Task
from datetime import datetime

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/", status_code=201)
async def create_task(payload: TaskCreate, user: dict = Depends(get_current_user)):
    data = payload.dict()
    data["created_by"] = user["id"]
    if data.get("status") == "completed":
        data["completed_at"] = datetime.utcnow().isoformat()
        
    res = supabase.table("tasks").insert(data).execute()
    return {"success": True, "data": res.data[0], "message": "Task created successfully"}

@router.get("/")
async def get_tasks(
    page: int = 1,
    limit: int = 10,
    status: str = "",
    priority: str = "",
    assigned_to: str = "",
    overdue: bool = False,
    user: dict = Depends(get_current_user)
):
    query = supabase.table("tasks").select("*, assigned_to(*), contact_id(*), account_id(*), opportunity_id(*)").eq("is_deleted", False).eq("created_by", user["id"])
    
    if status:
        query = query.eq("status", status)
    if priority:
        query = query.eq("priority", priority)
    if assigned_to:
        query = query.eq("assigned_to", assigned_to)
    if overdue:
        query = query.lt("due_date", datetime.utcnow().isoformat()).in_("status", ["pending", "in_progress"])

    start = (page - 1) * limit
    end = start + limit - 1
    
    count_res = supabase.table("tasks").select("id", count="exact").eq("is_deleted", False).eq("created_by", user["id"]).execute()
    total = count_res.count if hasattr(count_res, 'count') else len(count_res.data)

    res = query.order("due_date", desc=False).range(start, end).execute()
    
    return {
        "success": True,
        "data": {
            "tasks": res.data,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "limit": limit
        },
        "message": "Tasks fetched successfully"
    }

@router.get("/{id}")
async def get_task_by_id(id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("tasks").select("*, assigned_to(*), contact_id(*), account_id(*), opportunity_id(*)").eq("id", id).eq("is_deleted", False).eq("created_by", user["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "data": res.data[0], "message": "Task details fetched successfully"}

@router.put("/{id}")
async def update_task(id: str, payload: TaskUpdate, user: dict = Depends(get_current_user)):
    exists = supabase.table("tasks").select("*").eq("id", id).eq("is_deleted", False).eq("created_by", user["id"]).execute()
    if not exists.data:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = exists.data[0]
    update_data = payload.dict(exclude_unset=True)
    
    if "status" in update_data and update_data["status"] != task["status"]:
        if update_data["status"] == "completed":
            update_data["completed_at"] = datetime.utcnow().isoformat()
        else:
            update_data["completed_at"] = None

    res = supabase.table("tasks").update(update_data).eq("id", id).execute()
    return {"success": True, "data": res.data[0], "message": "Task updated successfully"}

@router.delete("/{id}")
async def delete_task(id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("tasks").update({"is_deleted": True, "deleted_at": datetime.utcnow().isoformat()}).eq("id", id).eq("created_by", user["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "message": "Task deleted successfully"}
