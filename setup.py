#!/usr/bin/env python3
"""
Setup script for Vendor Management System
This script helps initialize the application and create sample data
"""

import asyncio
import os
import sys
from getpass import getpass
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth import AuthService
from database import Database
from models import UserCreate, UserRole, Vendor, MenuItem, Stock

async def create_admin_user():
    """Create an admin user interactively"""
    print("\n🔐 Creating Admin User")
    print("-" * 30)
    
    auth_service = AuthService()
    
    username = input("Enter admin username (default: admin): ").strip() or "admin"
    email = input("Enter admin email: ").strip()
    if not email:
        email = "admin@example.com"
    
    full_name = input("Enter full name (default: System Administrator): ").strip() or "System Administrator"
    
    password = getpass("Enter admin password (default: admin123): ").strip() or "admin123"
    confirm_password = getpass("Confirm password: ").strip() or "admin123"
    
    if password != confirm_password:
        print("❌ Passwords don't match!")
        return False
    
    try:
        user_create = UserCreate(
            username=username,
            email=email,
            full_name=full_name,
            password=password,
            role=UserRole.ADMIN
        )
        
        user = await auth_service.create_user(user_create)
        print(f"✅ Admin user '{username}' created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

async def create_sample_data():
    """Create sample vendors, menu items, and stock"""
    print("\n📦 Creating Sample Data")
    print("-" * 30)
    
    db = Database()
    
    try:
        # Sample Vendors
        vendors_data = [
            {
                "name": "Fresh Foods Supplier",
                "contact_person": "John Smith",
                "phone": "+1-555-0101",
                "email": "john@freshfoods.com",
                "address": "123 Market Street, City, State 12345"
            },
            {
                "name": "Quality Meats Co.",
                "contact_person": "Maria Garcia",
                "phone": "+1-555-0102", 
                "email": "maria@qualitymeats.com",
                "address": "456 Butcher Lane, City, State 12346"
            },
            {
                "name": "Dairy Best",
                "contact_person": "Robert Johnson",
                "phone": "+1-555-0103",
                "email": "robert@dairybest.com", 
                "address": "789 Milk Road, City, State 12347"
            }
        ]
        
        created_vendors = []
        for vendor_data in vendors_data:
            vendor = Vendor(**vendor_data)
            created_vendor = await db.create_vendor(vendor)
            created_vendors.append(created_vendor)
            print(f"✅ Created vendor: {vendor_data['name']}")
        
        # Sample Menu Items
        menu_items_data = [
            {
                "name": "Grilled Chicken Sandwich",
                "description": "Tender grilled chicken breast with fresh vegetables",
                "price": 12.99,
                "category": "Main Course",
                "vendor_id": created_vendors[1].id  # Quality Meats Co.
            },
            {
                "name": "Caesar Salad",
                "description": "Fresh romaine lettuce with Caesar dressing and croutons",
                "price": 8.99,
                "category": "Appetizers",
                "vendor_id": created_vendors[0].id  # Fresh Foods Supplier
            },
            {
                "name": "Chocolate Milkshake",
                "description": "Rich chocolate milkshake with whipped cream",
                "price": 5.99,
                "category": "Beverages",
                "vendor_id": created_vendors[2].id  # Dairy Best
            },
            {
                "name": "French Fries",
                "description": "Crispy golden french fries",
                "price": 4.99,
                "category": "Snacks",
                "vendor_id": created_vendors[0].id  # Fresh Foods Supplier
            }
        ]
        
        for item_data in menu_items_data:
            menu_item = MenuItem(**item_data)
            await db.create_menu_item(menu_item)
            print(f"✅ Created menu item: {item_data['name']}")
        
        # Sample Stock Items
        stock_items_data = [
            {
                "item_name": "Chicken Breast",
                "description": "Fresh chicken breast fillets",
                "unit": "kg",
                "current_stock": 50,
                "minimum_stock": 10,
                "maximum_stock": 100,
                "unit_cost": 8.50,
                "vendor_id": created_vendors[1].id,
                "reorder_level": 15
            },
            {
                "item_name": "Romaine Lettuce",
                "description": "Fresh romaine lettuce heads",
                "unit": "piece",
                "current_stock": 25,
                "minimum_stock": 5,
                "maximum_stock": 50,
                "unit_cost": 2.00,
                "vendor_id": created_vendors[0].id,
                "reorder_level": 10
            },
            {
                "item_name": "Whole Milk",
                "description": "Fresh whole milk",
                "unit": "liter",
                "current_stock": 30,
                "minimum_stock": 10,
                "maximum_stock": 60,
                "unit_cost": 1.50,
                "vendor_id": created_vendors[2].id,
                "reorder_level": 15
            },
            {
                "item_name": "Potatoes",
                "description": "Fresh potatoes for fries",
                "unit": "kg",
                "current_stock": 5,  # Low stock to demonstrate alerts
                "minimum_stock": 10,
                "maximum_stock": 100,
                "unit_cost": 1.20,
                "vendor_id": created_vendors[0].id,
                "reorder_level": 20
            }
        ]
        
        for stock_data in stock_items_data:
            stock = Stock(**stock_data)
            await db.create_stock_item(stock)
            status = "⚠️ LOW" if stock_data["current_stock"] <= stock_data["reorder_level"] else "✅"
            print(f"{status} Created stock item: {stock_data['item_name']} ({stock_data['current_stock']} {stock_data['unit']})")
        
        print(f"\n🎉 Sample data created successfully!")
        print(f"   • {len(created_vendors)} vendors")
        print(f"   • {len(menu_items_data)} menu items")
        print(f"   • {len(stock_items_data)} stock items")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return False

async def check_database_connection():
    """Check if we can connect to Supabase"""
    print("\n🔍 Checking Database Connection")
    print("-" * 30)
    
    try:
        db = Database()
        # Try a simple operation
        vendors = await db.get_all_vendors()
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nPlease check:")
        print("1. SUPABASE_URL is set correctly")
        print("2. SUPABASE_ANON_KEY is set correctly") 
        print("3. Supabase project is active")
        print("4. All required tables are created")
        return False

def check_environment():
    """Check if environment variables are set"""
    print("\n🌍 Checking Environment Variables")
    print("-" * 30)
    
    required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SECRET_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"✅ {var} is set")
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("\nPlease:")
        print("1. Copy env.example to .env")
        print("2. Fill in the missing values")
        return False
    
    print("✅ All required environment variables are set!")
    return True

async def main():
    """Main setup function"""
    print("🚀 Vendor Management System Setup")
    print("=" * 40)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Check database connection
    if not await check_database_connection():
        sys.exit(1)
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Create admin user only")
    print("2. Create sample data only")
    print("3. Create admin user and sample data")
    print("4. Skip setup")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        await create_admin_user()
    elif choice == "2":
        await create_sample_data()
    elif choice == "3":
        success = await create_admin_user()
        if success:
            await create_sample_data()
    elif choice == "4":
        print("Setup skipped.")
    else:
        print("Invalid choice.")
        sys.exit(1)
    
    print("\n" + "=" * 40)
    print("🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Run: python main.py")
    print("2. Open: http://localhost:8000")
    print("3. Login with your admin credentials")
    print("\nEnjoy using the Vendor Management System! 🏪")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1) 