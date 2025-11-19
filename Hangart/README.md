# 📚 HangaArt API Documentation Index

Welcome to the HangaArt Django REST Framework API! This index will guide you through all available documentation.

## 🎯 Quick Start

**New to the project?** Start here:
1. 📖 [QUICKSTART.md](./QUICKSTART.md) - Step-by-step setup and testing guide
2. 📦 [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - Complete overview of what's been built

## 📘 Documentation Files

### For Developers

| File | Purpose | When to Use |
|------|---------|-------------|
| [QUICKSTART.md](./QUICKSTART.md) | Complete setup and testing workflow | First time setup, testing endpoints |
| [API_README.md](./API_README.md) | Full API reference with all endpoints | Building frontend, understanding API structure |
| [API_SAMPLES.md](./API_SAMPLES.md) | Sample requests for all endpoints | Copy-paste API testing, Postman/Insomnia setup |
| [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) | What was built and why | Understanding project architecture |
| [requirements.txt](./requirements.txt) | Python dependencies | Installing packages |

### For AI Coding Agents

| File | Purpose |
|------|---------|
| [.github/copilot-instructions.md](../.github/copilot-instructions.md) | GitHub Copilot guidelines for this codebase |

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend (Planned)                 │
│                    http://localhost:3000                     │
└──────────────────────────┬──────────────────────────────────┘
                           │ JSON API
                           │ JWT Authentication
┌──────────────────────────▼──────────────────────────────────┐
│              Django REST Framework Backend                   │
│                http://localhost:8000/api/                    │
├──────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ accounts │  │ artworks │  │  orders  │  │ Payments │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├──────────────────────────────────────────────────────────────┤
│                    SQLite Database                           │
│                  (PostgreSQL for prod)                       │
└──────────────────────────────────────────────────────────────┘
```

## 🔑 Key Concepts

### User Roles
- **Artist** 🎨 - Creates and manages artworks
- **Buyer** 🛒 - Purchases artworks
- **Admin** 👑 - Approves artworks, manages orders

### Workflow
1. **Artist** creates artwork (status: `draft`)
2. **Artist** submits for review (status: `submitted`)
3. **Admin** approves (status: `approved`) → Visible in marketplace
4. **Buyer** creates order
5. **Buyer** initiates payment
6. **Webhook** confirms payment → Order marked `paid`, artwork marked `sold`

## 📋 API Endpoint Categories

### 🔐 Authentication (9 endpoints)
- User registration (artist/buyer)
- JWT login/logout
- Token refresh
- Profile management

### 🎨 Artworks (8 endpoints)
- CRUD operations
- Submit for admin review
- Public marketplace listing
- Artist portfolio management

### 🛒 Orders (5 endpoints)
- Order creation with items
- Order tracking
- Admin order management
- Buyer order history

### 💳 Payments (5 endpoints)
- Payment initiation
- Transaction tracking
- Webhook integration
- Payment history

**Total: 27 RESTful endpoints**

## 🚀 Getting Started in 5 Minutes

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python manage.py migrate

# 3. Create admin user
python manage.py createsuperuser

# 4. Start server
python manage.py runserver

# 5. Access API
# API: http://localhost:8000/api/
# Admin: http://localhost:8000/admin/
```

## 📖 Common Tasks

### Testing the API
1. Open [API_SAMPLES.md](./API_SAMPLES.md)
2. Copy the sample requests
3. Use curl, Postman, or Insomnia
4. Follow the E2E workflow in [QUICKSTART.md](./QUICKSTART.md)

### Understanding the Code
1. Read [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) for overview
2. Check [.github/copilot-instructions.md](../.github/copilot-instructions.md) for patterns
3. Explore the code in each app's directory

### Admin Panel Usage
1. Go to http://localhost:8000/admin/
2. Login with superuser credentials
3. Manage:
   - Users and profiles
   - Artworks (bulk approve/reject)
   - Orders and tracking
   - Payment transactions

## 🔧 Technology Stack

| Technology | Purpose |
|------------|---------|
| Django 5.2.4 | Web framework |
| Django REST Framework | API framework |
| Simple JWT | Authentication |
| django-cors-headers | Frontend integration |
| django-filter | API filtering |
| Pillow | Image processing |
| SQLite | Development database |

## 📂 Project Structure

```
Hangart/
├── accounts/           # User & profile management
├── artworks/          # Artwork CRUD & approval
├── orders/            # Order processing
├── Payments/          # Payment handling
├── Hangart/           # Project settings
├── media/             # Uploaded images
├── db.sqlite3         # Database
└── manage.py          # Django CLI
```

## 🎓 Learning Resources

### For Django Beginners
- [Django Official Docs](https://docs.djangoproject.com/)
- [DRF Official Docs](https://www.django-rest-framework.org/)
- [JWT Authentication Guide](https://django-rest-framework-simplejwt.readthedocs.io/)

### For This Project
- Start with [QUICKSTART.md](./QUICKSTART.md)
- Read [API_README.md](./API_README.md) for complete reference
- Use [API_SAMPLES.md](./API_SAMPLES.md) for testing

## 🐛 Troubleshooting

### Common Issues

**Problem**: CORS errors when testing from React
- **Solution**: Verify React runs on `http://localhost:3000`

**Problem**: Token expired error
- **Solution**: Use `/api/auth/token/refresh/` endpoint

**Problem**: Permission denied
- **Solution**: Check user role matches endpoint requirements

**Problem**: Image upload fails
- **Solution**: Use `multipart/form-data` content type

See [QUICKSTART.md](./QUICKSTART.md) for more troubleshooting tips.

## 🤝 Contributing

When adding new features:
1. Follow existing patterns in `serializers.py`, `views.py`, `permissions.py`
2. Add endpoints to app's `urls.py`
3. Register models in `admin.py`
4. Update documentation files
5. Add sample requests to [API_SAMPLES.md](./API_SAMPLES.md)

## 📞 Support

- Check documentation files first
- Review error messages and status codes
- Use Django debug toolbar in development
- Check admin panel for data verification

## ✅ Deployment Checklist

Before going to production:
- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use PostgreSQL/MySQL
- [ ] Set up environment variables
- [ ] Configure cloud storage for media
- [ ] Implement webhook signature verification
- [ ] Enable HTTPS
- [ ] Update CORS origins
- [ ] Set up logging and monitoring

## 🎉 What's Next?

1. ✅ Backend API is complete
2. 🔄 Test all endpoints (use [QUICKSTART.md](./QUICKSTART.md))
3. 🔄 Build React frontend
4. 🔲 Integrate real payment gateway
5. 🔲 Deploy to production
6. 🔲 Add more features (reviews, favorites, analytics)

---

**Quick Links:**
- 📖 [Quick Start Guide](./QUICKSTART.md)
- 📚 [Complete API Reference](./API_README.md)
- 🧪 [Sample API Requests](./API_SAMPLES.md)
- 📊 [Implementation Summary](./IMPLEMENTATION_SUMMARY.md)
- 🤖 [Copilot Instructions](../.github/copilot-instructions.md)

**Happy Coding! 🚀**
