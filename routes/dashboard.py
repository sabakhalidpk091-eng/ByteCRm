from fastapi import APIRouter, Depends, HTTPException
from config.database import supabase
from utils.auth import get_current_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    now = datetime.utcnow()
    start_of_month = datetime(now.getFullYear() if hasattr(now, 'getFullYear') else now.year, 
                              now.getMonth() + 1 if hasattr(now, 'getMonth') else now.month, 1).isoformat()
    # Python datetime doesn't have getFullYear, I mean:
    start_of_month = datetime(now.year, now.month, 1).isoformat()
    seven_days_ago = (now - timedelta(days=7)).isoformat()

    # Aggregates
    contacts_count = supabase.table("contacts").select("id", count="exact").eq("is_deleted", False).eq("created_by", user_id).execute().count
    new_contacts_month = supabase.table("contacts").select("id", count="exact").eq("is_deleted", False).eq("created_by", user_id).gte("created_at", start_of_month).execute().count
    
    active_leads = supabase.table("leads").select("id", count="exact").eq("is_deleted", False).eq("created_by", user_id).in_("status", ["new", "contacted", "qualified"]).execute().count
    converted_leads_month = supabase.table("leads").select("id", count="exact").eq("is_deleted", False).eq("created_by", user_id).eq("status", "converted").gte("converted_at", start_of_month).execute().count
    
    open_deals_res = supabase.table("opportunities").select("value").eq("is_deleted", False).eq("created_by", user_id).not_.in_("stage", ["closed_won", "closed_lost"]).execute()
    open_deals_count = len(open_deals_res.data)
    open_deals_value = sum(float(d.get("value", 0)) for d in open_deals_res.data)
    
    won_deals_res = supabase.table("opportunities").select("value").eq("is_deleted", False).eq("created_by", user_id).eq("stage", "closed_won").gte("created_at", start_of_month).execute()
    revenue_mtd = sum(float(d.get("value", 0)) for d in won_deals_res.data)
    
    activities_week = supabase.table("activities").select("id", count="exact").eq("is_deleted", False).eq("created_by", user_id).gte("date", seven_days_ago).execute().count
    
    tasks_overdue = supabase.table("tasks").select("id", count="exact").eq("is_deleted", False).eq("created_by", user_id).in_("status", ["pending", "in_progress"]).lt("due_date", now.isoformat()).execute().count

    # Pipeline by stage
    all_opps = supabase.table("opportunities").select("stage, value").eq("is_deleted", False).eq("created_by", user_id).execute().data
    pipeline_stages = ['prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost']
    pipeline_by_stage = []
    for stage in pipeline_stages:
        stage_opps = [o for o in all_opps if o["stage"] == stage]
        pipeline_by_stage.append({
            "stage": stage,
            "count": len(stage_opps),
            "value": sum(float(o.get("value", 0)) for o in stage_opps)
        })

    return {
        "success": True,
        "message": "Dashboard stats fetched successfully",
        "data": {
            "totalContacts": contacts_count,
            "newContactsThisMonth": new_contacts_month,
            "activeLeads": active_leads,
            "leadsConvertedThisMonth": converted_leads_month,
            "openDeals": {
                "count": open_deals_count,
                "totalValue": open_deals_value,
            },
            "revenueClosedMTD": revenue_mtd,
            "activitiesThisWeek": activities_week,
            "tasksOverdue": tasks_overdue,
            "pipelineByStage": pipeline_by_stage
        }
    }
