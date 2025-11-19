# HangaArt - Django REST Framework API for Online Art Gallery

## Project Architecture

**HangaArt** is a Django 5.2.4 REST API backend for an online art gallery connecting artists with buyers. Built with Django REST Framework (DRF) and JWT authentication, it serves a React frontend via JSON APIs.

### Core Apps & Responsibilities
- **accounts** → User management, authentication, role-based profiles (Artist/Buyer/Admin)
- **artworks** → Artist artwork submission with admin approval workflow  
- **orders** → Buyer order management and fulfillment tracking
- **Payments** → Payment processing, transaction logging, webhook handling

### API Data Flow
1. **Artist Flow**: Register → Create artwork (`draft`) → Submit for review (`submitted`) → Admin approves (`approved`) → Marketplace visible
2. **Buyer Flow**: Browse approved artworks → Create order → Initiate payment → Payment webhook confirms → Order marked `paid` → Artwork marked `sold`
3. **Payment Flow**: Order created → Payment initiated (`pending`) → Gateway webhook updates status → Order/Artwork status cascades

## Authentication & Authorization

### JWT Authentication
```python
# All secured endpoints require: Authorization: Bearer <access_token>
# Tokens obtained via: POST /api/auth/login/
# Refresh via: POST /api/auth/token/refresh/
```

### Role-Based Permissions
- **Artists**: Can only CRUD their own artworks, view their artist profile
- **Buyers**: Can create orders, view own orders/payments
- **Admins**: Full access to approve artworks, manage orders, update statuses

Key permission classes:
- `IsArtistOwnerOrReadOnly` - Artists edit own artworks only
- `IsBuyerOwnerOrAdmin` - Buyers see own orders, admins see all
- `IsPaymentOwnerOrAdmin` - Users see own payments, admins see all

## Custom User Model

**Critical**: Uses `AUTH_USER_MODEL = 'accounts.User'`. Always reference:
```python
from django.conf import settings
models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
```

User roles with separate profiles (auto-created on registration):
- `artist` → `ArtistProfile` (verified_by_admin flag, social media links)
- `buyer` → `BuyerProfile` (shipping/billing details)
- `admin` → `AdminProfile` (employee tracking)

## API Endpoints

### Authentication (`/api/auth/`)
- `POST /register/` - Register artist/buyer (returns user + JWT tokens)
- `POST /login/` - Login (returns access + refresh tokens)
- `POST /token/refresh/` - Refresh access token
- `GET/PUT/PATCH /me/` - Current user details
- `POST /change-password/` - Update password

### Profiles (`/api/profiles/`)
- `GET/PUT/PATCH /artist/` - Current user's artist profile
- `GET/PUT/PATCH /buyer/` - Current user's buyer profile
- `GET /artist/<user_id>/` - Public artist profile view

### Artists (`/api/artists/`)
- `GET /` - List all verified artists (public)

### Artworks (`/api/artworks/`)
- `GET /` - List approved artworks (public) or artist's own (authenticated)
- `POST /` - Create artwork (artists only, auto-status: `draft`)
- `GET /<id>/` - Retrieve artwork details
- `PUT/PATCH /<id>/` - Update own artwork (artist only)
- `DELETE /<id>/` - Delete own artwork (artist only)
- `GET /my-artworks/` - Artist's all artworks (any status)
- `POST /<id>/submit/` - Submit artwork for admin review
- `PATCH /<id>/update-status/` - Admin updates status + comments

### Orders (`/api/orders/`)
- `GET /` - List orders (buyers see own, admins see all)
- `POST /` - Create order (buyers only, auto-generates order number)
- `GET /<id>/` - Retrieve order details
- `GET /my-orders/` - Buyer's order history
- `PATCH /<id>/update-status/` - Admin updates order status/tracking

### Payments (`/api/payments/`)
- `GET /` - List payments (users see own, admins see all)
- `POST /initiate/<order_id>/` - Initiate payment for order
- `GET /<id>/` - Retrieve payment details
- `GET /my-payments/` - User's payment history
- `POST /webhook/` - Payment gateway webhook (no auth required)

## Key Model Patterns

### Artwork Approval Workflow
```python
STATUS_CHOICES = ["draft", "submitted", "approved", "rejected", "sold", "archived"]
# Public marketplace only shows: status='approved' AND is_available=True
```

### Auto-Generated Fields
- `Artwork.slug`: Auto-generated from `title` + `artist.id` (via `save()` override)
- `Order.order_number`: Format `HGA-{8-char-uuid}` (generated in serializer)
- `PaymentTransaction.transaction_id`: Format `TXN-{12-char-uuid}`

### Price Snapshotting
`OrderItem.price` stores artwork price at purchase time to prevent historical corruption when artwork prices update.

### Status Cascading
When payment webhook confirms success:
1. `PaymentTransaction.status` → `successful`
2. `Order.status` → `paid`
3. `Artwork.is_available` → `False` + `status` → `sold`

## Development Workflow

### Install Dependencies
```cmd
pip install djangorestframework djangorestframework-simplejwt django-cors-headers django-filter Pillow
```

### Database Operations
```cmd
cd "D:\Notes CST CS\Year 3 S1\E commerce\HangaArt\Hangart"
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### Run Server
```cmd
python manage.py runserver
# API available at: http://localhost:8000/api/
# Admin panel: http://localhost:8000/admin/
```

### Test API Endpoints
```bash
# Register artist
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"artist1","email":"artist@test.com","password":"pass123","password2":"pass123","role":"artist"}'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"artist1","password":"pass123"}'
```

## Serializer Patterns

### Read-Only Nested Objects
```python
artist = UserSerializer(read_only=True)  # Full nested object for GET
artist_id = serializers.IntegerField(write_only=True)  # Accept ID for POST/PUT
```

### Context-Aware Creation
```python
def create(self, validated_data):
    validated_data['user'] = self.context['request'].user
    return super().create(validated_data)
```

## ViewSet Custom Actions

Use `@action` decorator for non-CRUD endpoints:
```python
@action(detail=False, methods=['get'], url_path='my-artworks')
def my_artworks(self, request):
    # GET /api/artworks/my-artworks/
```

## CORS Configuration

React frontend allowed origins (in `settings.py`):
```python
CORS_ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
```

## Payment Webhook Security

**Production TODO**: Add signature verification to `PaymentWebhookView` to validate requests from payment gateway.

## Conventions

- All API responses are JSON
- Pagination enabled (20 items per page)
- Filtering via `django-filter` on list endpoints
- Timestamps: `created_at`, `updated_at` auto-managed
- Related names: `user.artist_profile`, `order.items`, `payment.logs`
- Foreign keys: `PROTECT` for artworks (preserve order history), `CASCADE` for user-owned data
