#!/usr/bin/env python3
"""
Test login process to identify 500 error
"""

import asyncio
import requests
import time
from dotenv import load_dotenv

load_dotenv()

def test_login_flow():
    """Test the complete login flow"""
    print("🔐 Testing Login Flow")
    print("=" * 30)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Check if application is running
    print("1️⃣ Testing if application is accessible...")
    try:
        response = requests.get(f"{base_url}/login", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Login page accessible")
        else:
            print(f"   ❌ Login page error: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Cannot connect to application: {e}")
        return
    
    # Test 2: Attempt login
    print("2️⃣ Testing login submission...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        # Use a session to handle cookies
        session = requests.Session()
        
        # First get the login page to establish session
        session.get(f"{base_url}/login")
        
        # Submit login form
        response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
        print(f"   Login response status: {response.status_code}")
        
        if response.status_code == 302:
            print("   ✅ Login redirect received")
            redirect_url = response.headers.get('location', '/')
            print(f"   📍 Redirect to: {redirect_url}")
            
            # Test 3: Follow redirect to dashboard
            print("3️⃣ Testing dashboard access...")
            dashboard_response = session.get(f"{base_url}{redirect_url}")
            print(f"   Dashboard status: {dashboard_response.status_code}")
            
            if dashboard_response.status_code == 200:
                print("   ✅ Dashboard loaded successfully")
                print("   🎉 Login flow working correctly!")
            else:
                print(f"   ❌ Dashboard error: {dashboard_response.status_code}")
                print(f"   Error content: {dashboard_response.text[:200]}...")
                
        elif response.status_code == 200:
            print("   ❌ Login failed - no redirect")
            if "Invalid username or password" in response.text:
                print("   🔍 Authentication rejected")
            else:
                print("   🔍 Other login page issue")
        else:
            print(f"   ❌ Unexpected login response: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Login test failed: {e}")

def test_direct_dashboard():
    """Test direct dashboard access without login"""
    print("\n🏠 Testing Direct Dashboard Access")
    print("=" * 35)
    
    try:
        response = requests.get("http://localhost:8000/", allow_redirects=False)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ Correctly redirects unauthenticated users to login")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")

def main():
    """Main test function"""
    print("🧪 Login Flow Testing")
    print("=" * 40)
    
    # Wait for application to start
    print("⏳ Waiting for application to start...")
    time.sleep(3)
    
    test_direct_dashboard()
    test_login_flow()
    
    print("\n" + "=" * 40)
    print("🎯 Testing completed!")

if __name__ == "__main__":
    main() 