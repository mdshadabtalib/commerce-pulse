"""
Database setup with SQLAlchemy for CommercePulse
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database URL - will use SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./commercepulse.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=True  # Set to False in production
)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Database Models

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    status = Column(String(50), default="active")
    email_verified = Column(Boolean, default=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")


class Organization(Base):
    """Organization model"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True)
    status = Column(String(50), default="active")
    timezone = Column(String(50), default="UTC")
    default_currency = Column(String(10), default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="organization")


class Customer(Base):
    """Customer model"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), index=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    phone = Column(String(50))
    segment = Column(String(50))  # vip, repeat, at_risk, one_time, new
    total_spent = Column(Float, default=0.0)
    orders_count = Column(Integer, default=0)
    lifetime_value = Column(Float, default=0.0)
    average_order_value = Column(Float, default=0.0)
    last_order_at = Column(DateTime, nullable=True)
    first_order_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Product(Base):
    """Product model"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    title = Column(String(500), nullable=False)
    sku = Column(String(255), index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)
    status = Column(String(50), default="active")  # active, archived, draft
    product_type = Column(String(255))
    vendor = Column(String(255))
    inventory_quantity = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Order(Base):
    """Order model"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    order_number = Column(String(255), unique=True, index=True)
    status = Column(String(50), default="pending")  # pending, paid, shipped, completed, cancelled
    currency = Column(String(10), default="USD")
    subtotal_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    shipping_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    total_quantity = Column(Integer, default=0)
    customer_email = Column(String(255))
    ordered_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class Dataset(Base):
    """Dataset model - connected data sources"""
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    source_type = Column(String(100))  # shopify, woocommerce, amazon, stripe, csv
    status = Column(String(50), default="pending")  # pending, ready, importing, failed
    records_count = Column(Integer, default=0)
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Database helper functions

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def seed_demo_data():
    """Seed demo data for testing"""
    import bcrypt
    
    db = SessionLocal()
    
    try:
        # Check if demo org exists
        demo_org = db.query(Organization).filter_by(slug="demo-org").first()
        if not demo_org:
            print("Creating demo organization...")
            demo_org = Organization(
                name="Demo Commerce",
                slug="demo-org",
                status="active",
                timezone="UTC",
                default_currency="USD"
            )
            db.add(demo_org)
            db.commit()
            db.refresh(demo_org)
        
        # Check if demo user exists
        demo_user = db.query(User).filter_by(email="demo@commercepulse.com").first()
        if not demo_user:
            print("Creating demo user...")
            # Hash password directly with bcrypt
            password_bytes = "demo123".encode('utf-8')
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_bytes, salt)
            
            demo_user = User(
                email="demo@commercepulse.com",
                full_name="Demo User",
                password_hash=hashed.decode('utf-8'),
                status="active",
                email_verified=True,
                organization_id=demo_org.id
            )
            db.add(demo_user)
            db.commit()
        
        # Add demo customers
        if db.query(Customer).count() == 0:
            print("Creating demo customers...")
            demo_customers = [
                Customer(
                    organization_id=demo_org.id,
                    email="sarah.chen@example.com",
                    first_name="Sarah",
                    last_name="Chen",
                    segment="vip",
                    total_spent=12450.75,
                    orders_count=48,
                    lifetime_value=12450.75,
                    average_order_value=259.39
                ),
                Customer(
                    organization_id=demo_org.id,
                    email="michael.rodriguez@example.com",
                    first_name="Michael",
                    last_name="Rodriguez",
                    segment="repeat",
                    total_spent=3240.50,
                    orders_count=12,
                    lifetime_value=3240.50,
                    average_order_value=270.04
                ),
                Customer(
                    organization_id=demo_org.id,
                    email="emily.watson@example.com",
                    first_name="Emily",
                    last_name="Watson",
                    segment="at_risk",
                    total_spent=1890.25,
                    orders_count=8,
                    lifetime_value=1890.25,
                    average_order_value=236.28
                )
            ]
            for customer in demo_customers:
                db.add(customer)
            db.commit()
        
        # Add demo products
        if db.query(Product).count() == 0:
            print("Creating demo products...")
            demo_products = [
                Product(
                    organization_id=demo_org.id,
                    title="Wireless Bluetooth Headphones",
                    sku="WBH-001",
                    description="Premium wireless headphones with noise cancellation",
                    price=129.99,
                    cost=65.00,
                    status="active",
                    product_type="Electronics",
                    vendor="AudioTech",
                    inventory_quantity=156
                ),
                Product(
                    organization_id=demo_org.id,
                    title="Organic Cotton T-Shirt",
                    sku="OCT-001",
                    description="100% organic cotton, sustainably sourced",
                    price=29.99,
                    cost=12.50,
                    status="active",
                    product_type="Clothing",
                    vendor="EcoWear",
                    inventory_quantity=2134
                ),
                Product(
                    organization_id=demo_org.id,
                    title="Premium Yoga Mat",
                    sku="YM-001",
                    description="Non-slip, eco-friendly yoga mat",
                    price=79.99,
                    cost=35.00,
                    status="active",
                    product_type="Sports",
                    vendor="ZenFit",
                    inventory_quantity=89
                )
            ]
            for product in demo_products:
                db.add(product)
            db.commit()
        
        print("Demo data seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    seed_demo_data()
    print("Database setup complete!")
