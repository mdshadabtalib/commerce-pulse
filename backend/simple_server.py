"""
Simple standalone FastAPI server for CommercePulse
This version works without database setup for quick testing
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import uvicorn
from datetime import datetime, timedelta
import jwt

# Configuration
SECRET_KEY = "dev-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(
    title="CommercePulse API",
    description="E-commerce Analytics Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    organization_name: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    status: str = "active"
    roles: list[str] = ["user"]
    permissions: list[str] = []
    organization_id: int = 1
    created_at: str
    email_verified: bool = True

class LoginResponse(TokenResponse):
    user: UserResponse

# Mock database
MOCK_USERS = {
    "demo@commercepulse.com": {
        "id": 1,
        "email": "demo@commercepulse.com",
        "password": "demo123",  # In production, this would be hashed
        "full_name": "Demo User",
        "avatar_url": None,
        "status": "active",
        "organization_id": 1,
        "created_at": "2024-01-01T00:00:00Z"
    }
}

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CommercePulse API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/api/v1/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CommercePulse API",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login endpoint"""
    user = MOCK_USERS.get(request.email)
    
    if not user or user["password"] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create tokens
    access_token = create_access_token({"sub": user["email"], "user_id": user["id"]})
    refresh_token = create_access_token({"sub": user["email"], "type": "refresh"})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "avatar_url": user["avatar_url"],
            "status": user["status"],
            "roles": ["user"],
            "permissions": ["dashboard.view", "sales.view", "customers.view"],
            "organization_id": user["organization_id"],
            "created_at": user["created_at"],
            "email_verified": True
        }
    }

@app.post("/api/v1/auth/register", response_model=LoginResponse)
async def register(request: RegisterRequest):
    """Register new user"""
    if request.email in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = {
        "id": len(MOCK_USERS) + 1,
        "email": request.email,
        "password": request.password,
        "full_name": request.full_name,
        "avatar_url": None,
        "status": "active",
        "organization_id": len(MOCK_USERS) + 1,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    MOCK_USERS[request.email] = new_user
    
    # Create tokens
    access_token = create_access_token({"sub": new_user["email"], "user_id": new_user["id"]})
    refresh_token = create_access_token({"sub": new_user["email"], "type": "refresh"})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": new_user["id"],
            "email": new_user["email"],
            "full_name": new_user["full_name"],
            "avatar_url": new_user["avatar_url"],
            "status": new_user["status"],
            "roles": ["user", "owner"],
            "permissions": ["dashboard.view", "sales.view", "customers.view"],
            "organization_id": new_user["organization_id"],
            "created_at": new_user["created_at"],
            "email_verified": True
        }
    }

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user():
    """Get current user - returns demo user for simplicity"""
    demo_user = MOCK_USERS["demo@commercepulse.com"]
    return {
        "id": demo_user["id"],
        "email": demo_user["email"],
        "full_name": demo_user["full_name"],
        "avatar_url": demo_user["avatar_url"],
        "status": demo_user["status"],
        "roles": ["user"],
        "permissions": ["dashboard.view", "sales.view", "customers.view"],
        "organization_id": demo_user["organization_id"],
        "created_at": demo_user["created_at"],
        "email_verified": True
    }

@app.post("/api/v1/auth/forgot-password")
async def forgot_password(email: EmailStr):
    """Forgot password endpoint - mock implementation"""
    return {"message": "Password reset email sent (mock)"}

@app.post("/api/v1/auth/verify-email")
async def verify_email(token: str):
    """Verify email endpoint - mock implementation"""
    return {"message": "Email verified successfully (mock)"}

@app.post("/api/v1/auth/resend-verification")
async def resend_verification():
    """Resend verification email - mock implementation"""
    return {"message": "Verification email sent (mock)"}

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 CommercePulse API Server Starting...")
    print("="*60)
    print(f"📍 API: http://localhost:8000")
    print(f"📚 Docs: http://localhost:8000/docs")
    print(f"🔐 Demo Login: demo@commercepulse.com / demo123")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
