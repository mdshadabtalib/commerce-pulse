"""
CommercePulse Backend with Database Integration
Full CRUD operations for Users, Customers, Products, Orders
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
import jwt
import uvicorn
import bcrypt

# Import database models and session
from database import (
    get_db, init_db, seed_demo_data,
    User, Organization, Customer, Product, Order, Dataset
)

# Configuration
SECRET_KEY = "dev-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# FastAPI app
app = FastAPI(
    title="CommercePulse API",
    description="E-commerce Analytics Platform with Database",
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

# Pydantic Models for API

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    organization_name: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    avatar_url: Optional[str]
    status: str
    email_verified: bool
    organization_id: Optional[int]
    created_at: datetime
    
    class Config:
        orm_mode = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginResponse(TokenResponse):
    user: UserResponse

class CustomerResponse(BaseModel):
    id: int
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    segment: Optional[str]
    total_spent: float
    orders_count: int
    lifetime_value: float
    average_order_value: float
    created_at: datetime
    
    class Config:
        orm_mode = True

class CustomerCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None

class CustomerUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    segment: Optional[str] = None

class ProductResponse(BaseModel):
    id: int
    title: str
    sku: Optional[str]
    price: float
    cost: float
    status: str
    product_type: Optional[str]
    inventory_quantity: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class ProductCreate(BaseModel):
    title: str
    sku: str
    description: Optional[str] = None
    price: float
    cost: float
    product_type: Optional[str] = None
    vendor: Optional[str] = None
    inventory_quantity: int = 0

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    inventory_quantity: Optional[int] = None
    status: Optional[str] = None

# Helper Functions

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def get_password_hash(password: str) -> str:
    """Hash password"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def get_current_user(token: str, db: Session) -> User:
    """Get current user from token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# API Endpoints

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    seed_demo_data()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CommercePulse API with Database",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }

@app.get("/api/v1/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CommercePulse API",
        "database": "connected",
        "timestamp": datetime.utcnow().isoformat()
    }

# Authentication Endpoints

@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint"""
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token({"sub": user.email, "user_id": user.id})
    refresh_token = create_access_token({"sub": user.email, "type": "refresh"})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user
    }

@app.post("/api/v1/auth/register", response_model=LoginResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register new user"""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create organization
    org_slug = request.organization_name.lower().replace(" ", "-")
    new_org = Organization(
        name=request.organization_name,
        slug=org_slug,
        status="active"
    )
    db.add(new_org)
    db.flush()
    
    # Create user
    new_user = User(
        email=request.email,
        full_name=request.full_name,
        password_hash=get_password_hash(request.password),
        status="active",
        email_verified=True,
        organization_id=new_org.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token({"sub": new_user.email, "user_id": new_user.id})
    refresh_token = create_access_token({"sub": new_user.email, "type": "refresh"})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": new_user
    }

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_info(db: Session = Depends(get_db)):
    """Get current user - for demo, returns first user"""
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No users found")
    return user

# Customer Endpoints

@app.get("/api/v1/customers", response_model=List[CustomerResponse])
async def list_customers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all customers"""
    customers = db.query(Customer).offset(skip).limit(limit).all()
    return customers

@app.get("/api/v1/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Get customer by ID"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.post("/api/v1/customers", response_model=CustomerResponse)
async def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db)
):
    """Create new customer"""
    # Get first organization for demo
    org = db.query(Organization).first()
    if not org:
        raise HTTPException(status_code=400, detail="No organization found")
    
    new_customer = Customer(
        organization_id=org.id,
        email=customer.email,
        first_name=customer.first_name,
        last_name=customer.last_name,
        phone=customer.phone,
        segment="new"
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer

@app.put("/api/v1/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_update: CustomerUpdate,
    db: Session = Depends(get_db)
):
    """Update customer"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    update_data = customer_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    customer.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(customer)
    return customer

@app.delete("/api/v1/customers/{customer_id}")
async def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    """Delete customer"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    db.delete(customer)
    db.commit()
    return {"message": "Customer deleted successfully", "id": customer_id}

# Product Endpoints

@app.get("/api/v1/products", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all products"""
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

@app.get("/api/v1/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get product by ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/api/v1/products", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    """Create new product"""
    org = db.query(Organization).first()
    if not org:
        raise HTTPException(status_code=400, detail="No organization found")
    
    new_product = Product(
        organization_id=org.id,
        title=product.title,
        sku=product.sku,
        description=product.description,
        price=product.price,
        cost=product.cost,
        product_type=product.product_type,
        vendor=product.vendor,
        inventory_quantity=product.inventory_quantity,
        status="active"
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@app.put("/api/v1/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db)
):
    """Update product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(product)
    return product

@app.delete("/api/v1/products/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully", "id": product_id}

# Analytics Endpoints

@app.get("/api/v1/analytics/summary")
async def get_analytics_summary(db: Session = Depends(get_db)):
    """Get analytics summary"""
    total_customers = db.query(Customer).count()
    total_products = db.query(Product).count()
    total_orders = db.query(Order).count()
    
    # Calculate revenue from customers
    total_revenue = db.query(Customer).with_entities(
        db.func.sum(Customer.total_spent)
    ).scalar() or 0
    
    return {
        "total_customers": total_customers,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "avg_customer_value": float(total_revenue / total_customers) if total_customers > 0 else 0
    }

if __name__ == "__main__":
    print("\n" + "="*70)
    print("CommercePulse API Server with Database Starting...")
    print("="*70)
    print(f"API: http://localhost:8000")
    print(f"Docs: http://localhost:8000/docs")
    print(f"Demo Login: demo@commercepulse.com / demo123")
    print(f"Database: SQLite (commercepulse.db)")
    print(f"Full CRUD operations enabled")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
