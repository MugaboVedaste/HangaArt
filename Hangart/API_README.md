# HangaArt API - Online Art Gallery Backend

Django REST Framework API for an online art gallery connecting artists with buyers.

## Features

- 🎨 **Artist Management** - Artists can create, submit, and manage their artwork portfolios
- 🛒 **Order Processing** - Buyers can purchase artworks with order tracking
- 💳 **Payment Integration** - Multiple payment methods with webhook support
- 🔐 **JWT Authentication** - Secure token-based authentication
- 👥 **Role-Based Access** - Artist, Buyer, and Admin roles with specific permissions
- ✅ **Admin Approval Workflow** - Artworks require admin approval before marketplace listing

## Technology Stack

- Django 5.2.4
- Django REST Framework 3.14+
- Simple JWT for authentication
- SQLite (development) / PostgreSQL (production recommended)
- django-cors-headers for React frontend integration

## Installation

### 1. Clone the repository
```bash
cd HangaArt/Hangart
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create superuser (admin)
```bash
python manage.py createsuperuser
```

### 5. Run development server
```bash
python manage.py runserver
```

API will be available at: `http://localhost:8000/api/`

## API Documentation

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register/` | Register new user (artist/buyer) | No |
| POST | `/api/auth/login/` | Login and get JWT tokens | No |
| POST | `/api/auth/token/refresh/` | Refresh access token | No |
| GET | `/api/auth/me/` | Get current user details | Yes |
| PUT/PATCH | `/api/auth/me/` | Update user details | Yes |
| POST | `/api/auth/change-password/` | Change password | Yes |

### Profile Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET/PUT/PATCH | `/api/profiles/artist/` | Manage artist profile | Yes (Artist) |
| GET/PUT/PATCH | `/api/profiles/buyer/` | Manage buyer profile | Yes (Buyer) |
| GET | `/api/profiles/artist/<user_id>/` | View public artist profile | No |
| GET | `/api/artists/` | List all verified artists | No |

### Artwork Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/artworks/` | List approved artworks | No |
| POST | `/api/artworks/` | Create new artwork | Yes (Artist) |
| GET | `/api/artworks/<id>/` | Get artwork details | No |
| PUT/PATCH | `/api/artworks/<id>/` | Update artwork | Yes (Owner) |
| DELETE | `/api/artworks/<id>/` | Delete artwork | Yes (Owner) |
| GET | `/api/artworks/my-artworks/` | Get artist's artworks | Yes (Artist) |
| POST | `/api/artworks/<id>/submit/` | Submit for admin review | Yes (Owner) |
| PATCH | `/api/artworks/<id>/update-status/` | Update artwork status | Yes (Admin) |

### Order Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/orders/` | List orders | Yes |
| POST | `/api/orders/` | Create new order | Yes (Buyer) |
| GET | `/api/orders/<id>/` | Get order details | Yes (Owner/Admin) |
| GET | `/api/orders/my-orders/` | Get buyer's orders | Yes (Buyer) |
| PATCH | `/api/orders/<id>/update-status/` | Update order status | Yes (Admin) |

### Payment Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/payments/` | List payments | Yes |
| POST | `/api/payments/initiate/<order_id>/` | Initiate payment | Yes (Buyer) |
| GET | `/api/payments/<id>/` | Get payment details | Yes (Owner/Admin) |
| GET | `/api/payments/my-payments/` | Get user's payments | Yes |
| POST | `/api/payments/webhook/` | Payment gateway webhook | No |

## Authentication

All protected endpoints require JWT authentication. Include the token in request headers:

```
Authorization: Bearer <access_token>
```

### Example: Register and Login

**Register:**
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "artist1",
    "email": "artist@example.com",
    "password": "securepass123",
    "password2": "securepass123",
    "role": "artist",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "artist1",
    "password": "securepass123"
  }'
```

Response:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## User Roles

### Artist
- Create and manage artworks
- Submit artworks for admin approval
- View own artwork statistics
- Update artist profile with portfolio and social links

### Buyer
- Browse approved artworks
- Create orders
- Track order status
- Manage payment transactions
- Update buyer profile with shipping information

### Admin
- Approve/reject artwork submissions
- Manage all orders
- Update order statuses and tracking numbers
- View all payment transactions
- Verify artist accounts

## Data Models

### User (Custom)
- Extends Django's AbstractUser
- Roles: `artist`, `buyer`, `admin`
- One-to-one relationships with role-specific profiles

### Artwork
- Statuses: `draft`, `submitted`, `approved`, `rejected`, `sold`, `archived`
- Only `approved` artworks visible in public marketplace
- Auto-generated slugs for SEO-friendly URLs

### Order
- Auto-generated order numbers (format: `HGA-XXXXXXXX`)
- Status flow: `pending_payment` → `paid` → `processing` → `shipped` → `delivered`
- Includes order items with price snapshots

### Payment Transaction
- Supports: Mobile Money, Card, PayPal, Bank Transfer
- Webhook integration for payment gateway callbacks
- Transaction logging for audit trail

## Development Notes

### Media Files
Media files (artwork images, profile photos) are stored in the `media/` directory:
- Artworks: `media/artworks/images/`
- Artist profiles: `media/artists/`
- Buyer profiles: `media/buyers/`

### CORS Configuration
React frontend allowed at `http://localhost:3000`. Update `ALLOWED_ORIGINS` in `settings.py` for production.

### Payment Webhooks
The `/api/payments/webhook/` endpoint accepts payment gateway callbacks. For production, implement signature verification for security.

## Testing

Run Django tests:
```bash
python manage.py test
```

## Deployment Checklist

- [ ] Set `DEBUG = False` in production
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use PostgreSQL/MySQL instead of SQLite
- [ ] Set up environment variables for secrets
- [ ] Configure cloud storage for media files (AWS S3, Cloudinary)
- [ ] Implement payment gateway signature verification
- [ ] Set up HTTPS
- [ ] Configure production CORS origins
- [ ] Set up logging and monitoring

## License

MIT License

## Support

For issues and questions, please open a GitHub issue.
