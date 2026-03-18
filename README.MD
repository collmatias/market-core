# 🐶 VetCore — Veterinary Management Platform

**VetCore** is a comprehensive veterinary clinic management system designed for simplicity, offline resilience, and cloud connectivity.

Built with a hybrid architecture that supports both **Desktop** (Windows .exe with local SQLite) and **SaaS** (cloud PostgreSQL multi-tenant) deployment modes.

## 🚀 Features

### Core
- **Client & Patient Management** — Full CRUD with server-side search and pagination
- **Clinical Records** — Medical history, consultations, attachments, vaccine tracking
- **Appointment Scheduling** — Calendar/agenda with drag-and-drop, appointment states
- **POS / Point of Sale** — Cart-based sales with barcode scanner (camera + USB reader)
- **Inventory** — Products & services, stock movements, restock alerts, QR label printing
- **Cash Register Reports** — Daily/shift-based cash closing with payment method breakdown

### Team & Security
- **Multi-user** — Role-based access (Veterinarian, Administrative), team management
- **Quick Switch** — PIN-based fast user switching and lockscreen
- **Admin Controls** — Employee management, password reset, activate/deactivate users

### Settings & Data
- **Company Configuration** — Name, tax ID, currency (11 currencies), language (es/en/pt)
- **Backup & Restore** — Download/upload SQLite backups with safety copies
- **Data Migration** — Import from Vetter (FoxPro) with table selection and record preview
- **Internationalization** — Spanish, English, Portuguese with per-company language setting

### Licensing
- **Offline License** — Hardware ID-based perpetual key validation
- **Online Subscription** — Cloud API verification with 3-day offline grace period
- **Hybrid** — Seamless switch between offline and online license modes

### Cloud API (`cloud_api/`)
- **Modular Architecture** — FastAPI with routers, models, and core modules
- **License Management** — Check, create, renew, revoke licenses via JWT-protected admin API
- **Auth** — JWT token-based admin authentication
- **Infrastructure** — Rate limiting, CORS, request logging, health check with DB status
- **Database Migrations** — Alembic with autogenerate support
- **Future-ready** — Release, Tenant models in place for auto-update and SaaS registration

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VetCore Platform                          │
├─────────────┬──────────────┬────────────────────────────────┤
│  Desktop    │  SaaS        │  Cloud API                     │
│  (SQLite)   │  (PostgreSQL)│  (FastAPI + PostgreSQL)         │
│  Port 8000  │  Port 8001   │  Port 5000                     │
│  Offline    │  Multi-tenant│  Licenses, Updates, AI (future) │
└─────────────┴──────────────┴────────────────────────────────┘
```

### Services (Docker Compose)

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| `api_desktop` | `vetcore_desktop` | 8000 | Django — Desktop mode (SQLite) |
| `api_saas` | `vetcore_saas` | 8001 | Django — SaaS mode (PostgreSQL) |
| `db` | `vetcore_db_saas` | 5432 | PostgreSQL for SaaS app data |
| `cloud_api` | `cloud_api_service` | 5000 | FastAPI — Cloud license/management API |
| `cloud_db` | — | 5433 | PostgreSQL for cloud API data |

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11 + Django 5.2 + DRF 3.16 |
| Cloud API | FastAPI + SQLAlchemy 2 + Alembic |
| Desktop DB | SQLite 3 |
| SaaS DB | PostgreSQL 15 |
| Frontend | Django Templates + Bootstrap 5.3 + Bootstrap Icons |
| Barcode | html5-qrcode (camera) + USB reader support |
| Auth | Session-based (Django) + JWT (Cloud API) |
| i18n | Django i18n (es/en/pt) |
| Infrastructure | Docker & Docker Compose |
| Data Import | dbfread (FoxPro .DBF files) |

## 💻 Getting Started

### Prerequisites
- Docker and Docker Compose installed

### Quick Start
```bash
# Clone the repository
git clone https://github.com/collmatias/vetcore.git
cd vetcore

# Start all services
docker compose up --build

# Or use Make
make up
```

### Access Points

| Service | URL |
|---------|-----|
| Desktop App | http://localhost:8000 |
| SaaS App | http://localhost:8001 |
| Cloud API | http://localhost:5000 |
| Cloud API Docs | http://localhost:5000/docs |
| Django Admin | http://localhost:8000/admin |

### Useful Commands
```bash
make up          # Start all services
make down        # Stop all services
make logs        # View logs in real-time
make seed        # Load demo data
make reset-db    # Full reset: drop volumes, recreate migrations, rebuild
make db          # Run makemigrations + migrate
make shell       # Django shell
make test        # Run tests
```

### Cloud API Endpoints
```
GET  /                              Health check
GET  /health                        Health + DB status
POST /check-license                 Legacy license check (backward compat)
POST /license/check                 Check license status
GET  /license/admin/list            List all licenses (JWT required)
POST /license/admin/create          Create/renew license (JWT required)
POST /license/admin/revoke/{hw_id}  Revoke license (JWT required)
POST /admin/login                   Get JWT token (exchange API_SECRET)
```

## 📁 Project Structure
```
vetcore/
├── backend/                    # Django application
│   ├── core/                   # Company, Client, Patient, Auth, Settings
│   │   ├── services/           # Vetter import service
│   │   ├── models.py           # Company, UserProfile, Client, Patient
│   │   └── views.py            # All core views + backup/restore
│   ├── clinical/               # Medical records, appointments, attachments
│   ├── inventory/              # Products, stock movements, labels
│   ├── sales/                  # POS, sales, cash reports
│   ├── templates/              # Django templates (Bootstrap 5)
│   ├── locale/                 # i18n translations (es, en, pt)
│   └── vetcore/                # Django project settings
├── cloud_api/                  # FastAPI cloud service
│   ├── core/                   # Config, auth (JWT), database, deps
│   ├── models/                 # License, Release, Tenant
│   ├── routers/                # Health, license, admin
│   └── alembic/                # Database migrations
├── docker-compose.yml          # All services orchestration
├── Makefile                    # Development shortcuts
└── ROADMAP.md                  # Project roadmap
```

## 🗺️ Roadmap

### ✅ Completed
- [x] Hybrid architecture (Desktop SQLite + SaaS PostgreSQL)
- [x] Multi-tenant with Company model
- [x] Client & Patient management with search
- [x] Clinical records, consultations, attachments
- [x] Appointment scheduling with calendar
- [x] POS with barcode scanner (camera + USB)
- [x] Inventory with stock alerts and QR labels
- [x] Cash register reports
- [x] Team management with roles and PIN lock
- [x] License system (offline + online)
- [x] Backup/restore with auto-safety copies
- [x] Vetter (FoxPro) data import with table selection
- [x] i18n support (es/en/pt)
- [x] Cloud API with modular architecture (FASE 1)
- [x] JWT admin auth + license CRUD
- [x] Alembic migrations for cloud DB

### 🚧 In Progress / Next
- [ ] Auto-update system (Release model ready)
- [ ] Master product catalog with barcode lookup
- [ ] Supplier marketplace and order management
- [ ] AI assistant (clinical diagnosis + invoice OCR)
- [ ] Offline-first sync engine
- [ ] Cloud backup (encrypted)
- [ ] SaaS registration and onboarding
- [ ] Windows .exe installer (PyInstaller + Inno Setup)

See [ROADMAP.md](ROADMAP.md) for detailed phase planning.

## 📄 License

Private Property. All rights reserved.