#!/usr/bin/env python3
"""
Fix authentication issues in main.py
This script updates all routes to use cookie-based authentication
"""

import re

def fix_main_py():
    """Fix authentication in main.py"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Fix all routes that use user: User = Depends(require_auth)
    patterns_to_fix = [
        # Pattern 1: Routes with user dependency
        (r'(async def \w+\([^)]*), user: User = Depends\(require_auth\)\):', r'\1):'),
        # Pattern 2: Routes with get_current_user dependency  
        (r'(async def \w+\([^)]*), user: User = Depends\(get_current_user\)\):', r'\1):'),
    ]
    
    for pattern, replacement in patterns_to_fix:
        content = re.sub(pattern, replacement, content)
    
    # Add user = await require_auth(request) at the beginning of protected routes
    protected_routes = [
        'menu_page', 'create_menu_item', 'stock_page', 'create_stock_item',
        'stock_transactions_page', 'create_stock_transaction', 'reports_page'
    ]
    
    for route in protected_routes:
        # Find the function and add authentication
        pattern = f'(async def {route}\\([^\\)]*\\):\\s*\\n)'
        replacement = f'\\1    user = await require_auth(request)\n'
        content = re.sub(pattern, replacement, content)
    
    with open('main.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed authentication in main.py")

if __name__ == "__main__":
    fix_main_py() 