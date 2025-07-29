from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from typing import Optional, List
import os
from dotenv import load_dotenv

from database import Database
from models import User, Vendor, MenuItem, Stock, StockTransaction, VendorRegistration, BuyerRegistration, UserRole, VendorCreate, UserCreate, MenuItemCreate, Order, OrderCreate, OrderItem
from auth import AuthService

# Load environment variables
load_dotenv()

app = FastAPI(title="Local Vendor Management System", version="1.0.0")

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize services
db = Database()
auth_service = AuthService()
security = HTTPBearer(auto_error=False)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_current_user(request: Request):
    """Get current authenticated user from cookie"""
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    # Remove 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
    
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        user = await db.get_user_by_id(user_id)
        return user
    except jwt.PyJWTError:
        return None

async def require_auth(request: Request):
    """Require authentication for protected routes"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        user = await get_current_user(request)
        if not user:
            return RedirectResponse(url="/login", status_code=302)
        
        # Get dashboard data with error handling
        try:
            vendors_count = await db.get_vendors_count()
        except Exception as e:
            print(f"Error getting vendors count: {e}")
            vendors_count = 0
            
        try:
            menu_items_count = await db.get_menu_items_count()
        except Exception as e:
            print(f"Error getting menu items count: {e}")
            menu_items_count = 0
            
        try:
            total_stock_value = await db.get_total_stock_value()
        except Exception as e:
            print(f"Error getting total stock value: {e}")
            total_stock_value = 0.0
            
        try:
            low_stock_items = await db.get_low_stock_items()
        except Exception as e:
            print(f"Error getting low stock items: {e}")
            low_stock_items = []
        
        # Role-based dashboard routing
        if user.role == "buyer":
            return RedirectResponse(url="/buyer/dashboard", status_code=302)
        elif user.role == "vendor":
            return RedirectResponse(url="/vendor/dashboard", status_code=302)
        else:  # admin or staff
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "user": user,
                "vendors_count": vendors_count,
                "menu_items_count": menu_items_count,
                "total_stock_value": total_stock_value,
                "low_stock_items": low_stock_items
            })
    except Exception as e:
        print(f"Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    user = await auth_service.authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })
    
    token = auth_service.create_access_token({"sub": str(user.id)})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response

# Registration Routes
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/register/vendor", response_class=HTMLResponse)
async def vendor_register_page(request: Request):
    return templates.TemplateResponse("register_vendor.html", {"request": request})

@app.post("/register/vendor")
async def register_vendor(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    business_name: str = Form(...),
    contact_person: str = Form(...),
    phone: str = Form(...),
    business_email: str = Form(...),
    address: str = Form(...),
    business_type: str = Form("Restaurant"),
    description: str = Form("")
):
    try:
        vendor_reg = VendorRegistration(
            username=username,
            email=email,
            full_name=full_name,
            password=password,
            business_name=business_name,
            contact_person=contact_person,
            phone=phone,
            business_email=business_email,
            address=address,
            business_type=business_type,
            description=description
        )
        
        # Create VendorCreate object from registration data
        vendor_create = VendorCreate(
            name=vendor_reg.business_name,  # Map business_name to name
            contact_person=vendor_reg.contact_person,
            phone=vendor_reg.phone,
            email=vendor_reg.business_email,  # Map business_email to email
            address=vendor_reg.address,
            business_type=vendor_reg.business_type,
            description=vendor_reg.description
        )
        
        # Create UserCreate object from registration data
        user_create = UserCreate(
            username=vendor_reg.username,
            email=vendor_reg.email,
            full_name=vendor_reg.full_name,
            password=vendor_reg.password,
            role=UserRole.VENDOR
        )
        
        hashed_password = auth_service.get_password_hash(password)
        user, vendor = await db.register_vendor(vendor_create, user_create, hashed_password)
        
        return templates.TemplateResponse("register_success.html", {
            "request": request,
            "user_type": "vendor",
            "message": "Vendor registration successful! Please wait for admin approval before you can start selling."
        })
    except Exception as e:
        return templates.TemplateResponse("register_vendor.html", {
            "request": request,
            "error": f"Registration failed: {str(e)}"
        })

@app.get("/register/buyer", response_class=HTMLResponse)
async def buyer_register_page(request: Request):
    return templates.TemplateResponse("register_buyer.html", {"request": request})

@app.post("/register/buyer")
async def register_buyer(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    phone: str = Form(""),
    address: str = Form("")
):
    try:
        buyer_reg = BuyerRegistration(
            username=username,
            email=email,
            full_name=full_name,
            password=password,
            phone=phone if phone else None,
            address=address if address else None
        )
        
        # Create UserCreate object from buyer registration data
        user_create = UserCreate(
            username=buyer_reg.username,
            email=buyer_reg.email,
            full_name=buyer_reg.full_name,
            password=buyer_reg.password,
            role=UserRole.BUYER
        )
        
        hashed_password = auth_service.get_password_hash(password)
        user = await db.register_buyer(user_create, hashed_password)
        
        return templates.TemplateResponse("register_success.html", {
            "request": request,
            "user_type": "buyer",
            "message": "Registration successful! You can now login and start ordering."
        })
    except Exception as e:
        return templates.TemplateResponse("register_buyer.html", {
            "request": request,
                         "error": f"Registration failed: {str(e)}"
         })

# Buyer Routes
@app.get("/buyer/dashboard", response_class=HTMLResponse)
async def buyer_dashboard(request: Request):
    user = await require_auth(request)
    if user.role != "buyer":
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get approved vendors and their menu items
        vendors = await db.get_approved_vendors()
        
        return templates.TemplateResponse("buyer_dashboard.html", {
            "request": request,
            "user": user,
            "vendors": vendors
        })
    except Exception as e:
        print(f"Buyer dashboard error: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")

@app.get("/buyer/vendor/{vendor_id}", response_class=HTMLResponse)
async def buyer_vendor_menu(request: Request, vendor_id: int):
    user = await require_auth(request)
    if user.role != "buyer":
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        vendor = await db.get_vendor_by_id(vendor_id)
        if not vendor or not vendor.is_approved:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        menu_items = await db.get_vendor_menu_items(vendor_id)
        
        return templates.TemplateResponse("buyer_vendor_menu.html", {
            "request": request,
            "user": user,
            "vendor": vendor,
            "menu_items": menu_items
        })
    except Exception as e:
        print(f"Buyer vendor menu error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Vendor Routes
@app.get("/vendor/dashboard", response_class=HTMLResponse)
async def vendor_dashboard(request: Request):
    user = await require_auth(request)
    if user.role != "vendor":
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        if not user.vendor_id:
            raise HTTPException(status_code=400, detail="Vendor account not properly linked")
        
        # Get vendor's own data
        vendor = await db.get_vendor_by_id(user.vendor_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        # Get vendor's menu items and stock
        menu_items = await db.get_vendor_menu_items(user.vendor_id)
        
        # Get vendor's stock items
        try:
            result = db.supabase.table("stock").select("*").eq("vendor_id", user.vendor_id).execute()
            stock_items = [Stock(**item) for item in result.data]
        except:
            stock_items = []
        
        return templates.TemplateResponse("vendor_dashboard.html", {
            "request": request,
            "user": user,
            "vendor": vendor,
            "menu_items": menu_items,
            "stock_items": stock_items,
            "menu_count": len(menu_items),
            "stock_count": len(stock_items)
        })
    except Exception as e:
        print(f"Vendor dashboard error: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")

# Vendor-specific Routes
@app.get("/vendor/menu", response_class=HTMLResponse)
async def vendor_menu_page(request: Request):
    user = await require_auth(request)
    if user.role != "vendor":
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        if not user.vendor_id:
            raise HTTPException(status_code=400, detail="Vendor account not properly linked")
        
        vendor = await db.get_vendor_by_id(user.vendor_id)
        menu_items = await db.get_vendor_menu_items(user.vendor_id)
        
        return templates.TemplateResponse("vendor_menu.html", {
            "request": request,
            "user": user,
            "vendor": vendor,
            "menu_items": menu_items
        })
    except Exception as e:
        print(f"Vendor menu error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/vendor/menu/add", response_class=HTMLResponse)
async def vendor_add_menu_item_page(request: Request):
    user = await require_auth(request)
    if user.role != "vendor":
        raise HTTPException(status_code=403, detail="Access denied")
    
    vendor = await db.get_vendor_by_id(user.vendor_id)
    if not vendor or not vendor.is_approved:
        raise HTTPException(status_code=403, detail="Vendor not approved")
    
    return templates.TemplateResponse("vendor_add_menu_item.html", {
        "request": request,
        "user": user,
        "vendor": vendor
    })

@app.post("/vendor/menu/add")
async def vendor_add_menu_item(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    image_url: str = Form(""),
    preparation_time: int = Form(None)
):
    user = await require_auth(request)
    if user.role != "vendor":
        raise HTTPException(status_code=403, detail="Access denied")
    
    vendor = await db.get_vendor_by_id(user.vendor_id)
    if not vendor or not vendor.is_approved:
        raise HTTPException(status_code=403, detail="Vendor not approved")
    
    try:
        menu_item_create = MenuItemCreate(
            name=name,
            description=description,
            price=price,
            category=category,
            vendor_id=user.vendor_id,
            image_url=image_url if image_url else None,
            preparation_time=preparation_time if preparation_time else None,
            is_available=True
        )
        await db.create_menu_item(menu_item_create)
        return RedirectResponse(url="/vendor/menu", status_code=302)
    except Exception as e:
        return templates.TemplateResponse("vendor_add_menu_item.html", {
            "request": request,
            "user": user,
            "vendor": vendor,
            "error": f"Error adding menu item: {str(e)}"
        })

@app.get("/vendor/stock", response_class=HTMLResponse)
async def vendor_stock_page(request: Request):
    user = await require_auth(request)
    if user.role != "vendor":
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        if not user.vendor_id:
            raise HTTPException(status_code=400, detail="Vendor account not properly linked")
        
        vendor = await db.get_vendor_by_id(user.vendor_id)
        
        # Get vendor's stock items
        result = db.supabase.table("stock").select("*").eq("vendor_id", user.vendor_id).execute()
        stock_items = [Stock(**item) for item in result.data]
        
        return templates.TemplateResponse("vendor_stock.html", {
            "request": request,
            "user": user,
            "vendor": vendor,
            "stock_items": stock_items
        })
    except Exception as e:
        print(f"Vendor stock error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/vendor/profile", response_class=HTMLResponse)
async def vendor_profile_page(request: Request):
    user = await require_auth(request)
    if user.role != "vendor":
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        vendor = await db.get_vendor_by_id(user.vendor_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        return templates.TemplateResponse("vendor_profile.html", {
            "request": request,
            "user": user,
            "vendor": vendor
        })
    except Exception as e:
        print(f"Vendor profile error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/vendor/stock/add", response_class=HTMLResponse)
async def vendor_add_stock_page(request: Request):
    user = await require_auth(request)
    if user.role != "vendor":
        raise HTTPException(status_code=403, detail="Access denied")
    
    vendor = await db.get_vendor_by_id(user.vendor_id)
    if not vendor or not vendor.is_approved:
        raise HTTPException(status_code=403, detail="Vendor not approved")
    
    return templates.TemplateResponse("vendor_add_stock.html", {
        "request": request,
        "user": user,
        "vendor": vendor
    })

@app.post("/vendor/stock/add")
async def vendor_add_stock_item(
    request: Request,
    item_name: str = Form(...),
    description: str = Form(...),
    unit: str = Form(...),
    minimum_stock: int = Form(...),
    maximum_stock: int = Form(...),
    reorder_level: int = Form(...),
    unit_cost: float = Form(...)
):
    user = await require_auth(request)
    if user.role != "vendor":
        raise HTTPException(status_code=403, detail="Access denied")
    
    vendor = await db.get_vendor_by_id(user.vendor_id)
    if not vendor or not vendor.is_approved:
        raise HTTPException(status_code=403, detail="Vendor not approved")
    
    try:
        stock = Stock(
            item_name=item_name,
            description=description,
            unit=unit,
            current_stock=0,
            minimum_stock=minimum_stock,
            maximum_stock=maximum_stock,
            unit_cost=unit_cost,
            vendor_id=user.vendor_id,
            reorder_level=reorder_level
        )
        await db.create_stock_item(stock)
        return RedirectResponse(url="/vendor/stock", status_code=302)
    except Exception as e:
        print(f"Error creating stock item: {e}")
        return templates.TemplateResponse("vendor_add_stock.html", {
            "request": request,
            "user": user,
            "vendor": vendor,
            "error": "Failed to create stock item"
        })
    except Exception as e:
        print(f"Vendor profile error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Admin Routes
@app.get("/admin/vendors", response_class=HTMLResponse)
async def admin_vendors_page(request: Request):
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        vendors = await db.get_vendors()
        return templates.TemplateResponse("admin_vendors.html", {
            "request": request,
            "user": user,
            "vendors": vendors
        })
    except Exception as e:
        print(f"Admin vendors error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/admin/approvals", response_class=HTMLResponse)
async def admin_approvals_page(request: Request):
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get pending vendor approvals
        result = db.supabase.table("vendors").select("*").eq("is_approved", False).eq("is_active", True).execute()
        pending_vendors = [Vendor(**vendor) for vendor in result.data]
        
        return templates.TemplateResponse("admin_approvals.html", {
            "request": request,
            "user": user,
            "pending_vendors": pending_vendors
        })
    except Exception as e:
        print(f"Admin approvals error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/admin/approve_vendor/{vendor_id}")
async def approve_vendor(request: Request, vendor_id: int):
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Approve the vendor
        result = db.supabase.table("vendors").update({
            "is_approved": True,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", vendor_id).execute()
        
        if result.data:
            return {"success": True, "message": "Vendor approved successfully"}
        else:
            return {"success": False, "message": "Failed to approve vendor"}
    except Exception as e:
        print(f"Error approving vendor: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/admin/reject_vendor/{vendor_id}")
async def reject_vendor(request: Request, vendor_id: int):
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Deactivate the vendor
        result = db.supabase.table("vendors").update({
            "is_active": False,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", vendor_id).execute()
        
        if result.data:
            return {"success": True, "message": "Vendor rejected successfully"}
        else:
            return {"success": False, "message": "Failed to reject vendor"}
    except Exception as e:
        print(f"Error rejecting vendor: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}

# Additional Vendor Routes
@app.get("/vendor/orders", response_class=HTMLResponse)
async def vendor_orders_page(request: Request):
    user = await require_auth(request)
    if user.role != "vendor":
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        orders = await db.get_vendor_orders(user.vendor_id)
        return templates.TemplateResponse("vendor_orders.html", {
            "request": request,
            "user": user,
            "orders": orders
        })
    except Exception as e:
        print(f"Error loading vendor orders: {e}")
        return templates.TemplateResponse("vendor_orders.html", {
            "request": request,
            "user": user,
            "orders": [],
            "error": f"Error loading orders: {str(e)}"
        })

@app.get("/vendor/analytics", response_class=HTMLResponse)
async def vendor_analytics_page(request: Request):
    user = await require_auth(request)
    if user.role != "vendor":
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        vendor_id = user.vendor_id
        if not vendor_id:
            raise HTTPException(status_code=400, detail="Vendor ID not found")
        
        # Get comprehensive analytics data
        analytics_data = await db.get_vendor_analytics_data(vendor_id)
        revenue_trend = await db.get_vendor_revenue_trend(vendor_id, "daily")
        order_status = await db.get_vendor_order_status_distribution(vendor_id)
        top_items = await db.get_vendor_top_selling_items(vendor_id, 5)
        peak_hours = await db.get_vendor_peak_hours(vendor_id)
        insights = await db.get_vendor_business_insights(vendor_id)
        
        return templates.TemplateResponse("vendor_analytics.html", {
            "request": request,
            "user": user,
            "analytics_data": analytics_data,
            "revenue_trend": revenue_trend,
            "order_status": order_status,
            "top_items": top_items,
            "peak_hours": peak_hours,
            "insights": insights
        })
    except Exception as e:
        print(f"Error loading vendor analytics: {e}")
        # Fallback with empty data
        return templates.TemplateResponse("vendor_analytics.html", {
            "request": request,
            "user": user,
            "analytics_data": {},
            "revenue_trend": [],
            "order_status": {},
            "top_items": [],
            "peak_hours": [],
            "insights": [],
            "error": f"Unable to load analytics data: {str(e)}"
        })

# Buyer Routes
@app.get("/buyer/browse", response_class=HTMLResponse)
async def buyer_browse_page(request: Request):
    user = await require_auth(request)
    if user.role != "buyer":
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Redirect to buyer dashboard which already has vendor browsing
    return RedirectResponse(url="/buyer/dashboard", status_code=302)

@app.get("/buyer/orders", response_class=HTMLResponse)
async def buyer_orders_page(request: Request):
    user = await require_auth(request)
    if user.role != "buyer":
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        orders = await db.get_buyer_orders(user.id)
        return templates.TemplateResponse("buyer_orders.html", {
            "request": request,
            "user": user,
            "orders": orders
        })
    except Exception as e:
        print(f"Error loading buyer orders: {e}")
        return templates.TemplateResponse("buyer_orders.html", {
            "request": request,
            "user": user,
            "orders": [],
            "error": f"Error loading orders: {str(e)}"
        })

# Order API Endpoints
@app.post("/api/orders")
async def create_order_api(request: Request):
    """Create a new order via API"""
    try:
        user = await require_auth(request)
        if user.role != "buyer":
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get JSON data from request
        data = await request.json()
        
        # Create order object
        order_create = OrderCreate(
            vendor_id=data["vendor_id"],
            items=data["items"],
            delivery_address=data.get("delivery_address", ""),
            notes=data.get("notes", "")
        )
        
        # Create the order
        order = await db.create_order(order_create, user.id)
        
        return {
            "success": True,
            "message": "Order placed successfully!",
            "order_id": order.id,
            "order_number": order.order_number
        }
        
    except Exception as e:
        print(f"Error creating order: {e}")
        raise HTTPException(status_code=400, detail=f"Order creation failed: {str(e)}")

@app.post("/api/orders/{order_id}/status")
async def update_order_status_api(request: Request, order_id: int):
    """Update order status via API"""
    try:
        user = await require_auth(request)
        data = await request.json()
        new_status = data.get("status")
        
        if not new_status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        # Vendors can only update their own orders
        if user.role == "vendor":
            # TODO: Verify this order belongs to the vendor
            pass
        elif user.role != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        success = await db.update_order_status(order_id, new_status, user.id)
        
        if success:
            return {"success": True, "message": "Order status updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update order status")
            
    except Exception as e:
        print(f"Error updating order status: {e}")
        raise HTTPException(status_code=400, detail=f"Status update failed: {str(e)}")

@app.get("/buyer/favorites", response_class=HTMLResponse)
async def buyer_favorites_page(request: Request):
    user = await require_auth(request)
    if user.role != "buyer":
        raise HTTPException(status_code=403, detail="Access denied")
    
    return templates.TemplateResponse("buyer_favorites.html", {
        "request": request,
        "user": user,
        "favorites": []  # Placeholder
    })

@app.get("/buyer/profile", response_class=HTMLResponse)
async def buyer_profile_page(request: Request):
    user = await require_auth(request)
    if user.role != "buyer":
        raise HTTPException(status_code=403, detail="Access denied")
    
    return templates.TemplateResponse("buyer_profile.html", {
        "request": request,
        "user": user
    })

# Additional Admin Routes
@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request):
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = await db.get_all_users()
    return templates.TemplateResponse("admin_users.html", {
        "request": request,
        "user": user,
        "users": users
    })

@app.get("/admin/orders", response_class=HTMLResponse)
async def admin_orders_page(request: Request):
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    orders = await db.get_all_orders()
    return templates.TemplateResponse("admin_orders.html", {
        "request": request,
        "user": user,
        "orders": orders
    })

@app.get("/admin/stock", response_class=HTMLResponse)
async def admin_stock_page(request: Request):
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    stock_items = await db.get_all_stock_items()
    return templates.TemplateResponse("admin_stock.html", {
        "request": request,
        "user": user,
        "stock_items": stock_items
    })

@app.get("/admin/menu", response_class=HTMLResponse)
async def admin_menu_page(request: Request):
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    menu_items = await db.get_all_menu_items()
    return templates.TemplateResponse("admin_menu.html", {
        "request": request,
        "user": user,
        "menu_items": menu_items
    })

@app.get("/admin/reports", response_class=HTMLResponse)
async def admin_reports_page(request: Request):
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    return templates.TemplateResponse("admin_reports.html", {
        "request": request,
        "user": user
    })

# Admin Action Routes
@app.get("/admin/vendors/{vendor_id}/details")
async def get_vendor_details(vendor_id: int, request: Request):
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    vendor = await db.get_vendor_by_id(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return vendor

@app.post("/admin/vendors/{vendor_id}/deactivate")
async def deactivate_vendor(vendor_id: int, request: Request):
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result = db.supabase.table("vendors").update({"is_active": False}).eq("id", vendor_id).execute()
        if result.data:
            return {"success": True, "message": "Vendor deactivated successfully"}
        else:
            return {"success": False, "message": "Failed to deactivate vendor"}
    except Exception as e:
        print(f"Error deactivating vendor: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}

@app.get("/admin/vendors/{vendor_id}/edit", response_class=HTMLResponse)
async def edit_vendor_page(vendor_id: int, request: Request):
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    vendor = await db.get_vendor_by_id(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return templates.TemplateResponse("admin_edit_vendor.html", {
        "request": request,
        "user": user,
        "vendor": vendor
    })

@app.post("/admin/vendors/{vendor_id}/edit")
async def update_vendor(vendor_id: int, request: Request):
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    form = await request.form()
    
    try:
        update_data = {
            "name": form.get("name"),
            "email": form.get("email"),
            "phone": form.get("phone"),
            "address": form.get("address"),
            "contact_person": form.get("contact_person"),
            "business_type": form.get("business_type"),
            "description": form.get("description"),
            "is_active": form.get("is_active") == "on",
            "is_approved": form.get("is_approved") == "on"
        }
        
        result = db.supabase.table("vendors").update(update_data).eq("id", vendor_id).execute()
        
        if result.data:
            return RedirectResponse(url="/admin/vendors", status_code=303)
        else:
            vendor = await db.get_vendor_by_id(vendor_id)
            return templates.TemplateResponse("admin_edit_vendor.html", {
                "request": request,
                "user": user,
                "vendor": vendor,
                "error": "Failed to update vendor"
            })
    except Exception as e:
        print(f"Error updating vendor: {e}")
        vendor = await db.get_vendor_by_id(vendor_id)
        return templates.TemplateResponse("admin_edit_vendor.html", {
            "request": request,
            "user": user,
            "vendor": vendor,
            "error": f"Error: {str(e)}"
        })

@app.get("/admin/users/{user_id}/details")
async def get_user_details(user_id: int, request: Request):
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result = db.supabase.table("users").select("*").eq("id", user_id).execute()
        if result.data:
            return result.data[0]
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        print(f"Error getting user details: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/admin/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_page(user_id: int, request: Request):
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result = db.supabase.table("users").select("*").eq("id", user_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        target_user = result.data[0]
        return templates.TemplateResponse("admin_edit_user.html", {
            "request": request,
            "user": user,
            "target_user": target_user
        })
    except Exception as e:
        print(f"Error getting user for edit: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/admin/users/{user_id}/edit")
async def update_user(user_id: int, request: Request):
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    form = await request.form()
    
    try:
        # Get current user data
        current_result = db.supabase.table("users").select("*").eq("id", user_id).execute()
        if not current_result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        current_user = current_result.data[0]
        
        update_data = {
            "full_name": form.get("full_name"),
            "username": form.get("username"),
            "email": form.get("email"),
            "role": form.get("role"),
            "is_active": form.get("is_active") == "on"
        }
        
        # Handle password update if provided
        new_password = form.get("password")
        if new_password and new_password.strip():
            auth_service = AuthService()
            hashed_password = auth_service.get_password_hash(new_password)
            update_data["hashed_password"] = hashed_password
        
        result = db.supabase.table("users").update(update_data).eq("id", user_id).execute()
        
        if result.data:
            return RedirectResponse(url="/admin/users", status_code=303)
        else:
            return templates.TemplateResponse("admin_edit_user.html", {
                "request": request,
                "user": user,
                "target_user": current_user,
                "error": "Failed to update user"
            })
    except Exception as e:
        print(f"Error updating user: {e}")
        # Get current user data for form
        current_result = db.supabase.table("users").select("*").eq("id", user_id).execute()
        current_user = current_result.data[0] if current_result.data else {}
        return templates.TemplateResponse("admin_edit_user.html", {
            "request": request,
            "user": user,
            "target_user": current_user,
            "error": f"Error: {str(e)}"
        })

@app.delete("/admin/users/{user_id}/delete")
async def delete_user(user_id: int, request: Request):
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Don't allow deleting admin users
        target_user = db.supabase.table("users").select("role").eq("id", user_id).execute()
        if target_user.data and target_user.data[0]["role"] == "admin":
            return {"success": False, "message": "Cannot delete admin users"}
        
        result = db.supabase.table("users").delete().eq("id", user_id).execute()
        if result.data:
            return {"success": True, "message": "User deleted successfully"}
        else:
            return {"success": False, "message": "Failed to delete user"}
    except Exception as e:
        print(f"Error deleting user: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}

# Legacy admin routes (for backward compatibility)
@app.get("/vendors", response_class=HTMLResponse)
async def vendors_page(request: Request):
    user = await require_auth(request)
    vendors = await db.get_vendors()
    return templates.TemplateResponse("vendors.html", {
        "request": request,
        "user": user,
        "vendors": vendors
    })

@app.post("/vendors")
async def create_vendor(
    request: Request,
    name: str = Form(...),
    contact_person: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    address: str = Form(...)
):
    user = await require_auth(request)
    vendor = Vendor(
        name=name,
        contact_person=contact_person,
        phone=phone,
        email=email,
        address=address
    )
    await db.create_vendor(vendor)
    return RedirectResponse(url="/vendors", status_code=302)

@app.get("/menu", response_class=HTMLResponse)
async def menu_page(request: Request):
    user = await require_auth(request)
    menu_items = await db.get_all_menu_items()
    vendors = await db.get_vendors()
    return templates.TemplateResponse("menu.html", {
        "request": request,
        "user": user,
        "menu_items": menu_items,
        "vendors": vendors
    })

@app.post("/menu")
async def create_menu_item(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    vendor_id: int = Form(...),
    preparation_time: int = Form(None),
    image_url: str = Form("")
):
    user = await require_auth(request)
    menu_item_create = MenuItemCreate(
        name=name,
        description=description,
        price=price,
        category=category,
        vendor_id=vendor_id,
        preparation_time=preparation_time if preparation_time else None,
        image_url=image_url if image_url else None,
        is_available=True
    )
    await db.create_menu_item(menu_item_create)
    return RedirectResponse(url="/menu", status_code=302)

@app.get("/stock", response_class=HTMLResponse)
async def stock_page(request: Request):
    user = await require_auth(request)
    stock_items = await db.get_all_stock_items()
    vendors = await db.get_vendors()
    return templates.TemplateResponse("stock.html", {
        "request": request,
        "user": user,
        "stock_items": stock_items,
        "vendors": vendors
    })

@app.post("/stock")
async def create_stock_item(
    request: Request,
    item_name: str = Form(...),
    description: str = Form(...),
    unit: str = Form(...),
    vendor_id: int = Form(...),
    reorder_level: int = Form(...)
):
    user = await require_auth(request)
    stock = Stock(
        item_name=item_name,
        description=description,
        unit=unit,
        current_stock=0,
        vendor_id=vendor_id,
        reorder_level=reorder_level
    )
    await db.create_stock_item(stock)
    return RedirectResponse(url="/stock", status_code=302)

@app.get("/stock/transactions", response_class=HTMLResponse)
async def stock_transactions_page(request: Request):
    user = await require_auth(request)
    transactions = await db.get_recent_stock_transactions(limit=50)
    stock_items = await db.get_all_stock_items()
    return templates.TemplateResponse("stock_transactions.html", {
        "request": request,
        "user": user,
        "transactions": transactions,
        "stock_items": stock_items
    })

@app.post("/stock/transactions")
async def create_stock_transaction(
    request: Request,
    stock_id: int = Form(...),
    transaction_type: str = Form(...),
    quantity: int = Form(...),
    unit_cost: float = Form(0),
    notes: str = Form("")
):
    user = await require_auth(request)
    transaction = StockTransaction(
        stock_id=stock_id,
        transaction_type=transaction_type,
        quantity=quantity,
        unit_cost=unit_cost,
        notes=notes,
        created_by=user.id
    )
    await db.create_stock_transaction(transaction)
    return RedirectResponse(url="/stock/transactions", status_code=302)

@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    user = await require_auth(request)
    
    # Get comprehensive analytics data
    try:
        report_data = await db.get_comprehensive_report_data()
        
        # Extract individual components for template
        low_stock_report = report_data.get("low_stock_report", [])
        vendor_performance = report_data.get("vendor_performance", [])
        monthly_transactions = report_data.get("monthly_transactions", [])
        sales_analytics = report_data.get("sales_analytics", {})
        inventory_analytics = report_data.get("inventory_analytics", {})
        customer_analytics = report_data.get("customer_analytics", {})
        financial_summary = report_data.get("financial_summary", {})
        
        return templates.TemplateResponse("reports.html", {
            "request": request,
            "user": user,
            "low_stock_report": low_stock_report,
            "vendor_performance": vendor_performance,
            "monthly_transactions": monthly_transactions,
            "sales_analytics": sales_analytics,
            "inventory_analytics": inventory_analytics,
            "customer_analytics": customer_analytics,
            "financial_summary": financial_summary,
            "report_generated_at": report_data.get("report_generated_at")
        })
    except Exception as e:
        print(f"Error loading reports: {e}")
        # Fallback to empty data if there's an error
        return templates.TemplateResponse("reports.html", {
            "request": request,
            "user": user,
            "low_stock_report": [],
            "vendor_performance": [],
            "monthly_transactions": [],
            "sales_analytics": {},
            "inventory_analytics": {},
            "customer_analytics": {},
            "financial_summary": {},
            "error": "Unable to load report data. Please try again later."
        })

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 