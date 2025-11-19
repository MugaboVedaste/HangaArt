# Sample API Requests - HangaArt

## 1. Authentication

### Register Artist
```json
POST /api/auth/register/
Content-Type: application/json

{
  "username": "picasso_art",
  "email": "picasso@example.com",
  "password": "artpass123",
  "password2": "artpass123",
  "role": "artist",
  "first_name": "Pablo",
  "last_name": "Picasso",
  "phone": "+250789123456"
}
```

### Register Buyer
```json
POST /api/auth/register/
Content-Type: application/json

{
  "username": "art_collector",
  "email": "collector@example.com",
  "password": "buypass123",
  "password2": "buypass123",
  "role": "buyer",
  "first_name": "Jane",
  "last_name": "Collector",
  "phone": "+250788654321"
}
```

### Login
```json
POST /api/auth/login/
Content-Type: application/json

{
  "username": "picasso_art",
  "password": "artpass123"
}

// Response:
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Refresh Token
```json
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "YOUR_REFRESH_TOKEN"
}
```

### Get Current User
```json
GET /api/auth/me/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Update User
```json
PATCH /api/auth/me/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "first_name": "Pablo Updated",
  "phone": "+250789999999"
}
```

### Change Password
```json
POST /api/auth/change-password/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "old_password": "artpass123",
  "new_password": "newpass456",
  "new_password2": "newpass456"
}
```

## 2. Profiles

### Update Artist Profile
```json
PATCH /api/profiles/artist/
Authorization: Bearer ARTIST_ACCESS_TOKEN
Content-Type: application/json

{
  "bio": "Award-winning contemporary artist specializing in abstract expressionism",
  "specialization": "Abstract Art",
  "experience_years": 15,
  "website": "https://picassoart.com",
  "country": "Rwanda",
  "city": "Kigali",
  "instagram": "https://instagram.com/picasso_art",
  "facebook": "https://facebook.com/picassoart"
}
```

### Update Buyer Profile
```json
PATCH /api/profiles/buyer/
Authorization: Bearer BUYER_ACCESS_TOKEN
Content-Type: application/json

{
  "address": "123 Art Street, KN 5 Ave",
  "city": "Kigali",
  "country": "Rwanda",
  "date_of_birth": "1985-03-15"
}
```

### View Public Artist Profile
```json
GET /api/profiles/artist/1/
// No authentication required
```

### List All Verified Artists
```json
GET /api/artists/
// No authentication required
```

## 3. Artworks

### Create Artwork (Artist Only)
```json
POST /api/artworks/
Authorization: Bearer ARTIST_ACCESS_TOKEN
Content-Type: application/json

{
  "title": "Sunset Over Volcanoes",
  "description": "A vibrant oil painting capturing the majestic sunset over Rwanda's volcanic mountains",
  "category": "Painting",
  "medium": "Oil on Canvas",
  "width_cm": "80.00",
  "height_cm": "60.00",
  "creation_year": 2024,
  "price": "1500.00"
}

// Note: main_image must be uploaded separately or use multipart/form-data
```

### Create Artwork with Image (Multipart)
```
POST /api/artworks/
Authorization: Bearer ARTIST_ACCESS_TOKEN
Content-Type: multipart/form-data

title: Sunset Over Volcanoes
description: A vibrant oil painting...
category: Painting
medium: Oil on Canvas
price: 1500.00
width_cm: 80.00
height_cm: 60.00
main_image: [file upload]
```

### List All Approved Artworks (Public)
```json
GET /api/artworks/
// No authentication required
// Query params: ?category=Painting&search=sunset&ordering=-price
```

### Get Artwork Details
```json
GET /api/artworks/5/
// No authentication required for approved artworks
```

### Update Artwork (Owner Only)
```json
PATCH /api/artworks/5/
Authorization: Bearer ARTIST_ACCESS_TOKEN
Content-Type: application/json

{
  "price": "1800.00",
  "description": "Updated description with more details"
}
```

### Get My Artworks (Artist Only)
```json
GET /api/artworks/my-artworks/
Authorization: Bearer ARTIST_ACCESS_TOKEN
// Returns all artworks regardless of status
```

### Submit Artwork for Review
```json
POST /api/artworks/5/submit/
Authorization: Bearer ARTIST_ACCESS_TOKEN
// Changes status from 'draft' to 'submitted'
```

### Update Artwork Status (Admin Only)
```json
PATCH /api/artworks/5/update-status/
Authorization: Bearer ADMIN_ACCESS_TOKEN
Content-Type: application/json

{
  "status": "approved",
  "admin_comment": "Excellent work! Approved for marketplace listing."
}
```

### Delete Artwork (Owner Only)
```json
DELETE /api/artworks/5/
Authorization: Bearer ARTIST_ACCESS_TOKEN
```

## 4. Orders

### Create Order (Buyer Only)
```json
POST /api/orders/
Authorization: Bearer BUYER_ACCESS_TOKEN
Content-Type: application/json

{
  "items": [
    {
      "artwork_id": 5,
      "quantity": 1
    },
    {
      "artwork_id": 8,
      "quantity": 1
    }
  ],
  "shipping_address": "123 Art Street, KN 5 Ave, Kigali, Rwanda",
  "shipping_fee": "15.00"
}

// Response includes auto-generated order_number and calculated totals
```

### List My Orders (Buyer)
```json
GET /api/orders/my-orders/
Authorization: Bearer BUYER_ACCESS_TOKEN
```

### List All Orders (Admin)
```json
GET /api/orders/
Authorization: Bearer ADMIN_ACCESS_TOKEN
// Query params: ?status=paid&payment_method=card
```

### Get Order Details
```json
GET /api/orders/12/
Authorization: Bearer BUYER_ACCESS_TOKEN
// Buyers see only their orders, admins see all
```

### Update Order Status (Admin Only)
```json
PATCH /api/orders/12/update-status/
Authorization: Bearer ADMIN_ACCESS_TOKEN
Content-Type: application/json

{
  "status": "shipped",
  "tracking_number": "DHL123456789",
  "admin_notes": "Shipped via DHL Express"
}
```

## 5. Payments

### Initiate Payment
```json
POST /api/payments/initiate/12/
Authorization: Bearer BUYER_ACCESS_TOKEN
Content-Type: application/json

{
  "payment_method": "card"
}

// Response includes transaction_id for tracking
```

### Get My Payments
```json
GET /api/payments/my-payments/
Authorization: Bearer BUYER_ACCESS_TOKEN
```

### Get Payment Details
```json
GET /api/payments/15/
Authorization: Bearer BUYER_ACCESS_TOKEN
// Includes payment logs
```

### Payment Webhook (No Auth Required)
```json
POST /api/payments/webhook/
Content-Type: application/json

{
  "transaction_id": "TXN-ABC123DEF456",
  "status": "successful",
  "amount": "1515.00",
  "provider_response": {
    "gateway": "stripe",
    "charge_id": "ch_3MmlLrKSn4Z7Lm8w0K8m3h2J"
  }
}

// This updates payment, order, and artwork statuses automatically
```

## 6. Filtering & Search Examples

### Search Artworks
```
GET /api/artworks/?search=sunset
GET /api/artworks/?category=Painting
GET /api/artworks/?medium=Oil
GET /api/artworks/?artist=5
```

### Ordering
```
GET /api/artworks/?ordering=-created_at  // Newest first
GET /api/artworks/?ordering=price        // Cheapest first
GET /api/artworks/?ordering=-price       // Most expensive first
```

### Pagination
```
GET /api/artworks/?page=2
// Default page size: 20 items
```

### Combined Filters
```
GET /api/artworks/?category=Painting&medium=Oil&ordering=-price&search=sunset
```

## 7. Error Responses

### Validation Error (400)
```json
{
  "password": ["Password fields didn't match."],
  "email": ["User with this email already exists."]
}
```

### Unauthorized (401)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Forbidden (403)
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### Not Found (404)
```json
{
  "detail": "Not found."
}
```

## 8. Testing Workflow

### Complete E2E Flow
1. Register artist → Get tokens
2. Update artist profile
3. Create artwork → Get artwork_id
4. Submit artwork for review
5. Admin approves artwork (via admin panel or API)
6. Register buyer → Get tokens
7. Buyer creates order with artwork_id
8. Initiate payment → Get transaction_id
9. Simulate webhook with transaction_id
10. Verify order status = 'paid' and artwork status = 'sold'

## Tips

- Always include `Content-Type: application/json` header
- Use `Authorization: Bearer TOKEN` for authenticated requests
- Save access tokens from login/register responses
- Use refresh token when access token expires
- Check response status codes: 200/201 = success, 400 = validation error, 401 = not authenticated, 403 = no permission
