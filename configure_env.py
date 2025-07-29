#!/usr/bin/env python3
"""
Environment Configuration Helper
This script helps you configure the .env file interactively
"""

import os
import secrets

def generate_secret_key():
    """Generate a secure random secret key"""
    return secrets.token_urlsafe(32)

def create_env_file():
    """Create .env file with user input"""
    print("🔧 Environment Configuration Helper")
    print("=" * 40)
    
    # Check if .env file exists
    if os.path.exists('.env'):
        overwrite = input("📄 .env file already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("❌ Configuration cancelled.")
            return False
    
    print("\n📝 Please provide your Supabase credentials:")
    print("   You can find these in your Supabase project dashboard")
    print("   at https://app.supabase.com/project/YOUR_PROJECT/settings/api")
    
    # Get Supabase URL
    supabase_url = input("\n🔗 Enter your Supabase URL: ").strip()
    if not supabase_url:
        print("❌ Supabase URL is required!")
        return False
    
    # Get Supabase Anon Key
    supabase_key = input("🔑 Enter your Supabase Anon Key: ").strip()
    if not supabase_key:
        print("❌ Supabase Anon Key is required!")
        return False
    
    # Generate or get secret key
    use_generated = input("\n🎲 Use auto-generated SECRET_KEY? (Y/n): ").strip().lower()
    if use_generated == 'n':
        secret_key = input("🔐 Enter your custom SECRET_KEY: ").strip()
        if not secret_key:
            print("❌ SECRET_KEY cannot be empty!")
            return False
    else:
        secret_key = generate_secret_key()
        print(f"✅ Generated SECRET_KEY: {secret_key[:20]}...")
    
    # Create .env content
    env_content = f"""# Supabase Configuration
SUPABASE_URL={supabase_url}
SUPABASE_ANON_KEY={supabase_key}

# JWT Secret Key (change this to a secure random string)
SECRET_KEY={secret_key}

# Database Configuration (if needed for additional setup)
DATABASE_URL=postgresql://username:password@localhost:5432/vendor_management

# Application Settings
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Email Configuration (for future email notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# File Upload Settings
MAX_FILE_SIZE=5242880  # 5MB in bytes
UPLOAD_DIR=uploads/
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("\n✅ .env file created successfully!")
        print("\n📋 Configuration Summary:")
        print(f"   • SUPABASE_URL: {supabase_url[:30]}...")
        print(f"   • SUPABASE_ANON_KEY: {supabase_key[:20]}...")
        print(f"   • SECRET_KEY: Generated and set")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def main():
    """Main function"""
    success = create_env_file()
    
    if success:
        print("\n🎉 Environment configured successfully!")
        print("\nNext steps:")
        print("1. Set up your Supabase database tables (see README.md)")
        print("2. Run: python setup.py")
        print("3. Start the application: python main.py")
    else:
        print("\n❌ Environment configuration failed.")
        print("Please check your inputs and try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Configuration cancelled by user.")
    except Exception as e:
        print(f"\n❌ Configuration failed: {e}") 