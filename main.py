from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routes import auth, users, accounts, contacts, leads, opportunities, tasks, activities, campaigns, tickets, reports, dashboard, pipeline, uploads
from fastapi.staticfiles import StaticFiles
from fastapi import WebSocket, WebSocketDisconnect
from utils.websocket import manager
import os

app = FastAPI(title="ByteCRM API", version="2.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory exists (Try-except for Read-only filesystems like Vercel)
try:
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
except OSError:
    print("Warning: Could not create uploads directory (Read-only filesystem)")

# Serve static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# WebSocket Endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive, though we mainly send from server -> client
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# Register Routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(accounts.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
app.include_router(leads.router, prefix="/api")
app.include_router(opportunities.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(activities.router, prefix="/api")
app.include_router(campaigns.router, prefix="/api")
app.include_router(tickets.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to ByteCRM FastAPI backend", "docs": "/docs"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
