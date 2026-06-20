import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_SECRET_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_SECRET_KEY must be set in .env")

supabase: Client = create_client(url, key)
