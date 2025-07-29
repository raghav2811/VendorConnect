#!/usr/bin/env python3
"""
Fix admin user password in database
This script updates the admin user with the correct password hash
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from auth import AuthService
from database import Database

async def fix_admin_password():
    """Fix the admin user password"""
    print("🔧 Fixing Admin User Password")
    print("=" * 40)
    
    try:
        # Initialize services
        auth_service = AuthService()
        db = Database()
        
        # Get the admin user
        print("👤 Looking for admin user...")
        user = await db.get_user_by_username("admin")
        
        if not user:
            print("❌ Admin user not found!")
            print("💡 Creating admin user...")
            
            # Create the user using the setup script functionality
            from models import UserCreate, UserRole
            user_create = UserCreate(
                username="admin",
                email="admin@example.com", 
                full_name="System Administrator",
                password="admin123",
                role=UserRole.ADMIN
            )
            
            new_user = await auth_service.create_user(user_create)
            print(f"✅ Created admin user: {new_user.username}")
            return
        
        # Generate correct password hash
        correct_password = "admin123"
        new_hash = auth_service.get_password_hash(correct_password)
        
        print(f"📝 Current hash: {user.hashed_password[:30]}...")
        print(f"📝 New hash:     {new_hash[:30]}...")
        
        # Test the new hash
        is_valid = auth_service.verify_password(correct_password, new_hash)
        if not is_valid:
            print("❌ ERROR: New hash verification failed!")
            return
        
        print("✅ New hash verified successfully")
        
        # Update the user in database
        print("💾 Updating password in database...")
        
        # Use Supabase client directly to update
        result = db.supabase.table("users").update({
            "hashed_password": new_hash,
            "updated_at": "now()"
        }).eq("username", "admin").execute()
        
        if result.data:
            print("✅ Password updated successfully!")
            
            # Test authentication
            print("🧪 Testing authentication...")
            auth_user = await auth_service.authenticate_user("admin", "admin123")
            if auth_user:
                print("🎉 Authentication now works!")
                print(f"   Logged in as: {auth_user.full_name}")
            else:
                print("❌ Authentication still failing")
        else:
            print("❌ Failed to update password")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function"""
    await fix_admin_password()
    
    print("\n" + "=" * 40)
    print("✅ Admin password fix completed!")
    print("\nYou can now login with:")
    print("  Username: admin")
    print("  Password: admin123")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Fix cancelled by user.")
    except Exception as e:
        print(f"\n❌ Fix failed: {e}") 