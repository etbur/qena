# 🇪🇹 Qenagebeya — Ethiopia's Multi-Vendor E-Commerce Platform

A full-stack multi-vendor marketplace built with **Django 5** + **Flutter**, featuring:

## Features
- 🛒 Multi-vendor marketplace (Customers, Vendors, Agents, Admin)
- 📱 Flutter mobile app with REST API (JWT auth)
- 🔴 Real-time Live Streaming (WebSocket + WebRTC)
- 🌐 White-label vendor storefronts (subdomain + custom domain)
- 🔧 Makerspace (3D Print, Laser, CNC orders)
- 📦 Full inventory management (warehouses, suppliers, POs)
- 💬 Real-time live chat
- 🌍 3-language support: English, አማርኛ, Afaan Oromoo
- 💳 Ethiopian payment methods: TeleBirr, CBE Birr, Amole

## Tech Stack
| Layer | Technology |
|---|---|
| Backend | Django 5.2, Django REST Framework, Django Channels |
| Database | SQLite (dev) |
| Auth | JWT (SimpleJWT) |
| WebSocket | Daphne ASGI + Django Channels |
| Mobile | Flutter 3 (Android + iOS) |
| State | Provider |

## Quick Start

### Backend
```bash
pip install -r requirements.txt
python manage.py migrate
python -m daphne -b 0.0.0.0 -p 8000 qenagebeya.asgi:application
```

### API
Base URL: `http://localhost:8000/api/v1/`

| Endpoint | Method | Description |
|---|---|---|
| `/auth/login/` | POST | Login → JWT tokens |
| `/auth/register/` | POST | Register new user |
| `/home/` | GET | Home screen data |
| `/products/` | GET | Product list (filterable) |
| `/products/<id>/` | GET | Product detail |
| `/categories/` | GET | All categories |
| `/vendors/` | GET | All vendors |
| `/orders/` | GET | My orders |
| `/orders/place/` | POST | Place order |
| `/live/` | GET | Live streams |
| `/search/?q=...` | GET | Search products + vendors |

### Flutter App
```bash
cd qena_app
flutter pub get
flutter run
```

### Vendor Storefronts
Add to Windows hosts file:
```
127.0.0.1  ahmed-tech-store.localhost
127.0.0.1  mariam-home-decor.localhost
```
Then visit: `http://ahmed-tech-store.localhost:8000/`

## Accounts (Dev)
| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@1234` |
| Vendor | `ahmed_store` | `Vendor@1234` |
| Agent | `omar_agent` | `Agent@1234` |
| Customer | `customer1` | `Customer@1234` |

## License
MIT — Made with ❤️ for Ethiopia 🇪🇹
