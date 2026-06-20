from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional
import jwt
from datetime import datetime, timedelta
import bcrypt
import os
import hashlib
import secrets
from config.database import supabase
from schemas.user import UserCreate, User

router = APIRouter(prefix="/auth", tags=["Authentication"])

JWT_SECRET = os.getenv("JWT_SECRET", "bytecrm-jwt-secret-key-102938")
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_MINUTES = 60 * 24 * 7 # 7 days

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRES_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    password: str

@router.post("/register", status_code=201)
async def register(payload: UserCreate):
    # Check if user exists
    exists = supabase.table("users").select("*").eq("email", payload.email).eq("is_deleted", False).execute()
    if exists.data:
        raise HTTPException(status_code=400, detail="A user with this email address already exists.")

    hashed = hash_password(payload.password)
    user_data = payload.dict()
    user_data["password"] = hashed
    
    res = supabase.table("users").insert(user_data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Error creating user")
    
    user = res.data[0]
    token = create_access_token({"id": user["id"], "role": user["role"], "email": user["email"]})
    
    return {
        "success": True,
        "message": "User registered successfully.",
        "data": {
            "token": token,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "isActive": user["is_active"]
            }
        }
    }

@router.post("/login")
async def login(payload: LoginRequest):
    res = supabase.table("users").select("*").eq("email", payload.email).eq("is_deleted", False).execute()
    if not res.data:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    
    user = res.data[0]
    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="User account is deactivated.")
    
    if not verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    
    # Update last login
    supabase.table("users").update({"last_login_at": datetime.utcnow().isoformat()}).eq("id", user["id"]).execute()
    
    token = create_access_token({"id": user["id"], "role": user["role"], "email": user["email"]})
    
    return {
        "success": True,
        "message": "Login successful.",
        "data": {
            "token": token,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "isActive": user["is_active"]
            }
        }
    }

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest):
    res = supabase.table("users").select("*").eq("email", payload.email).eq("is_deleted", False).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="User with this email does not exist.")
    
    user = res.data[0]
    reset_token = secrets.token_hex(20)
    hashed_token = hashlib.sha256(reset_token.encode()).hexdigest()
    expires = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    
    supabase.table("users").update({
        "reset_password_token": hashed_token,
        "reset_password_expires": expires
    }).eq("id", user["id"]).execute()
    
    print(f"[MOCK EMAIL SERVICE] Password reset token generated for {user['email']}: {reset_token}")
    
    return {
        "success": True,
        "message": "Password reset token generated successfully. Link logged to mock email service.",
        "data": {"resetToken": reset_token}
    }

@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest):
    hashed_token = hashlib.sha256(payload.token.encode()).hexdigest()
    
    res = supabase.table("users").select("*").eq("reset_password_token", hashed_token).eq("is_deleted", False).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Invalid reset token.")
    
    user = res.data[0]
    # Check expiry
    if datetime.fromisoformat(user["reset_password_expires"].replace('Z', '+00:00')) < datetime.utcnow().replace(tzinfo=None):
        raise HTTPException(status_code=400, detail="Reset token expired.")
    
    hashed = hash_password(payload.password)
    supabase.table("users").update({
        "password": hashed,
        "reset_password_token": None,
        "reset_password_expires": None
    }).eq("id", user["id"]).execute()
    
    return {
        "success": True,
        "message": "Password has been reset successfully."
    }

@router.get("/me")
async def get_me(user_id: str): # Usually this would be from a dependency
    res = supabase.table("users").select("*").eq("id", user_id).eq("is_deleted", False).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = res.data[0]
    return {
        "success": True,
        "message": "User details retrieved successfully.",
        "data": {
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "isActive": user["is_active"],
                "lastLoginAt": user["last_login_at"]
            }
        }
    }
