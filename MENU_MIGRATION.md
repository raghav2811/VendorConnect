# Menu Item Migration Guide

## Issue Fixed
- **Problem**: 'MenuItem' object has no attribute 'preparation_time'
- **Root Cause**: Database was trying to insert preparation_time field that didn't exist in models or database schema

## Changes Made

### 1. Model Updates (models.py)
- Added `preparation_time: Optional[int] = None` to `MenuItem` model
- Added `preparation_time: Optional[int] = None` to `MenuItemCreate` model  
- Added `is_available: bool = True` to `MenuItemCreate` model

### 2. Database Method Updates (database.py)
- Updated `create_menu_item()` method to handle optional fields gracefully
- Only inserts non-None values to avoid database errors
- Properly handles `image_url` and `preparation_time` optional fields

### 3. Endpoint Updates (main.py)
- Updated `/vendor/menu/add` endpoint to accept `preparation_time` parameter
- Updated `/menu` endpoint to accept `preparation_time` parameter
- Changed endpoints to use `MenuItemCreate` instead of `MenuItem` for creation
- Added `MenuItemCreate` import

### 4. Form Updates (templates/vendor_add_menu_item.html)
- Added preparation_time input field (1-120 minutes)
- Reorganized form layout to include prep time and image URL in same row
- Added helpful placeholder text and validation

### 5. Database Schema Updates (database_setup.sql)
- Added `preparation_time INTEGER` column to menu_items table
- Included migration script to add column to existing databases
- Migration is safe - checks if column exists before adding

## Customer Portal Features

The customer menu display already properly handles:
- **Preparation Time Display**: Shows preparation time with clock icon if available
- **Conditional Rendering**: Only displays prep time if it exists (no errors for null values)
- **Responsive Design**: Prep time appears alongside price in item metadata

## Database Migration Required

Run this SQL in your Supabase SQL Editor:

```sql
-- Add preparation_time column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'menu_items' 
                   AND column_name = 'preparation_time') THEN
        ALTER TABLE menu_items ADD COLUMN preparation_time INTEGER;
    END IF;
END $$;
```

## Testing

✅ **Model Creation**: MenuItemCreate objects work with preparation_time
✅ **Syntax Check**: All Python modules import successfully  
✅ **Form Layout**: Vendor can now input preparation time when adding menu items
✅ **Database Insertion**: Optional fields handled gracefully
✅ **Customer Display**: Preparation time displays correctly in buyer portal

## User Roles Supported

- **Vendors**: Can add preparation time when creating menu items
- **Buyers**: Can see preparation time when browsing vendor menus
- **Admins**: Can manage menu items with full functionality

The menu system now works seamlessly across all user roles without the preparation_time attribute error. 