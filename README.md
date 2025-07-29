# Vendor Management System

A comprehensive vendor management application built with FastAPI, HTML, and Supabase for local businesses to manage vendors, menu items, and stock inventory.

## Features

### 🏢 Vendor Management
- Add, edit, and manage vendor information
- Track vendor contact details and addresses
- Monitor vendor performance and relationships

### 🍽️ Menu Management
- Create and organize menu items by category
- Link menu items to specific vendors
- Track pricing and availability status
- Categorize items (Appetizers, Main Course, Desserts, etc.)

### 📦 Stock Management
- Real-time inventory tracking
- Automated low stock alerts
- Multiple unit types (kg, liter, piece, etc.)
- Reorder level management

### 📊 Stock Transactions
- Record stock in/out movements
- Track stock adjustments and corrections
- Detailed transaction history
- Cost tracking and analytics

### 📈 Reports & Analytics
- Low stock reports
- Vendor performance analytics
- Monthly transaction trends
- Key Performance Indicators (KPIs)
- Export functionality (planned)

### 🔐 Authentication & Security
- User login system with JWT tokens
- Role-based access control
- Secure password handling with bcrypt
- Session management

## Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Database**: Supabase (PostgreSQL)
- **Authentication**: JWT with bcrypt
- **Styling**: Custom CSS with modern design
- **Icons**: Font Awesome

## Installation

### Prerequisites
- Python 3.8 or higher
- Supabase account and project
- Git

### 1. Clone the Repository
```bash
git clone <repository-url>
cd vendor-management-system
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your actual values
# You'll need:
# - SUPABASE_URL: Your Supabase project URL
# - SUPABASE_ANON_KEY: Your Supabase anonymous key
# - SECRET_KEY: A secure random string for JWT signing
```

### 5. Setup Supabase Database

Create the following tables in your Supabase project:

#### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) DEFAULT 'staff',
    is_active BOOLEAN DEFAULT true,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Vendors Table
```sql
CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Menu Items Table
```sql
CREATE TABLE menu_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(50) NOT NULL,
    vendor_id INTEGER REFERENCES vendors(id),
    is_available BOOLEAN DEFAULT true,
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Stock Table
```sql
CREATE TABLE stock (
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
```

#### Stock Transactions Table
```sql
CREATE TABLE stock_transactions (
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
```

### 6. Create Initial Admin User

Run this SQL in your Supabase SQL editor to create an admin user:

```sql
INSERT INTO users (username, email, full_name, role, hashed_password)
VALUES (
    'admin',
    'admin@example.com',
    'System Administrator',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewrLm/XBkKb6Wht2'
);
-- Password is: admin123
```

### 7. Run the Application
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at: `http://localhost:8000`

## Usage

### Login
- Navigate to `http://localhost:8000`
- Use the demo credentials:
  - **Username**: admin
  - **Password**: admin123

### Dashboard
- View system overview and statistics
- Monitor low stock alerts
- Quick access to all modules

### Managing Vendors
1. Go to "Vendors" in the sidebar
2. Fill out the vendor form
3. Add contact information and address
4. Vendors will appear in the list

### Managing Menu Items
1. Navigate to "Menu Items"
2. Select a vendor and category
3. Add item details and pricing
4. Items are automatically linked to vendors

### Stock Management
1. Go to "Stock Management"
2. Add new stock items with units and reorder levels
3. Use quick buttons (+/-) for fast updates
4. Monitor stock status with color-coded indicators

### Recording Transactions
1. Visit "Stock Transactions"
2. Select stock item and transaction type
3. Enter quantities and costs
4. Add notes for record keeping

### Viewing Reports
1. Access "Reports" for analytics
2. View low stock alerts
3. Check vendor performance
4. Monitor monthly trends

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Your Supabase project URL | Yes |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Yes |
| `SECRET_KEY` | JWT signing secret | Yes |
| `DEBUG` | Enable debug mode | No |
| `HOST` | Server host | No |
| `PORT` | Server port | No |

### User Roles

- **Admin**: Full system access
- **Manager**: Vendor and stock management
- **Staff**: Limited access to view and basic operations

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## Development

### Project Structure
```
vendor-management-system/
├── main.py                 # FastAPI application
├── models.py              # Pydantic models
├── database.py            # Database operations
├── auth.py                # Authentication logic
├── requirements.txt       # Python dependencies
├── env.example           # Environment variables template
├── README.md             # Documentation
├── static/               # Static files
│   ├── css/
│   │   └── style.css     # Application styles
│   └── js/               # JavaScript files
└── templates/            # HTML templates
    ├── base.html         # Base template
    ├── login.html        # Login page
    ├── dashboard.html    # Dashboard
    ├── vendors.html      # Vendor management
    ├── menu.html         # Menu management
    ├── stock.html        # Stock management
    ├── stock_transactions.html  # Transactions
    └── reports.html      # Reports & analytics
```

### Adding New Features

1. **Models**: Add new Pydantic models in `models.py`
2. **Database**: Add CRUD operations in `database.py`
3. **Routes**: Add new endpoints in `main.py`
4. **Templates**: Create HTML templates in `templates/`
5. **Styles**: Update `static/css/style.css`

## Security Considerations

- Change default admin credentials immediately
- Use strong, unique `SECRET_KEY` in production
- Enable Supabase Row Level Security (RLS)
- Use environment variables for sensitive data
- Implement proper input validation

## Troubleshooting

### Common Issues

1. **Supabase Connection Error**
   - Verify SUPABASE_URL and SUPABASE_ANON_KEY
   - Check internet connection
   - Ensure Supabase project is active

2. **Authentication Issues**
   - Verify SECRET_KEY is set
   - Check user exists in database
   - Clear browser cookies

3. **Template Not Found**
   - Ensure templates directory exists
   - Check file names match exactly
   - Verify template inheritance

4. **Database Errors**
   - Confirm all tables are created
   - Check foreign key constraints
   - Verify data types match models

## Roadmap

### Planned Features
- [ ] Purchase order management
- [ ] Supplier integration
- [ ] Barcode scanning
- [ ] Email notifications
- [ ] Advanced reporting with charts
- [ ] Mobile app
- [ ] API for external integrations
- [ ] Backup and restore functionality

### Version History
- **v1.0.0**: Initial release with core functionality

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please create an issue on the GitHub repository or contact the development team.

## Acknowledgments

- FastAPI team for the excellent framework
- Supabase team for the backend-as-a-service platform
- Font Awesome for the icons
- All contributors and testers

---

**Note**: This is a production-ready application suitable for small to medium businesses. For enterprise use, consider additional security measures and scalability improvements. 