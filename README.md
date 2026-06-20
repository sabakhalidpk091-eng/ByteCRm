# ByteCRM Backend (FastAPI)

Modern CRM backend migrated from Node.js to FastAPI with Supabase integration.

## Features
- **FastAPI**: High-performance Python framework.
- **Supabase**: PostgreSQL database with real-time capabilities.
- **Authentication**: JWT based secure auth.
- **Real-time**: WebSocket integration for activity broadcasting.
- **Modules**: Accounts, Leads, Opportunities, Tasks, Campaigns, Tickets.

## Tech Stack
- Python 3.9+
- FastAPI
- Supabase (PostgreSQL)
- Pydantic
- WebSockets

## Setup
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Set up `.env` with `SUPABASE_URL` and `SUPABASE_SECRET_KEY`.
4. Run locally: `python main.py`

## Deployment
Managed via `vercel.json` for seamless Vercel deployment.
