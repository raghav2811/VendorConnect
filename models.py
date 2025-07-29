from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    VENDOR = "vendor"
    BUYER = "buyer"
    STAFF = "staff"

class TransactionType(str, Enum):
    IN = "in"
    OUT = "out"
    ADJUSTMENT = "adjustment"

class StockStatus(str, Enum):
    AVAILABLE = "available"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"

# Base models first (no dependencies)
class Vendor(BaseModel):
    id: Optional[int] = None
    name: str
    contact_person: str
    phone: str
    email: EmailStr
    address: str
    business_type: str = "Restaurant"
    description: Optional[str] = None
    is_active: bool = True
    is_approved: bool = False  # Vendors need approval
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class VendorCreate(BaseModel):
    name: str
    contact_person: str
    phone: str
    email: EmailStr
    address: str
    business_type: str = "Restaurant"
    description: Optional[str] = None

class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: EmailStr
    full_name: str
    role: UserRole
    vendor_id: Optional[int] = None  # Links vendor users to their vendor record
    is_active: bool = True
    hashed_password: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Related data
    vendor: Optional[Vendor] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.BUYER
    vendor_id: Optional[int] = None

class UserLogin(BaseModel):
    username: str
    password: str
    user_type: Optional[str] = None  # 'buyer', 'vendor', 'admin'

class VendorRegistration(BaseModel):
    # User details
    username: str
    email: EmailStr
    full_name: str
    password: str
    
    # Vendor details
    business_name: str
    contact_person: str
    phone: str
    business_email: EmailStr
    address: str
    business_type: str = "Restaurant"
    description: Optional[str] = None

class BuyerRegistration(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str
    phone: Optional[str] = None
    address: Optional[str] = None

class MenuItem(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    price: float
    category: str
    vendor_id: int
    is_available: bool = True
    image_url: Optional[str] = None
    preparation_time: Optional[int] = None  # in minutes
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Related data
    vendor: Optional[Vendor] = None

class MenuItemCreate(BaseModel):
    name: str
    description: str
    price: float
    category: str
    vendor_id: int
    image_url: Optional[str] = None
    preparation_time: Optional[int] = None  # in minutes
    is_available: bool = True

class Stock(BaseModel):
    id: Optional[int] = None
    item_name: str
    description: str
    unit: str  # kg, liter, piece, etc.
    current_stock: int = 0
    minimum_stock: int = 10
    maximum_stock: int = 1000
    unit_cost: float = 0.0
    vendor_id: int
    reorder_level: int = 20
    status: StockStatus = StockStatus.AVAILABLE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Related data
    vendor: Optional[Vendor] = None

class StockCreate(BaseModel):
    item_name: str
    description: str
    unit: str
    minimum_stock: int = 10
    maximum_stock: int = 1000
    unit_cost: float = 0.0
    vendor_id: int
    reorder_level: int = 20

class StockTransaction(BaseModel):
    id: Optional[int] = None
    stock_id: int
    transaction_type: TransactionType
    quantity: int
    unit_cost: float = 0.0
    total_cost: Optional[float] = None
    reference_number: Optional[str] = None
    notes: str = ""
    created_by: int
    created_at: Optional[datetime] = None
    
    # Related data
    stock: Optional[Stock] = None
    user: Optional[User] = None

class StockTransactionCreate(BaseModel):
    stock_id: int
    transaction_type: TransactionType
    quantity: int
    unit_cost: float = 0.0
    reference_number: Optional[str] = None
    notes: str = ""

class OrderItem(BaseModel):
    id: Optional[int] = None
    order_id: int
    menu_item_id: int
    quantity: int
    unit_price: float
    total_price: float
    
    # Related data
    menu_item: Optional[MenuItem] = None

class Order(BaseModel):
    id: Optional[int] = None
    order_number: str
    vendor_id: int
    buyer_id: int
    total_amount: float
    status: str = "pending"  # pending, confirmed, preparing, ready, delivered, cancelled
    order_date: datetime
    delivery_date: Optional[datetime] = None
    delivery_address: Optional[str] = None
    notes: str = ""
    created_by: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Related data
    vendor: Optional[Vendor] = None
    buyer: Optional[User] = None
    items: Optional[List[OrderItem]] = None

class OrderCreate(BaseModel):
    vendor_id: int
    items: List[dict]  # [{"menu_item_id": 1, "quantity": 2}, ...]
    delivery_address: Optional[str] = None
    notes: str = ""

class DashboardStats(BaseModel):
    total_vendors: int
    total_menu_items: int
    total_stock_items: int
    low_stock_count: int
    total_stock_value: float
    recent_transactions: List[StockTransaction]

class VendorPerformance(BaseModel):
    vendor_id: int
    vendor_name: str
    total_orders: int
    total_amount: float
    average_order_value: float
    last_order_date: Optional[datetime]

class MonthlyTransactionSummary(BaseModel):
    month: str
    total_in: int
    total_out: int
    total_adjustments: int
    net_change: int 