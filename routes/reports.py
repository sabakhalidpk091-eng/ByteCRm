from fastapi import APIRouter, Depends, HTTPException, Query
from config.database import supabase
from utils.auth import get_current_user
from typing import Optional, List

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/dashboard-analytics")
async def get_dashboard_analytics(user: dict = Depends(get_current_user)):
    try:
        # 1. Lead Funnel Data
        leads_res = supabase.table("leads").select("status").eq("is_deleted", False).eq("created_by", user["id"]).execute()
        opps_res = supabase.table("opportunities").select("stage").eq("is_deleted", False).eq("created_by", user["id"]).execute()
        
        leads_data = leads_res.data
        opps_data = opps_res.data
        
        lead_funnel = [
            {"stage": "New Leads", "count": len([l for l in leads_data if l["status"] == "new"])},
            {"stage": "Contacted", "count": len([l for l in leads_data if l["status"] == "contacted"])},
            {"stage": "Qualified", "count": len([l for l in leads_data if l["status"] == "qualified"])},
            {"stage": "Proposal", "count": len([o for o in opps_data if o["stage"] == "proposal"])},
            {"stage": "Closed Won", "count": len([o for o in opps_data if o["stage"] == "closed_won"])},
        ]
        
        # 2. Revenue Data (Simplified - for now just current totals)
        closed_won_opps = [o for o in opps_data if o["stage"] == "closed_won"]
        total_revenue = sum(float(o.get("value", 0)) for o in closed_won_opps)
        
        # 3. Metrics
        conversion_rate = (len([l for l in leads_data if l["status"] == "converted"]) / len(leads_data) * 100) if leads_data else 0
        
        return {
            "success": True, 
            "data": {
                "leadFunnelData": lead_funnel,
                "metrics": {
                    "closedRevenueYTD": round(total_revenue),
                    "leadConversionRate": round(conversion_rate, 1),
                    "slaTargetMet": 85.0
                },
                "revenueData": [], # Simplified for now
                "ticketSlaData": [
                    {"name": "Resolved", "value": 65, "color": "#10b981"},
                    {"name": "On Track", "value": 20, "color": "#3b82f6"},
                    {"name": "At Risk", "value": 10, "color": "#f59e0b"},
                    {"name": "Breached", "value": 5, "color": "#ef4444"}
                ]
            }, 
            "message": "Dashboard analytics generated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sales-by-rep")
async def get_sales_by_rep(user: dict = Depends(get_current_user)):
    # Aggregate sales by rep in supabase
    res = supabase.table("opportunities").select("assigned_to(name), value").eq("stage", "closed_won").eq("is_deleted", False).execute()
    
    reps = {}
    for deal in res.data:
        name = deal.get("assigned_to", {}).get("name", "Unknown")
        val = float(deal.get("value", 0))
        if name not in reps: reps[name] = {"rep": name, "closedWon": 0, "totalValue": 0}
        reps[name]["closedWon"] += 1
        reps[name]["totalValue"] += val
        
    return {"success": True, "data": list(reps.values()), "message": "Sales by rep report generated successfully"}

@router.get("/lead-source")
async def get_lead_source(user: dict = Depends(get_current_user)):
    res = supabase.table("leads").select("source").eq("is_deleted", False).execute()
    sources = {}
    for lead in res.data:
        s = lead["source"]
        sources[s] = sources.get(s, 0) + 1
    
    return {"success": True, "data": [{"source": k, "count": v} for k, v in sources.items()], "message": "Lead source report generated successfully"}
