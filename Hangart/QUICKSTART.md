# Quick Start Guide - HangaArt API

## Installation & Setup

### 1. Install Dependencies
```bash
cd "D:\Notes CST CS\Year 3 S1\E commerce\HangaArt\Hangart"
pip install -r requirements.txt
```

### 2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Admin User
```bash
python manage.py createsuperuser
# Follow prompts to create admin account
```

### 4. Start Server
```bash
python manage.py runserver
```

Server running at: http://localhost:8000

## Quick API Test Flow

### Step 1: Register an Artist
```bash
curl -X POST http://localhost:8000/api/auth/register/ ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"artist1\",\"email\":\"artist@test.com\",\"password\":\"test123\",\"password2\":\"test123\",\"role\":\"artist\",\"first_name\":\"John\",\"last_name\":\"Artist\"}"
```

### Step 2: Login as Artist
```bash
curl -X POST http://localhost:8000/api/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"artist1\",\"password\":\"test123\"}"
```

**Save the `access` token from response!**

### Step 3: Create an Artwork (Artist)
Replace `YOUR_ACCESS_TOKEN` with the token from Step 2:

```bash
curl -X POST http://localhost:8000/api/artworks/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" ^
  -d "{\"title\":\"Sunset Painting\",\"description\":\"Beautiful sunset\",\"category\":\"Painting\",\"medium\":\"Oil\",\"price\":\"500.00\",\"width_cm\":\"50\",\"height_cm\":\"70\"}"
```

**Note:** You'll need to add `main_image` via admin panel or multipart form data.

### Step 4: Submit Artwork for Review
Replace `ARTWORK_ID` with ID from Step 3:

```bash
curl -X POST http://localhost:8000/api/artworks/ARTWORK_ID/submit/ ^
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Step 5: Approve Artwork (Admin)
1. Go to http://localhost:8000/admin/
2. Login with superuser credentials
3. Navigate to Artworks → Select artwork → Change status to "approved" → Save

OR use admin bulk action:
- Select the artwork
- Choose "Approve selected artworks" from Actions dropdown
- Click Go

### Step 6: Register a Buyer
```bash
curl -X POST http://localhost:8000/api/auth/register/ ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"buyer1\",\"email\":\"buyer@test.com\",\"password\":\"test123\",\"password2\":\"test123\",\"role\":\"buyer\",\"first_name\":\"Jane\",\"last_name\":\"Buyer\"}"
```

### Step 7: Login as Buyer
```bash
curl -X POST http://localhost:8000/api/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"buyer1\",\"password\":\"test123\"}"
```

**Save the new `access` token!**

### Step 8: Browse Artworks (Public)
```bash
curl http://localhost:8000/api/artworks/
```

### Step 9: Create an Order (Buyer)
Replace `BUYER_ACCESS_TOKEN` and `ARTWORK_ID`:

```bash
curl -X POST http://localhost:8000/api/orders/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer BUYER_ACCESS_TOKEN" ^
  -d "{\"items\":[{\"artwork_id\":ARTWORK_ID,\"quantity\":1}],\"shipping_address\":\"123 Main St, City\",\"shipping_fee\":\"10.00\"}"
```

### Step 10: Initiate Payment
Replace `ORDER_ID` from Step 9:

```bash
curl -X POST http://localhost:8000/api/payments/initiate/ORDER_ID/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer BUYER_ACCESS_TOKEN" ^
  -d "{\"payment_method\":\"card\"}"
```

### Step 11: Simulate Payment Webhook
Replace `TRANSACTION_ID` from Step 10:

```bash
curl -X POST http://localhost:8000/api/payments/webhook/ ^
  -H "Content-Type: application/json" ^
  -d "{\"transaction_id\":\"TRANSACTION_ID\",\"status\":\"successful\"}"
```

This will:
- Mark payment as successful
- Update order status to "paid"
- Mark artwork as sold

## Testing with Postman/Insomnia

Import these endpoints:

### Base URL
```
http://localhost:8000/api
```

### Collections

**Authentication**
- POST `/auth/register/` - Register
- POST `/auth/login/` - Login
- POST `/auth/token/refresh/` - Refresh token
- GET `/auth/me/` - Get current user

**Artworks**
- GET `/artworks/` - List artworks
- POST `/artworks/` - Create artwork (Auth: Artist)
- GET `/artworks/{id}/` - Get artwork
- PUT `/artworks/{id}/` - Update artwork (Auth: Owner)
- POST `/artworks/{id}/submit/` - Submit for review (Auth: Owner)
- GET `/artworks/my-artworks/` - My artworks (Auth: Artist)

**Orders**
- GET `/orders/` - List orders (Auth: Buyer/Admin)
- POST `/orders/` - Create order (Auth: Buyer)
- GET `/orders/my-orders/` - My orders (Auth: Buyer)

**Payments**
- POST `/payments/initiate/{order_id}/` - Initiate payment (Auth: Buyer)
- GET `/payments/my-payments/` - My payments (Auth: User)
- POST `/payments/webhook/` - Payment webhook (No auth)

## Admin Panel Features

Access at: http://localhost:8000/admin/

### Users Management
- View all users with roles
- Verify artist accounts (set `verified_by_admin = True`)

### Artworks Management
- Bulk approve/reject artworks
- Add admin comments
- View artwork details and images

### Orders Management
- View all orders with items
- Update order status
- Add tracking numbers
- View buyer information

### Payments Management
- View all transactions
- See payment logs
- Update payment status manually

## Common Issues

### 1. CORS Errors
Ensure React frontend is running on `http://localhost:3000`

### 2. Token Expired
Refresh token using `/api/auth/token/refresh/`

### 3. Permission Denied
Check user role matches endpoint requirements

### 4. Image Upload Issues
Use multipart/form-data for file uploads:
```bash
curl -X POST http://localhost:8000/api/artworks/ ^
  -H "Authorization: Bearer TOKEN" ^
  -F "title=Test Artwork" ^
  -F "description=Test" ^
  -F "category=Painting" ^
  -F "price=100" ^
  -F "main_image=@C:\path\to\image.jpg"
```

## Next Steps

1. ✅ Test all API endpoints
2. ✅ Verify role-based permissions
3. ✅ Test payment webhook flow
4. 🔲 Connect React frontend
5. 🔲 Configure production settings
6. 🔲 Set up cloud storage for images
7. 🔲 Integrate real payment gateway

## Useful Commands

```bash
# Run development server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test

# Open Django shell
python manage.py shell
```
