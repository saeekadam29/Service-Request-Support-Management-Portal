# Service Request & Support Management Portal

A full-stack Django web application that simulates a small company's internal/customer
support system, where customers raise service tickets, support agents resolve them,
and admins oversee the whole operation.

Built as a resume-ready, fresher-appropriate project demonstrating backend development,
REST API design, database modeling, authentication/authorization, and frontend integration.

---

## Overview

Customers create service requests ("tickets"). Support agents pick them up, update their
status, and resolve them. Admins manage users, categories, and have full visibility across
the system. All actions (creation, assignment, status/priority changes, comments) are
tracked in an audit history per ticket.

## Problem Statement

Small businesses often handle customer support requests over email or spreadsheets, which
makes it hard to track ticket status, ownership, and history. This portal centralizes
service requests into a single, role-aware system with search, filtering, dashboards, and
a REST API for integration with other tools.

## Features

- **Authentication & Authorization** — registration, login, logout, session auth, hashed
  passwords, protected views, and three distinct roles (Admin, Support Agent, Customer).
- **Ticket Management (CRUD)** — create, read, update, delete tickets with category,
  priority, status, resolution notes, and full audit history.
- **Role-Based Access Control** — customers only see their own tickets; agents/admins see
  everything; only staff can change status/assignment.
- **Search & Filter** — search by title/ID, filter by status/priority/category/agent.
- **Dashboards** — role-aware stats (total, open, in progress, resolved, critical, category
  breakdown, tickets assigned to the logged-in agent).
- **Comments & Ticket History** — threaded comments and an automatic audit trail (created,
  status changed, priority changed, assigned, commented).
- **REST API** — Django REST Framework endpoints for tickets, categories, and comments with
  serializers, permissions, filtering, search, ordering, and pagination.
- **Django Admin** — configured for Users, Tickets, Categories, Comments, and History with
  list displays, filters, search, and inlines.
- **Validation & Security** — server-side validation (never relies on JS alone), CSRF
  protection, password hashing via Django's PBKDF2 hasher, environment-based secrets.
- **Automated Tests** — Django's test framework covers registration, login, ticket CRUD,
  permissions, and history logging.
- **Attractive, responsive UI** — Bootstrap 5 + a custom design system (gradient navbar,
  colour-coded status/priority badges, stat cards, comment/history timeline).

## User Roles

| Role | Capabilities |
|---|---|
| **Customer** | Create tickets, view/edit their own open tickets, comment, track status |
| **Support Agent** | View all tickets, update status/priority, get assigned tickets, add resolution notes, comment |
| **Admin** | Everything Agents can do, plus assign tickets to any agent, manage categories/users via Django Admin, full visibility |

## Tech Stack

**Backend:** Python, Django, Django REST Framework, Django ORM
**Database:** SQLite (default, zero-config) or PostgreSQL (via `.env`)
**Frontend:** Django Templates, HTML5, CSS3, JavaScript, Bootstrap 5, Bootstrap Icons
**Tools:** Git, GitHub, VS Code, Postman

## Architecture

```
Browser (Bootstrap + Django Templates)
        │  HTML forms, session cookies
        ▼
Django Views (accounts, tickets apps)  ──────► Django ORM ──────► SQLite / PostgreSQL
        │
        │  also exposes
        ▼
Django REST Framework (api app)  ◄──── JSON over HTTP ────  API clients (Postman, JS fetch)
```

- `accounts` app owns authentication and the `Profile` model (role).
- `tickets` app owns the domain model (`Category`, `Ticket`, `Comment`, `TicketHistory`)
  and the server-rendered UI (dashboard, list, CRUD, comments).
- `api` app exposes the same domain model over REST using DRF viewsets/serializers,
  reusing the same models and enforcing the same role-based rules.

## Database Design

- **User** (Django built-in) 1─1 **Profile** (`role`, `phone_number`, `department`)
- **Category** 1─* **Ticket** (`PROTECT` — a category in use can't be deleted)
- **User (customer)** 1─* **Ticket** (`CASCADE`)
- **User (agent)** 1─* **Ticket** (`SET_NULL`, nullable — a ticket keeps existing if its agent is removed)
- **Ticket** 1─* **Comment**
- **Ticket** 1─* **TicketHistory**

All relationships use Django's `ForeignKey`/`OneToOneField`, normalized to 3NF — no
repeated or derivable data is stored redundantly.

## REST API

Base path: `/api/`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/tickets/` | List tickets (paginated, filterable, searchable) — scoped by role |
| POST | `/api/tickets/` | Create a ticket |
| GET | `/api/tickets/{id}/` | Retrieve one ticket (includes comments + history) |
| PUT/PATCH | `/api/tickets/{id}/` | Update a ticket |
| DELETE | `/api/tickets/{id}/` | Delete a ticket |
| GET | `/api/categories/` | List categories |
| POST | `/api/categories/` | Create a category (Admin only) |
| GET | `/api/comments/?ticket={id}` | List comments for a ticket |
| POST | `/api/comments/` | Add a comment |

**Filtering:** `?status=OPEN&priority=HIGH&category=1&assigned_agent=3`
**Search:** `?search=login`
**Ordering:** `?ordering=-created_at`
**Pagination:** `?page=2` (10 per page)

Authentication for the API uses Django's session auth — log in via the web UI or
`/api-auth/login/`, then browse `/api/tickets/` directly (DRF's browsable API).

## Installation

### Prerequisites
- Python 3.11+
- pip
- (Optional) PostgreSQL 14+, if you want to use it instead of SQLite

### Steps

```bash
# 1. Clone / unzip the project, then enter it
cd service_portal

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and set a real SECRET_KEY

# 5. Apply database migrations
python manage.py migrate

# 6. (Optional) Load demo data — creates an admin, 2 agents, 2 customers, 5 sample tickets
python manage.py seed_data

# 7. (Optional) Create your own superuser instead
python manage.py createsuperuser

# 8. Run the development server
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** — you'll be redirected to the dashboard (or login page).

### Demo credentials (after running `seed_data`)

| Role | Username | Password |
|---|---|---|
| Admin | `admin1` | `Admin@12345` |
| Agent | `agent_riya` | `Agent@12345` |
| Agent | `agent_dev` | `Agent@12345` |
| Customer | `customer_amit` | `Customer@12345` |
| Customer | `customer_priya` | `Customer@12345` |

### Using PostgreSQL instead of SQLite

In `.env`, set:
```
USE_POSTGRES=True
POSTGRES_DB=service_portal
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```
Then run `python manage.py migrate` again against the new database.

## Running Tests

```bash
python manage.py test
```

Covers: user registration & login, ticket creation, role-based view permissions,
ticket updates, and automatic history logging. All 11 tests pass.

## Project Structure

```
service_portal/
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
│
├── config/                # Project-level settings, URLs, WSGI/ASGI
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/               # Authentication + role-aware Profile model
│   ├── models.py           # Profile (OneToOne -> User, role field)
│   ├── forms.py             # Registration, profile update
│   ├── views.py             # Login, register, logout, profile
│   ├── signals.py            # Auto-creates a Profile whenever a User is created
│   └── tests.py
│
├── tickets/                # Core domain: tickets, comments, history
│   ├── models.py            # Category, Ticket, Comment, TicketHistory
│   ├── forms.py
│   ├── views.py              # Dashboard, list/search/filter, CRUD, comments
│   ├── permissions.py         # Role-based access helpers
│   ├── signals.py              # Logs "Ticket created" automatically
│   ├── management/commands/seed_data.py   # Demo data seeder
│   └── tests.py
│
├── api/                    # Django REST Framework layer
│   ├── serializers.py
│   ├── views.py              # ViewSets with filtering/search/pagination
│   └── permissions.py
│
├── templates/               # Django templates (Bootstrap 5 UI)
│   ├── base.html
│   ├── accounts/
│   └── tickets/
│
└── static/
    ├── css/style.css        # Custom design system
    └── js/main.js
```

## Future Enhancements

- Email notifications on ticket assignment/status change
- File attachments on tickets
- SLA timers and escalation rules
- WebSocket-based live ticket updates
- Deployment to a cloud platform with PostgreSQL and static file hosting

---

*This README documents exactly what is implemented in this codebase — no unimplemented
features are claimed.*
