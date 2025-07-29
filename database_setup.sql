-- Vendor Management System Database Setup
-- Run this SQL in your Supabase SQL Editor

-- Migration: Add preparation_time column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'menu_items' 
                   AND column_name = 'preparation_time') THEN
        ALTER TABLE menu_items ADD COLUMN preparation_time INTEGER;
    END IF;
END $$;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) DEFAULT 'buyer',
    vendor_id INTEGER,
    is_active BOOLEAN DEFAULT true,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Vendors Table
CREATE TABLE IF NOT EXISTS vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    business_type VARCHAR(50) DEFAULT 'Restaurant',
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    is_approved BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Menu Items Table
CREATE TABLE IF NOT EXISTS menu_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(50) NOT NULL,
    vendor_id INTEGER REFERENCES vendors(id),
    is_available BOOLEAN DEFAULT true,
    image_url TEXT,
    preparation_time INTEGER, -- in minutes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Orders Table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    vendor_id INTEGER REFERENCES vendors(id),
    buyer_id INTEGER REFERENCES users(id),
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivery_date TIMESTAMP,
    delivery_address TEXT,
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Order Items Table
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    menu_item_id INTEGER REFERENCES menu_items(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Stock Table
CREATE TABLE IF NOT EXISTS stock (
    id SERIAL PRIMARY KEY,
    item_name VARCHAR(100) NOT NULL,
    description TEXT,
    unit VARCHAR(20) NOT NULL,
    current_stock INTEGER DEFAULT 0,
    minimum_stock INTEGER DEFAULT 10,
    maximum_stock INTEGER DEFAULT 1000,
    unit_cost DECIMAL(10,2) DEFAULT 0,
    vendor_id INTEGER REFERENCES vendors(id),
    reorder_level INTEGER DEFAULT 20,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Stock Transactions Table
CREATE TABLE IF NOT EXISTS stock_transactions (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stock(id),
    transaction_type VARCHAR(20) NOT NULL, -- 'in', 'out', 'adjustment'
    quantity INTEGER NOT NULL,
    unit_cost DECIMAL(10,2) DEFAULT 0,
    total_cost DECIMAL(10,2),
    reference_number VARCHAR(50),
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Create Default Admin User (password: admin123)
INSERT INTO users (username, email, full_name, role, hashed_password)
VALUES (
    'admin',
    'admin@example.com',
    'System Administrator',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewrLm/XBkKb6Wht2'
) ON CONFLICT (username) DO NOTHING;

-- 7. Create foreign key constraints
ALTER TABLE users ADD CONSTRAINT fk_users_vendor FOREIGN KEY (vendor_id) REFERENCES vendors(id);

-- 8. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_vendors_name ON vendors(name);
CREATE INDEX IF NOT EXISTS idx_vendors_approved ON vendors(is_approved);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_vendor ON users(vendor_id);
CREATE INDEX IF NOT EXISTS idx_menu_items_vendor ON menu_items(vendor_id);
CREATE INDEX IF NOT EXISTS idx_menu_items_category ON menu_items(category);
CREATE INDEX IF NOT EXISTS idx_stock_vendor ON stock(vendor_id);
CREATE INDEX IF NOT EXISTS idx_stock_transactions_stock ON stock_transactions(stock_id);
CREATE INDEX IF NOT EXISTS idx_stock_transactions_created_by ON stock_transactions(created_by);
CREATE INDEX IF NOT EXISTS idx_stock_transactions_date ON stock_transactions(created_at);

-- Order-related indexes
CREATE INDEX IF NOT EXISTS idx_orders_vendor_id ON orders(vendor_id);
CREATE INDEX IF NOT EXISTS idx_orders_buyer_id ON orders(buyer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_menu_item_id ON order_items(menu_item_id);

-- 9. Enable Row Level Security (optional but recommended)
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE vendors ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE menu_items ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE stock ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE stock_transactions ENABLE ROW LEVEL SECURITY;

-- Done! Your database is ready for the Vendor Management System with Order Management 