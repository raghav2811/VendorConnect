import os
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from supabase import create_client, Client
from models import (
    User, Vendor, MenuItem, Stock, StockTransaction, Order, OrderItem,
    UserCreate, VendorCreate, MenuItemCreate, StockCreate, StockTransactionCreate,
    OrderCreate, TransactionType, StockStatus, VendorPerformance, MonthlyTransactionSummary
)


class Database:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_anon_key:
            raise ValueError("Missing required environment variables: SUPABASE_URL, SUPABASE_ANON_KEY")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_anon_key)

    # User Management
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        try:
            result = self.supabase.table("users").insert({
                "username": user_data.username,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "hashed_password": user_data.hashed_password,
                "role": user_data.role,
                "is_active": user_data.is_active,
                "vendor_id": user_data.vendor_id
            }).execute()
            
            if result.data:
                return User(**result.data[0])
            else:
                raise Exception("Failed to create user")
        except Exception as e:
            print(f"Error creating user: {e}")
            raise

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            result = self.supabase.table("users").select("*").eq("username", username).execute()
            if result.data:
                user_data = result.data[0]
                
                # If user has a vendor_id, fetch the vendor data
                if user_data.get("vendor_id"):
                    vendor_result = self.supabase.table("vendors").select("*").eq("id", user_data["vendor_id"]).execute()
                    if vendor_result.data:
                        user_data["vendor"] = vendor_result.data[0]
                
                return User(**user_data)
            return None
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            result = self.supabase.table("users").select("*").eq("email", email).execute()
            if result.data:
                user_data = result.data[0]
                
                # If user has a vendor_id, fetch the vendor data
                if user_data.get("vendor_id"):
                    vendor_result = self.supabase.table("vendors").select("*").eq("id", user_data["vendor_id"]).execute()
                    if vendor_result.data:
                        user_data["vendor"] = vendor_result.data[0]
                
                return User(**user_data)
            return None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            result = self.supabase.table("users").select("*").eq("id", user_id).execute()
            if result.data:
                user_data = result.data[0]
                
                # If user has a vendor_id, fetch the vendor data
                if user_data.get("vendor_id"):
                    vendor_result = self.supabase.table("vendors").select("*").eq("id", user_data["vendor_id"]).execute()
                    if vendor_result.data:
                        user_data["vendor"] = vendor_result.data[0]
                
                return User(**user_data)
            return None
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None

    async def update_user_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        try:
            result = self.supabase.table("users").update({
                "last_login": datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()
            return result.data is not None
        except Exception as e:
            print(f"Error updating last login: {e}")
            return False

    # Registration methods
    async def register_vendor(self, vendor_data: VendorCreate, user_data: UserCreate, hashed_password: str) -> tuple[User, Vendor]:
        """Register a new vendor with user account"""
        try:
            # First create the vendor
            vendor_result = self.supabase.table("vendors").insert({
                "name": vendor_data.name,
                "email": vendor_data.email,
                "phone": vendor_data.phone,
                "address": vendor_data.address,
                "contact_person": vendor_data.contact_person,
                "business_type": vendor_data.business_type,
                "description": vendor_data.description,
                "is_approved": False,  # Vendors need approval
                "is_active": True
            }).execute()
            
            if not vendor_result.data:
                raise Exception("Failed to create vendor")
            
            vendor = Vendor(**vendor_result.data[0])
            
            # Create the user with the hashed password
            user_result = self.supabase.table("users").insert({
                "username": user_data.username,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "hashed_password": hashed_password,
                "role": user_data.role,
                "is_active": True,
                "vendor_id": vendor.id
            }).execute()
            
            if not user_result.data:
                raise Exception("Failed to create user")
                
            user = User(**user_result.data[0])
            
            return user, vendor
        except Exception as e:
            print(f"Error registering vendor: {e}")
            raise

    async def register_buyer(self, user_data: UserCreate, hashed_password: str) -> User:
        """Register a new buyer"""
        try:
            # Create the user with the hashed password
            user_result = self.supabase.table("users").insert({
                "username": user_data.username,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "hashed_password": hashed_password,
                "role": user_data.role,
                "is_active": True,
                "vendor_id": None
            }).execute()
            
            if not user_result.data:
                raise Exception("Failed to create user")
                
            user = User(**user_result.data[0])
            return user
        except Exception as e:
            print(f"Error registering buyer: {e}")
            raise

    # Vendor Management
    async def get_vendors(self) -> List[Vendor]:
        """Get all vendors"""
        try:
            result = self.supabase.table("vendors").select("*").order("name").execute()
            vendors = []
            for vendor_data in result.data:
                vendor = Vendor(**vendor_data)
                vendors.append(vendor)
            return vendors
        except Exception as e:
            print(f"Error getting vendors: {e}")
            return []

    async def get_approved_vendors(self) -> List[Vendor]:
        """Get only approved vendors for buyers"""
        try:
            result = self.supabase.table("vendors").select("*").eq("is_approved", True).eq("is_active", True).order("name").execute()
            vendors = []
            for vendor_data in result.data:
                vendor = Vendor(**vendor_data)
                vendors.append(vendor)
            return vendors
        except Exception as e:
            print(f"Error getting approved vendors: {e}")
            return []

    async def get_pending_vendors(self) -> List[Vendor]:
        """Get vendors pending approval"""
        try:
            result = self.supabase.table("vendors").select("*").eq("is_approved", False).order("created_at", desc=True).execute()
            vendors = []
            for vendor_data in result.data:
                vendor = Vendor(**vendor_data)
                vendors.append(vendor)
            return vendors
        except Exception as e:
            print(f"Error getting pending vendors: {e}")
            return []

    async def get_vendor_by_id(self, vendor_id: int) -> Optional[Vendor]:
        """Get vendor by ID"""
        try:
            result = self.supabase.table("vendors").select("*").eq("id", vendor_id).execute()
            if result.data:
                return Vendor(**result.data[0])
            return None
        except Exception as e:
            print(f"Error getting vendor by ID {vendor_id}: {e}")
            return None

    async def create_vendor(self, vendor_data: VendorCreate) -> Vendor:
        """Create a new vendor"""
        try:
            result = self.supabase.table("vendors").insert({
                "name": vendor_data.name,
                "email": vendor_data.email,
                "phone": vendor_data.phone,
                "address": vendor_data.address,
                "contact_person": vendor_data.contact_person,
                "business_type": vendor_data.business_type,
                "description": vendor_data.description,
                "is_approved": vendor_data.is_approved,
                "is_active": vendor_data.is_active
            }).execute()
            
            if result.data:
                return Vendor(**result.data[0])
            else:
                raise Exception("Failed to create vendor")
        except Exception as e:
            print(f"Error creating vendor: {e}")
            raise

    async def approve_vendor(self, vendor_id: int) -> bool:
        """Approve a vendor"""
        try:
            result = self.supabase.table("vendors").update({
                "is_approved": True
            }).eq("id", vendor_id).execute()
            return result.data is not None
        except Exception as e:
            print(f"Error approving vendor: {e}")
            return False

    async def reject_vendor(self, vendor_id: int) -> bool:
        """Reject a vendor (soft delete or mark as rejected)"""
        try:
            result = self.supabase.table("vendors").update({
                "is_approved": False,
                "is_active": False
            }).eq("id", vendor_id).execute()
            return result.data is not None
        except Exception as e:
            print(f"Error rejecting vendor: {e}")
            return False

    # Menu Management
    async def get_menu_items(self, vendor_id: Optional[int] = None) -> List[MenuItem]:
        """Get menu items, optionally filtered by vendor"""
        try:
            query = self.supabase.table("menu_items").select("*")
            if vendor_id:
                query = query.eq("vendor_id", vendor_id)
            
            result = query.order("category").order("name").execute()
            menu_items = []
            for item_data in result.data:
                menu_item = MenuItem(**item_data)
                menu_items.append(menu_item)
            return menu_items
        except Exception as e:
            print(f"Error getting menu items: {e}")
            return []

    async def get_vendor_menu_items(self, vendor_id: int) -> List[MenuItem]:
        """Get menu items for a specific vendor"""
        try:
            result = self.supabase.table("menu_items").select("*").eq("vendor_id", vendor_id).order("category").order("name").execute()
            menu_items = []
            for item_data in result.data:
                menu_item = MenuItem(**item_data)
                menu_items.append(menu_item)
            return menu_items
        except Exception as e:
            print(f"Error getting vendor menu items: {e}")
            return []

    async def get_all_menu_items(self) -> List[MenuItem]:
        """Get all menu items across all vendors"""
        try:
            result = self.supabase.table("menu_items").select("*").order("category").order("name").execute()
            menu_items = []
            for item_data in result.data:
                menu_item = MenuItem(**item_data)
                menu_items.append(menu_item)
            return menu_items
        except Exception as e:
            print(f"Error getting all menu items: {e}")
            return []

    async def create_menu_item(self, menu_item_data: MenuItemCreate) -> MenuItem:
        """Create a new menu item"""
        try:
            # Build insert data - only include non-None values
            insert_data = {
                "vendor_id": menu_item_data.vendor_id,
                "name": menu_item_data.name,
                "description": menu_item_data.description,
                "price": menu_item_data.price,
                "category": menu_item_data.category,
                "is_available": menu_item_data.is_available
            }
            
            # Only add optional fields if they have values
            if menu_item_data.image_url:
                insert_data["image_url"] = menu_item_data.image_url
            if menu_item_data.preparation_time is not None:
                insert_data["preparation_time"] = menu_item_data.preparation_time
                
            result = self.supabase.table("menu_items").insert(insert_data).execute()
            
            if result.data:
                return MenuItem(**result.data[0])
            else:
                raise Exception("Failed to create menu item")
        except Exception as e:
            print(f"Error creating menu item: {e}")
            raise

    # Stock Management
    async def get_stock_items(self, vendor_id: Optional[int] = None) -> List[Stock]:
        """Get stock items, optionally filtered by vendor"""
        try:
            query = self.supabase.table("stock").select("*")
            if vendor_id:
                query = query.eq("vendor_id", vendor_id)
            
            result = query.order("item_name").execute()
            stock_items = []
            for stock_data in result.data:
                stock_item = Stock(**stock_data)
                stock_items.append(stock_item)
            return stock_items
        except Exception as e:
            print(f"Error getting stock items: {e}")
            return []

    async def get_all_stock_items(self) -> List[Stock]:
        """Get all stock items across all vendors"""
        try:
            result = self.supabase.table("stock").select("*").order("item_name").execute()
            stock_items = []
            for stock_data in result.data:
                stock_item = Stock(**stock_data)
                stock_items.append(stock_item)
            return stock_items
        except Exception as e:
            print(f"Error getting all stock items: {e}")
            return []

    async def create_stock_item(self, stock_data: StockCreate) -> Stock:
        """Create a new stock item"""
        try:
            result = self.supabase.table("stock").insert({
                "vendor_id": stock_data.vendor_id,
                "item_name": stock_data.item_name,
                "description": stock_data.description,
                "unit": stock_data.unit,
                "current_stock": stock_data.current_stock,
                "minimum_stock": stock_data.minimum_stock,
                "maximum_stock": stock_data.maximum_stock,
                "reorder_level": stock_data.reorder_level,
                "unit_cost": stock_data.unit_cost
            }).execute()
            
            if result.data:
                return Stock(**result.data[0])
            else:
                raise Exception("Failed to create stock item")
        except Exception as e:
            print(f"Error creating stock item: {e}")
            raise

    async def update_stock_quantity(self, stock_id: int, new_quantity: float) -> bool:
        """Update stock quantity"""
        try:
            result = self.supabase.table("stock").update({
                "current_stock": new_quantity,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", stock_id).execute()
            return result.data is not None
        except Exception as e:
            print(f"Error updating stock quantity: {e}")
            return False

    async def get_low_stock_items(self, vendor_id: Optional[int] = None) -> List[Stock]:
        """Get items with low stock (current_stock <= reorder_level)"""
        try:
            query = self.supabase.table("stock").select("*")
            if vendor_id:
                query = query.eq("vendor_id", vendor_id)
            
            result = query.execute()
            low_stock_items = []
            
            for stock_data in result.data:
                stock_item = Stock(**stock_data)
                # Filter in Python since Supabase doesn't support column-to-column comparisons in filters
                if stock_item.current_stock <= stock_item.reorder_level:
                    low_stock_items.append(stock_item)
            
            return low_stock_items
        except Exception as e:
            print(f"Error getting low stock items: {e}")
            return []

    # Stock Transaction Management
    async def get_stock_transactions(self, vendor_id: Optional[int] = None, limit: int = 50) -> List[StockTransaction]:
        """Get stock transactions, optionally filtered by vendor"""
        try:
            query = self.supabase.table("stock_transactions").select("*")
            if vendor_id:
                query = query.eq("vendor_id", vendor_id)
            
            result = query.order("created_at", desc=True).limit(limit).execute()
            transactions = []
            for transaction_data in result.data:
                transaction = StockTransaction(**transaction_data)
                transactions.append(transaction)
            return transactions
        except Exception as e:
            print(f"Error getting stock transactions: {e}")
            return []

    async def get_recent_stock_transactions(self, limit: int = 10) -> List[StockTransaction]:
        """Get recent stock transactions across all vendors"""
        try:
            result = self.supabase.table("stock_transactions").select("*").order("created_at", {"ascending": False}).limit(limit).execute()
            transactions = []
            for transaction_data in result.data:
                transaction = StockTransaction(**transaction_data)
                transactions.append(transaction)
            return transactions
        except Exception as e:
            print(f"Error getting recent stock transactions: {e}")
            return []

    async def create_stock_transaction(self, transaction_data: StockTransactionCreate) -> StockTransaction:
        """Create a new stock transaction"""
        try:
            result = self.supabase.table("stock_transactions").insert({
                "stock_id": transaction_data.stock_id,
                "vendor_id": transaction_data.vendor_id,
                "transaction_type": transaction_data.transaction_type,
                "quantity": transaction_data.quantity,
                "unit_cost": transaction_data.unit_cost,
                "total_cost": transaction_data.total_cost,
                "supplier": transaction_data.supplier,
                "notes": transaction_data.notes,
                "reference_number": transaction_data.reference_number
            }).execute()
            
            if result.data:
                return StockTransaction(**result.data[0])
            else:
                raise Exception("Failed to create stock transaction")
        except Exception as e:
            print(f"Error creating stock transaction: {e}")
            raise

    # Analytics and Reporting
    async def get_vendor_performance(self, vendor_id: int) -> VendorPerformance:
        """Get performance metrics for a vendor"""
        try:
            # This is a simplified version - in a real app, you'd have more complex queries
            menu_items_result = self.supabase.table("menu_items").select("*").eq("vendor_id", vendor_id).execute()
            stock_items_result = self.supabase.table("stock").select("*").eq("vendor_id", vendor_id).execute()
            
            return VendorPerformance(
                vendor_id=vendor_id,
                total_orders=0,  # Would come from orders table
                total_revenue=0.0,  # Would come from orders table
                average_rating=0.0,  # Would come from reviews table
                total_menu_items=len(menu_items_result.data) if menu_items_result.data else 0,
                active_menu_items=len([item for item in menu_items_result.data if item.get("is_available", False)]) if menu_items_result.data else 0,
                total_stock_items=len(stock_items_result.data) if stock_items_result.data else 0,
                low_stock_alerts=len(await self.get_low_stock_items(vendor_id))
            )
        except Exception as e:
            print(f"Error getting vendor performance: {e}")
            return VendorPerformance(vendor_id=vendor_id)

    async def get_monthly_transaction_summary(self, vendor_id: int, month: int, year: int) -> MonthlyTransactionSummary:
        """Get monthly transaction summary for a vendor"""
        try:
            # Construct date range for the month
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            result = self.supabase.table("stock_transactions").select("*").eq("vendor_id", vendor_id).gte("created_at", start_date.isoformat()).lt("created_at", end_date.isoformat()).execute()
            
            transactions = result.data if result.data else []
            
            total_in = sum(t["quantity"] for t in transactions if t["transaction_type"] == "IN")
            total_out = sum(t["quantity"] for t in transactions if t["transaction_type"] == "OUT")
            total_cost = sum(t["total_cost"] for t in transactions if t["total_cost"])
            
            return MonthlyTransactionSummary(
                vendor_id=vendor_id,
                month=month,
                year=year,
                total_transactions=len(transactions),
                total_stock_in=total_in,
                total_stock_out=total_out,
                total_cost=total_cost,
                unique_items=len(set(t["stock_id"] for t in transactions))
            )
        except Exception as e:
            print(f"Error getting monthly transaction summary: {e}")
            return MonthlyTransactionSummary(vendor_id=vendor_id, month=month, year=year)

    async def get_all_users(self) -> List[User]:
        """Get all users for admin management"""
        try:
            result = self.supabase.table("users").select("*").execute()
            users = []
            for user_data in result.data:
                user = User(**user_data)
                users.append(user)
            return users
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []

    # Order Management Methods
    async def create_order(self, order_data: OrderCreate, buyer_id: int) -> Order:
        """Create a new order"""
        try:
            import uuid
            from datetime import datetime
            
            # Generate unique order number
            order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Calculate total amount
            total_amount = 0
            for item in order_data.items:
                menu_item = await self.get_menu_item_by_id(item["menu_item_id"])
                total_amount += menu_item.price * item["quantity"]
            
            # Add delivery fee
            delivery_fee = 30
            total_amount += delivery_fee
            
            # Create order
            order_result = self.supabase.table("orders").insert({
                "order_number": order_number,
                "vendor_id": order_data.vendor_id,
                "buyer_id": buyer_id,
                "total_amount": total_amount,
                "status": "pending",
                "order_date": datetime.now().isoformat(),
                "delivery_address": order_data.delivery_address,
                "notes": order_data.notes,
                "created_by": buyer_id
            }).execute()
            
            if not order_result.data:
                raise Exception("Failed to create order")
                
            order = Order(**order_result.data[0])
            
            # Create order items
            for item in order_data.items:
                menu_item = await self.get_menu_item_by_id(item["menu_item_id"])
                item_total = menu_item.price * item["quantity"]
                
                self.supabase.table("order_items").insert({
                    "order_id": order.id,
                    "menu_item_id": item["menu_item_id"],
                    "quantity": item["quantity"],
                    "unit_price": menu_item.price,
                    "total_price": item_total
                }).execute()
            
            return order
            
        except Exception as e:
            print(f"Error creating order: {e}")
            raise
    
    async def get_menu_item_by_id(self, item_id: int) -> MenuItem:
        """Get a single menu item by ID"""
        try:
            result = self.supabase.table("menu_items").select("*").eq("id", item_id).execute()
            if result.data:
                return MenuItem(**result.data[0])
            else:
                raise Exception(f"Menu item {item_id} not found")
        except Exception as e:
            print(f"Error getting menu item: {e}")
            raise
    
    async def update_order_status(self, order_id: int, status: str, updated_by: int) -> bool:
        """Update order status"""
        try:
            result = self.supabase.table("orders").update({
                "status": status,
                "updated_at": datetime.now().isoformat()
            }).eq("id", order_id).execute()
            
            return bool(result.data)
        except Exception as e:
            print(f"Error updating order status: {e}")
            return False
    
    async def get_vendor_orders(self, vendor_id: int) -> List[Order]:
        """Get orders for a specific vendor"""
        try:
            result = self.supabase.table("orders").select("*").eq("vendor_id", vendor_id).order("created_at", desc=True).execute()
            orders = []
            for order_data in result.data:
                order = Order(**order_data)
                # Get order items
                items_result = self.supabase.table("order_items").select("*, menu_items(*)").eq("order_id", order.id).execute()
                order_items = []
                for item_data in items_result.data:
                    order_item = OrderItem(**item_data)
                    if item_data.get("menu_items"):
                        order_item.menu_item = MenuItem(**item_data["menu_items"])
                    order_items.append(order_item)
                order.items = order_items
                
                # Get buyer info
                buyer_result = self.supabase.table("users").select("*").eq("id", order.buyer_id).execute()
                if buyer_result.data:
                    order.buyer = User(**buyer_result.data[0])
                    
                orders.append(order)
            return orders
        except Exception as e:
            print(f"Error getting vendor orders: {e}")
            return []
    
    async def get_buyer_orders(self, buyer_id: int) -> List[Order]:
        """Get orders for a specific buyer"""
        try:
            result = self.supabase.table("orders").select("*").eq("buyer_id", buyer_id).order("created_at", desc=True).execute()
            orders = []
            for order_data in result.data:
                order = Order(**order_data)
                # Get order items
                items_result = self.supabase.table("order_items").select("*, menu_items(*)").eq("order_id", order.id).execute()
                order_items = []
                for item_data in items_result.data:
                    order_item = OrderItem(**item_data)
                    if item_data.get("menu_items"):
                        order_item.menu_item = MenuItem(**item_data["menu_items"])
                    order_items.append(order_item)
                order.items = order_items
                
                # Get vendor info
                vendor_result = self.supabase.table("vendors").select("*").eq("id", order.vendor_id).execute()
                if vendor_result.data:
                    order.vendor = Vendor(**vendor_result.data[0])
                    
                orders.append(order)
            return orders
        except Exception as e:
            print(f"Error getting buyer orders: {e}")
            return []
    
    async def get_all_orders(self) -> List[Order]:
        """Get all orders for admin overview"""
        try:
            result = self.supabase.table("orders").select("*").order("created_at", desc=True).execute()
            orders = []
            for order_data in result.data:
                order = Order(**order_data)
                # Get vendor and buyer info
                vendor_result = self.supabase.table("vendors").select("*").eq("id", order.vendor_id).execute()
                if vendor_result.data:
                    order.vendor = Vendor(**vendor_result.data[0])
                    
                buyer_result = self.supabase.table("users").select("*").eq("id", order.buyer_id).execute()
                if buyer_result.data:
                    order.buyer = User(**buyer_result.data[0])
                    
                orders.append(order)
            return orders
        except Exception as e:
            print(f"Error getting all orders: {e}")
            return []

    async def get_vendor_by_id(self, vendor_id: int) -> Optional[Vendor]:
        """Get vendor by ID"""
        try:
            result = self.supabase.table("vendors").select("*").eq("id", vendor_id).execute()
            if result.data:
                return Vendor(**result.data[0])
            return None
        except Exception as e:
            print(f"Error getting vendor by ID {vendor_id}: {e}")
            return None

    # Analytics and Reporting Methods for Real Data
    async def get_vendor_performance_report(self) -> List[VendorPerformance]:
        """Get vendor performance report with real data"""
        try:
            vendors = await self.get_vendors()
            performance_data = []
            
            for vendor in vendors:
                # Get orders for this vendor
                orders_result = self.supabase.table("orders").select("*").eq("vendor_id", vendor.id).execute()
                orders = orders_result.data if orders_result.data else []
                
                total_orders = len(orders)
                total_amount = sum(float(order.get("total_amount", 0)) for order in orders)
                average_order_value = total_amount / total_orders if total_orders > 0 else 0
                
                # Get last order date
                last_order_date = None
                if orders:
                    last_order = max(orders, key=lambda x: x.get("order_date", ""))
                    last_order_date = last_order.get("order_date")
                
                performance_data.append(VendorPerformance(
                    vendor_id=vendor.id,
                    vendor_name=vendor.name,
                    total_orders=total_orders,
                    total_amount=total_amount,
                    average_order_value=average_order_value,
                    last_order_date=last_order_date
                ))
            
            return performance_data
        except Exception as e:
            print(f"Error getting vendor performance report: {e}")
            return []

    async def get_monthly_transaction_summary(self) -> List[MonthlyTransactionSummary]:
        """Get monthly transaction summary for all vendors"""
        try:
            # Get transactions from the last 12 months
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            result = self.supabase.table("stock_transactions").select("*").gte("created_at", start_date.isoformat()).lte("created_at", end_date.isoformat()).execute()
            transactions = result.data if result.data else []
            
            # Group by month
            monthly_data = {}
            for transaction in transactions:
                try:
                    trans_date = datetime.fromisoformat(transaction["created_at"].replace('Z', '+00:00'))
                    month_key = trans_date.strftime("%B %Y")
                    
                    if month_key not in monthly_data:
                        monthly_data[month_key] = {
                            "month": month_key,
                            "total_in": 0,
                            "total_out": 0,
                            "total_adjustments": 0,
                            "net_change": 0
                        }
                    
                    quantity = int(transaction.get("quantity", 0))
                    trans_type = transaction.get("transaction_type", "")
                    
                    if trans_type == "in":
                        monthly_data[month_key]["total_in"] += quantity
                        monthly_data[month_key]["net_change"] += quantity
                    elif trans_type == "out":
                        monthly_data[month_key]["total_out"] += quantity
                        monthly_data[month_key]["net_change"] -= quantity
                    elif trans_type == "adjustment":
                        monthly_data[month_key]["total_adjustments"] += abs(quantity)
                        
                except Exception as e:
                    print(f"Error processing transaction: {e}")
                    continue
            
            # Convert to list and sort by date
            monthly_list = []
            for month_data in monthly_data.values():
                monthly_list.append(MonthlyTransactionSummary(**month_data))
            
            # Sort by date (most recent first)
            monthly_list.sort(key=lambda x: datetime.strptime(x.month, "%B %Y"), reverse=True)
            
            return monthly_list[:12]  # Return last 12 months
        except Exception as e:
            print(f"Error getting monthly transaction summary: {e}")
            return []

    async def get_sales_analytics(self) -> Dict[str, Any]:
        """Get comprehensive sales analytics"""
        try:
            # Get all orders
            orders_result = self.supabase.table("orders").select("*").execute()
            orders = orders_result.data if orders_result.data else []
            
            # Calculate total sales
            total_sales = sum(float(order.get("total_amount", 0)) for order in orders)
            total_orders = len(orders)
            
            # Calculate this month's sales
            current_month = datetime.now().replace(day=1)
            this_month_orders = [
                order for order in orders 
                if order.get("order_date") and datetime.fromisoformat(order["order_date"].replace('Z', '+00:00')) >= current_month
            ]
            this_month_sales = sum(float(order.get("total_amount", 0)) for order in this_month_orders)
            
            # Top performing vendors
            vendor_sales = {}
            for order in orders:
                vendor_id = order.get("vendor_id")
                if vendor_id:
                    vendor_sales[vendor_id] = vendor_sales.get(vendor_id, 0) + float(order.get("total_amount", 0))
            
            top_vendors = sorted(vendor_sales.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Order status distribution
            status_counts = {}
            for order in orders:
                status = order.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "total_sales": total_sales,
                "total_orders": total_orders,
                "this_month_sales": this_month_sales,
                "this_month_orders": len(this_month_orders),
                "average_order_value": total_sales / total_orders if total_orders > 0 else 0,
                "top_vendors": top_vendors,
                "status_distribution": status_counts
            }
        except Exception as e:
            print(f"Error getting sales analytics: {e}")
            return {}

    async def get_inventory_analytics(self) -> Dict[str, Any]:
        """Get comprehensive inventory analytics"""
        try:
            # Get all stock items
            stock_result = self.supabase.table("stock").select("*").execute()
            stock_items = stock_result.data if stock_result.data else []
            
            total_stock_items = len(stock_items)
            total_stock_value = sum(
                float(item.get("current_stock", 0)) * float(item.get("unit_cost", 0)) 
                for item in stock_items
            )
            
            # Low stock analysis
            low_stock_items = [
                item for item in stock_items 
                if int(item.get("current_stock", 0)) <= int(item.get("reorder_level", 0))
            ]
            critical_stock_items = [
                item for item in low_stock_items 
                if int(item.get("current_stock", 0)) == 0
            ]
            
            # Stock by vendor
            vendor_stock = {}
            for item in stock_items:
                vendor_id = item.get("vendor_id")
                if vendor_id:
                    if vendor_id not in vendor_stock:
                        vendor_stock[vendor_id] = {"items": 0, "value": 0}
                    vendor_stock[vendor_id]["items"] += 1
                    vendor_stock[vendor_id]["value"] += float(item.get("current_stock", 0)) * float(item.get("unit_cost", 0))
            
            # Get recent stock transactions
            transactions_result = self.supabase.table("stock_transactions").select("*").order("created_at", desc=True).limit(10).execute()
            recent_transactions = transactions_result.data if transactions_result.data else []
            
            return {
                "total_stock_items": total_stock_items,
                "total_stock_value": total_stock_value,
                "low_stock_count": len(low_stock_items),
                "critical_stock_count": len(critical_stock_items),
                "stock_efficiency": (total_stock_items - len(low_stock_items)) / total_stock_items * 100 if total_stock_items > 0 else 100,
                "vendor_stock_distribution": vendor_stock,
                "recent_transactions": recent_transactions
            }
        except Exception as e:
            print(f"Error getting inventory analytics: {e}")
            return {}

    async def get_customer_analytics(self) -> Dict[str, Any]:
        """Get customer behavior analytics"""
        try:
            # Get all buyers
            buyers_result = self.supabase.table("users").select("*").eq("role", "buyer").execute()
            buyers = buyers_result.data if buyers_result.data else []
            
            # Get all orders
            orders_result = self.supabase.table("orders").select("*").execute()
            orders = orders_result.data if orders_result.data else []
            
            total_customers = len(buyers)
            
            # Customer order frequency
            customer_orders = {}
            for order in orders:
                buyer_id = order.get("buyer_id")
                if buyer_id:
                    customer_orders[buyer_id] = customer_orders.get(buyer_id, 0) + 1
            
            # Active customers (customers who have placed orders)
            active_customers = len(customer_orders)
            
            # Average orders per customer
            avg_orders_per_customer = sum(customer_orders.values()) / active_customers if active_customers > 0 else 0
            
            # Customer acquisition (new customers this month)
            current_month = datetime.now().replace(day=1)
            new_customers_this_month = len([
                buyer for buyer in buyers 
                if buyer.get("created_at") and datetime.fromisoformat(buyer["created_at"].replace('Z', '+00:00')) >= current_month
            ])
            
            # Customer retention (customers with more than one order)
            repeat_customers = len([count for count in customer_orders.values() if count > 1])
            retention_rate = repeat_customers / active_customers * 100 if active_customers > 0 else 0
            
            return {
                "total_customers": total_customers,
                "active_customers": active_customers,
                "new_customers_this_month": new_customers_this_month,
                "avg_orders_per_customer": avg_orders_per_customer,
                "retention_rate": retention_rate,
                "repeat_customers": repeat_customers
            }
        except Exception as e:
            print(f"Error getting customer analytics: {e}")
            return {}

    async def get_financial_summary(self) -> Dict[str, Any]:
        """Get financial summary and trends"""
        try:
            # Get all orders
            orders_result = self.supabase.table("orders").select("*").execute()
            orders = orders_result.data if orders_result.data else []
            
            # Calculate monthly revenue for the last 12 months
            monthly_revenue = {}
            current_date = datetime.now()
            
            for i in range(12):
                month_date = current_date.replace(day=1) - timedelta(days=i*30)
                month_key = month_date.strftime("%B %Y")
                monthly_revenue[month_key] = 0
            
            for order in orders:
                if order.get("order_date"):
                    try:
                        order_date = datetime.fromisoformat(order["order_date"].replace('Z', '+00:00'))
                        month_key = order_date.strftime("%B %Y")
                        if month_key in monthly_revenue:
                            monthly_revenue[month_key] += float(order.get("total_amount", 0))
                    except Exception:
                        continue
            
            # Calculate growth trends
            revenue_values = list(monthly_revenue.values())
            if len(revenue_values) >= 2:
                current_month_revenue = revenue_values[0]
                previous_month_revenue = revenue_values[1]
                growth_rate = ((current_month_revenue - previous_month_revenue) / previous_month_revenue * 100) if previous_month_revenue > 0 else 0
            else:
                growth_rate = 0
            
            # Total revenue
            total_revenue = sum(float(order.get("total_amount", 0)) for order in orders)
            
            # Average transaction value
            avg_transaction_value = total_revenue / len(orders) if orders else 0
            
            return {
                "total_revenue": total_revenue,
                "monthly_revenue": monthly_revenue,
                "growth_rate": growth_rate,
                "avg_transaction_value": avg_transaction_value,
                "total_transactions": len(orders)
            }
        except Exception as e:
            print(f"Error getting financial summary: {e}")
            return {}

    async def get_comprehensive_report_data(self) -> Dict[str, Any]:
        """Get all report data in one call for dashboard"""
        try:
            # Get all required data concurrently for better performance
            low_stock_report = await self.get_low_stock_items()
            vendor_performance = await self.get_vendor_performance_report()
            monthly_transactions = await self.get_monthly_transaction_summary()
            sales_analytics = await self.get_sales_analytics()
            inventory_analytics = await self.get_inventory_analytics()
            customer_analytics = await self.get_customer_analytics()
            financial_summary = await self.get_financial_summary()
            
            return {
                "low_stock_report": low_stock_report,
                "vendor_performance": vendor_performance,
                "monthly_transactions": monthly_transactions,
                "sales_analytics": sales_analytics,
                "inventory_analytics": inventory_analytics,
                "customer_analytics": customer_analytics,
                "financial_summary": financial_summary,
                "report_generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error getting comprehensive report data: {e}")
            return {}

    # Vendor-Specific Analytics Methods
    async def get_vendor_analytics_data(self, vendor_id: int) -> Dict[str, Any]:
        """Get comprehensive analytics data for a specific vendor"""
        try:
            # Get vendor's orders
            orders_result = self.supabase.table("orders").select("*").eq("vendor_id", vendor_id).execute()
            orders = orders_result.data if orders_result.data else []
            
            # Get vendor's menu items
            menu_items_result = self.supabase.table("menu_items").select("*").eq("vendor_id", vendor_id).execute()
            menu_items = menu_items_result.data if menu_items_result.data else []
            
            # Get vendor's stock items
            stock_result = self.supabase.table("stock").select("*").eq("vendor_id", vendor_id).execute()
            stock_items = stock_result.data if stock_result.data else []
            
            # Calculate metrics
            total_revenue = sum(float(order.get("total_amount", 0)) for order in orders)
            total_orders = len(orders)
            
            # Current month metrics
            current_month = datetime.now().replace(day=1)
            this_month_orders = [
                order for order in orders 
                if order.get("order_date") and datetime.fromisoformat(order["order_date"].replace('Z', '+00:00')) >= current_month
            ]
            this_month_revenue = sum(float(order.get("total_amount", 0)) for order in this_month_orders)
            
            # Previous month for comparison
            previous_month = (current_month - timedelta(days=1)).replace(day=1)
            previous_month_end = current_month
            previous_month_orders = [
                order for order in orders 
                if order.get("order_date") and 
                previous_month <= datetime.fromisoformat(order["order_date"].replace('Z', '+00:00')) < previous_month_end
            ]
            previous_month_revenue = sum(float(order.get("total_amount", 0)) for order in previous_month_orders)
            
            # Calculate growth rate
            revenue_growth = 0
            if previous_month_revenue > 0:
                revenue_growth = ((this_month_revenue - previous_month_revenue) / previous_month_revenue) * 100
            
            # Customer metrics
            unique_customers = len(set(order.get("buyer_id") for order in orders if order.get("buyer_id")))
            new_customers_this_month = len(set(order.get("buyer_id") for order in this_month_orders if order.get("buyer_id")))
            
            return {
                "revenue_metrics": {
                    "total_revenue": total_revenue,
                    "this_month_revenue": this_month_revenue,
                    "revenue_growth": revenue_growth,
                    "average_order_value": total_revenue / total_orders if total_orders > 0 else 0
                },
                "order_metrics": {
                    "total_orders": total_orders,
                    "this_month_orders": len(this_month_orders),
                    "orders_growth": ((len(this_month_orders) - len(previous_month_orders)) / len(previous_month_orders) * 100) if len(previous_month_orders) > 0 else 0
                },
                "customer_metrics": {
                    "total_customers": unique_customers,
                    "new_customers_this_month": new_customers_this_month,
                    "customer_growth": 0  # Would need customer registration dates
                },
                "business_metrics": {
                    "menu_items_count": len(menu_items),
                    "active_menu_items": len([item for item in menu_items if item.get("is_available", False)]),
                    "stock_items_count": len(stock_items),
                    "average_rating": 4.8  # Placeholder - would come from reviews table
                }
            }
        except Exception as e:
            print(f"Error getting vendor analytics data: {e}")
            return {}

    async def get_vendor_revenue_trend(self, vendor_id: int, period: str = "daily") -> List[Dict[str, Any]]:
        """Get revenue trend data for charts"""
        try:
            orders_result = self.supabase.table("orders").select("*").eq("vendor_id", vendor_id).execute()
            orders = orders_result.data if orders_result.data else []
            
            # Group by period
            trend_data = {}
            now = datetime.now()
            
            if period == "daily":
                # Last 7 days
                for i in range(7):
                    date = now - timedelta(days=i)
                    date_key = date.strftime("%Y-%m-%d")
                    trend_data[date_key] = {"date": date.strftime("%m/%d"), "revenue": 0, "orders": 0}
            elif period == "weekly":
                # Last 8 weeks
                for i in range(8):
                    week_start = now - timedelta(weeks=i)
                    week_key = week_start.strftime("%Y-W%U")
                    trend_data[week_key] = {"date": f"Week {week_start.strftime('%U')}", "revenue": 0, "orders": 0}
            elif period == "monthly":
                # Last 12 months
                for i in range(12):
                    month_date = now.replace(day=1) - timedelta(days=i*30)
                    month_key = month_date.strftime("%Y-%m")
                    trend_data[month_key] = {"date": month_date.strftime("%b %Y"), "revenue": 0, "orders": 0}
            
            # Aggregate order data
            for order in orders:
                if order.get("order_date"):
                    try:
                        order_date = datetime.fromisoformat(order["order_date"].replace('Z', '+00:00'))
                        
                        if period == "daily":
                            key = order_date.strftime("%Y-%m-%d")
                        elif period == "weekly":
                            key = order_date.strftime("%Y-W%U")
                        elif period == "monthly":
                            key = order_date.strftime("%Y-%m")
                        
                        if key in trend_data:
                            trend_data[key]["revenue"] += float(order.get("total_amount", 0))
                            trend_data[key]["orders"] += 1
                    except Exception:
                        continue
            
            # Convert to list and sort
            result = list(trend_data.values())
            result.reverse()  # Most recent first
            return result
        except Exception as e:
            print(f"Error getting vendor revenue trend: {e}")
            return []

    async def get_vendor_order_status_distribution(self, vendor_id: int) -> Dict[str, int]:
        """Get order status distribution for pie chart"""
        try:
            orders_result = self.supabase.table("orders").select("*").eq("vendor_id", vendor_id).execute()
            orders = orders_result.data if orders_result.data else []
            
            status_counts = {}
            for order in orders:
                status = order.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return status_counts
        except Exception as e:
            print(f"Error getting vendor order status distribution: {e}")
            return {}

    async def get_vendor_top_selling_items(self, vendor_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top selling menu items for the vendor"""
        try:
            # Get order items for this vendor
            orders_result = self.supabase.table("orders").select("id").eq("vendor_id", vendor_id).execute()
            order_ids = [order["id"] for order in orders_result.data] if orders_result.data else []
            
            if not order_ids:
                return []
            
            # Get order items with menu item details
            items_result = self.supabase.table("order_items").select("*, menu_items(*)").in_("order_id", order_ids).execute()
            order_items = items_result.data if items_result.data else []
            
            # Aggregate by menu item
            item_stats = {}
            for item in order_items:
                menu_item = item.get("menu_items")
                if menu_item:
                    item_id = menu_item["id"]
                    item_name = menu_item["name"]
                    quantity = int(item.get("quantity", 0))
                    revenue = float(item.get("total_price", 0))
                    
                    if item_id not in item_stats:
                        item_stats[item_id] = {
                            "name": item_name,
                            "orders": 0,
                            "total_quantity": 0,
                            "total_revenue": 0
                        }
                    
                    item_stats[item_id]["orders"] += 1
                    item_stats[item_id]["total_quantity"] += quantity
                    item_stats[item_id]["total_revenue"] += revenue
            
            # Sort by revenue and return top items
            top_items = sorted(item_stats.values(), key=lambda x: x["total_revenue"], reverse=True)
            return top_items[:limit]
        except Exception as e:
            print(f"Error getting vendor top selling items: {e}")
            return []

    async def get_vendor_peak_hours(self, vendor_id: int) -> List[Dict[str, Any]]:
        """Get peak hour analysis for the vendor"""
        try:
            orders_result = self.supabase.table("orders").select("*").eq("vendor_id", vendor_id).execute()
            orders = orders_result.data if orders_result.data else []
            
            # Initialize hour buckets
            hour_stats = {}
            for hour in range(24):
                hour_stats[hour] = {"hour": hour, "orders": 0, "revenue": 0}
            
            # Aggregate by hour
            for order in orders:
                if order.get("order_date"):
                    try:
                        order_date = datetime.fromisoformat(order["order_date"].replace('Z', '+00:00'))
                        hour = order_date.hour
                        
                        hour_stats[hour]["orders"] += 1
                        hour_stats[hour]["revenue"] += float(order.get("total_amount", 0))
                    except Exception:
                        continue
            
            # Filter to only show significant hours and format
            peak_hours = []
            for hour, stats in hour_stats.items():
                if stats["orders"] > 0:
                    hour_12 = hour % 12 if hour % 12 != 0 else 12
                    period = "AM" if hour < 12 else "PM"
                    peak_hours.append({
                        "hour": hour,
                        "display_hour": f"{hour_12} {period}",
                        "orders": stats["orders"],
                        "revenue": stats["revenue"]
                    })
            
            # Sort by orders and return
            peak_hours.sort(key=lambda x: x["orders"], reverse=True)
            return peak_hours[:9]  # Return top 9 for display
        except Exception as e:
            print(f"Error getting vendor peak hours: {e}")
            return []

    async def get_vendor_business_insights(self, vendor_id: int) -> List[Dict[str, Any]]:
        """Generate business insights and recommendations for the vendor"""
        try:
            # Get analytics data for insights
            analytics = await self.get_vendor_analytics_data(vendor_id)
            top_items = await self.get_vendor_top_selling_items(vendor_id, 5)
            peak_hours = await self.get_vendor_peak_hours(vendor_id)
            
            insights = []
            
            # Revenue growth insight
            revenue_growth = analytics.get("revenue_metrics", {}).get("revenue_growth", 0)
            if revenue_growth > 10:
                insights.append({
                    "type": "positive",
                    "icon": "fas fa-trending-up",
                    "title": "Strong Growth",
                    "message": f"Your revenue has increased by {revenue_growth:.1f}% this month. Keep up the great work!"
                })
            elif revenue_growth < -5:
                insights.append({
                    "type": "warning",
                    "icon": "fas fa-trending-down",
                    "title": "Revenue Decline",
                    "message": f"Revenue decreased by {abs(revenue_growth):.1f}% this month. Consider promotional campaigns."
                })
            
            # Peak hours insight
            if peak_hours:
                busiest_hour = peak_hours[0]
                insights.append({
                    "type": "info",
                    "icon": "fas fa-clock",
                    "title": "Peak Hour Opportunity",
                    "message": f"Your busiest time is {busiest_hour['display_hour']} with {busiest_hour['orders']} orders. Consider special offers during peak hours."
                })
            
            # Top items insight
            if top_items:
                best_seller = top_items[0]
                insights.append({
                    "type": "positive",
                    "icon": "fas fa-star",
                    "title": "Bestseller Success",
                    "message": f"'{best_seller['name']}' is your top performer with ₹{best_seller['total_revenue']:.0f} in sales. Consider promoting it more!"
                })
            
            # Menu optimization insight
            menu_items_count = analytics.get("business_metrics", {}).get("menu_items_count", 0)
            active_items = analytics.get("business_metrics", {}).get("active_menu_items", 0)
            if menu_items_count > 0 and active_items / menu_items_count < 0.8:
                insights.append({
                    "type": "neutral",
                    "icon": "fas fa-utensils",
                    "title": "Menu Optimization",
                    "message": "Some menu items aren't available. Update availability or remove items to streamline your menu."
                })
            
            return insights[:4]  # Return top 4 insights
        except Exception as e:
            print(f"Error getting vendor business insights: {e}")
            return [] 