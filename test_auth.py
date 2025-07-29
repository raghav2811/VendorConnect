#!/usr/bin/env python3
"""
Test authentication functionality
This script helps debug authentication issues
"""

import asyncio
import os
from dotenv import load_dotenv
from passlib.context import CryptContext

# Load environment variables
load_dotenv()

from auth import AuthService
from database import Database

async def test_authentication():
    """Test the authentication flow"""
    print("🔐 Testing Authentication System")
    print("=" * 40)
    
    try:
        # Initialize services
        auth_service = AuthService()
        db = Database()
        
        # Test database connection
        print("📡 Testing database connection...")
        try:
            vendors = await db.get_all_vendors()
            print("✅ Database connection successful")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return
        
        # Test getting user from database
        print("\n👤 Testing user retrieval...")
        username = "admin"
        user = await db.get_user_by_username(username)
        
        if not user:
            print(f"❌ User '{username}' not found in database")
            print("💡 Make sure you've created the admin user in Supabase")
            return
        else:
            print(f"✅ User '{username}' found")
            print(f"   • ID: {user.id}")
            print(f"   • Email: {user.email}")
            print(f"   • Full Name: {user.full_name}")
            print(f"   • Role: {user.role}")
            print(f"   • Active: {user.is_active}")
            print(f"   • Password Hash: {user.hashed_password[:30]}...")
        
        # Test password verification
        print(f"\n🔑 Testing password verification...")
        test_passwords = ["admin123", "wrong_password"]
        
        for password in test_passwords:
            is_valid = auth_service.verify_password(password, user.hashed_password)
            status = "✅ VALID" if is_valid else "❌ INVALID"
            print(f"   Password '{password}': {status}")
        
        # Test full authentication flow
        print(f"\n🎯 Testing full authentication...")
        authenticated_user = await auth_service.authenticate_user("admin", "admin123")
        
        if authenticated_user:
            print("✅ Authentication successful!")
            print(f"   Authenticated as: {authenticated_user.full_name}")
            
            # Test token creation
            token = auth_service.create_access_token({"sub": str(authenticated_user.id)})
            print(f"✅ JWT token created: {token[:30]}...")
            
        else:
            print("❌ Authentication failed!")
        
        # Test with wrong password
        print(f"\n🚫 Testing with wrong password...")
        failed_auth = await auth_service.authenticate_user("admin", "wrong_password")
        if failed_auth:
            print("❌ ERROR: Wrong password should not authenticate!")
        else:
            print("✅ Correctly rejected wrong password")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

def test_password_hashing():
    """Test password hashing functions"""
    print("\n🔒 Testing Password Hashing")
    print("-" * 30)
    
    auth_service = AuthService()
    
    # Test password hashing
    test_password = "admin123"
    hashed = auth_service.get_password_hash(test_password)
    print(f"Original: {test_password}")
    print(f"Hashed: {hashed}")
    
    # Test verification
    is_valid = auth_service.verify_password(test_password, hashed)
    print(f"Verification: {'✅ PASS' if is_valid else '❌ FAIL'}")
    
    # Test with wrong password
    is_invalid = auth_service.verify_password("wrong", hashed)
    print(f"Wrong password: {'❌ INCORRECTLY PASSED' if is_invalid else '✅ CORRECTLY REJECTED'}")

async def main():
    """Main test function"""
    print("🧪 Vendor Management System - Authentication Tests")
    print("=" * 50)
    
    # Test password hashing first
    test_password_hashing()
    
    # Test full authentication
    await test_authentication()
    
    print("\n" + "=" * 50)
    print("🎉 Testing completed!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Tests cancelled by user.")
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc() 