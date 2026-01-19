"""
Creators Hive HQ - Authentication System
JWT-based authentication for admin access
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid
import os

# Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "creators-hive-hq-secret-key-change-in-production-2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

# ============== MODELS ==============

class AdminUser(BaseModel):
    id: str = Field(default_factory=lambda: f"ADMIN-{str(uuid.uuid4())[:8]}")
    email: str
    name: str
    hashed_password: str
    role: str = "admin"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

class AdminUserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class AdminUserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None

# ============== PASSWORD UTILITIES ==============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

# ============== JWT UTILITIES ==============

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        if email is None:
            return None
        return TokenData(email=email, user_id=user_id)
    except JWTError:
        return None

# ============== DEPENDENCY ==============

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db=None):
    """
    Dependency to get the current authenticated user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    token_data = decode_token(token)
    
    if token_data is None:
        raise credentials_exception
    
    # If db is provided, verify user exists
    if db is not None:
        user = await db.admin_users.find_one({"email": token_data.email}, {"_id": 0, "hashed_password": 0})
        if user is None:
            raise credentials_exception
        return user
    
    return {"email": token_data.email, "user_id": token_data.user_id}

async def get_current_active_user(credentials: HTTPAuthorizationCredentials = Depends(security), db=None):
    """
    Dependency to get current active user
    """
    current_user = await get_current_user(credentials, db)
    if db is not None and not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# ============== AUTH FUNCTIONS ==============

async def authenticate_user(db, email: str, password: str) -> Optional[dict]:
    """Authenticate a user by email and password"""
    user = await db.admin_users.find_one({"email": email})
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

async def create_admin_user(db, user_data: AdminUserCreate) -> dict:
    """Create a new admin user"""
    # Check if user already exists
    existing = await db.admin_users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    admin_user = AdminUser(
        email=user_data.email,
        name=user_data.name,
        hashed_password=get_password_hash(user_data.password)
    )
    
    doc = admin_user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.admin_users.insert_one(doc)
    
    # Return user without password
    return {
        "id": admin_user.id,
        "email": admin_user.email,
        "name": admin_user.name,
        "role": admin_user.role,
        "is_active": admin_user.is_active
    }

async def login_user(db, email: str, password: str) -> Token:
    """Login user and return token"""
    user = await authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    await db.admin_users.update_one(
        {"email": email},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Create token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "user_id": user["id"]},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user.get("role", "admin")
        }
    )

# ============== SEED DEFAULT ADMIN ==============

async def seed_default_admin(db):
    """Create a default admin user if none exists"""
    existing = await db.admin_users.count_documents({})
    if existing == 0:
        default_admin = AdminUser(
            id="ADMIN-0001",
            email="admin@hivehq.com",
            name="System Admin",
            hashed_password=get_password_hash("admin123"),
            role="superadmin"
        )
        doc = default_admin.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.admin_users.insert_one(doc)
        return True
    return False

# ============== CREATOR AUTHENTICATION ==============

async def authenticate_creator(db, email: str, password: str) -> Optional[dict]:
    """Authenticate a creator by email and password"""
    creator = await db.creators.find_one({"email": email})
    if not creator:
        return None
    if not creator.get("hashed_password"):
        return None
    if not verify_password(password, creator["hashed_password"]):
        return None
    return creator

async def login_creator(db, email: str, password: str):
    """Login creator and return token"""
    from models_creator import CreatorToken
    
    creator = await authenticate_creator(db, email, password)
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if creator is approved/active
    if creator.get("status") not in ["approved", "active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account status: {creator.get('status')}. Please wait for approval."
        )
    
    # Update last login
    await db.creators.update_one(
        {"email": email},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Create token with creator role
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": creator["email"], 
            "user_id": creator["id"],
            "role": "creator"
        },
        expires_delta=access_token_expires
    )
    
    return CreatorToken(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        creator={
            "id": creator["id"],
            "email": creator["email"],
            "name": creator["name"],
            "status": creator.get("status", "pending"),
            "tier": creator.get("assigned_tier", "Free"),
            "platforms": creator.get("platforms", []),
            "niche": creator.get("niche", "")
        }
    )

async def get_current_creator(credentials: HTTPAuthorizationCredentials = Depends(security), db=None):
    """
    Dependency to get the current authenticated creator from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    token_data = decode_token(token)
    
    if token_data is None:
        raise credentials_exception
    
    # If db is provided, verify creator exists
    if db is not None:
        creator = await db.creators.find_one(
            {"email": token_data.email}, 
            {"_id": 0, "hashed_password": 0}
        )
        if creator is None:
            raise credentials_exception
        return creator
    
    return {"email": token_data.email, "user_id": token_data.user_id}
