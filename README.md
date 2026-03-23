# MarketNav — Phase 1

Indoor Market Navigation & Vendor Discovery System  
**QR-First MVP — Django Backend**

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Docker & Docker Compose (optional, recommended)

### 2. Local Setup (without Docker)

```bash
# Clone and enter the project
cd marketnav

# Create and activate virtualenv
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set SECRET_KEY, DB credentials, etc.

# Create database (in psql)
# CREATE DATABASE marketnav;
# CREATE USER marketnav_user WITH PASSWORD 'marketnav_pass';
# GRANT ALL PRIVILEGES ON DATABASE marketnav TO marketnav_user;

# Run migrations
python manage.py migrate

# Load sample data
python manage.py loaddata fixtures/sample_data.json

# Create admin user
python manage.py createsuperuser

# Start dev server
python manage.py runserver
```

Admin panel: http://localhost:8000/admin/

### 3. Docker Setup

```bash
cp .env.example .env
# Edit .env as needed

docker-compose up --build

# In another terminal, load sample data:
docker-compose exec web python manage.py loaddata fixtures/sample_data.json
docker-compose exec web python manage.py createsuperuser
```

---

## Project Structure

```
marketnav/
├── config/
│   ├── settings.py         # Django settings (env-driven)
│   ├── urls.py             # Root URL config
│   └── wsgi.py
├── apps/
│   ├── markets/            # Market, Zone, Node, Edge models + admin + API
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── api_urls.py
│   │   └── urls.py
│   ├── vendors/            # Vendor, Product, ProductCategory models + admin + API
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── api_urls.py
│   └── navigation/         # Routing engine + search API
│       ├── routing.py      # A* pathfinding engine (no dependencies)
│       ├── views.py
│       └── api_urls.py
├── fixtures/
│   └── sample_data.json    # Balogun Market seed data
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Data Models

### Market
Top-level container for a physical market.  
Fields: `name`, `slug`, `city`, `state`, `address`, `description`, `map_image`, `map_width`, `map_height`, `is_active`

### Zone
A named section or aisle within a market.  
Fields: `market`, `name`, `code`, `color_hex`, `description`

### Node
A single point on the navigation graph (stall, junction, entrance, etc.).  
Fields: `market`, `zone`, `qr_id` (UUID, auto), `label`, `node_type`, `x`, `y`, `qr_image`, `is_active`  
Types: `stall`, `intersection`, `entrance`, `exit`, `amenity`

### Edge
A walkable path between two Nodes.  
Fields: `market`, `node_from`, `node_to`, `weight` (metres), `is_active`  
Edges are treated as **undirected** by the routing engine.

### Vendor
A trader assigned to a Node stall.  
Fields: `market`, `node` (OneToOne), `business_name`, `owner_name`, `phone`, `whatsapp`, `email`, `categories`, `products`

### ProductCategory
Lookup table for what vendors sell.  
Examples: Fabrics & Textiles, Electronics, Foodstuffs

### Product
An item listed by a vendor (optional in MVP).  
Fields: `vendor`, `category`, `name`, `price`, `is_available`

---

## API Endpoints

All endpoints return JSON.

### Markets

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/markets/` | List all active markets |
| GET | `/api/v1/markets/<slug>/` | Market detail with zones, nodes, edges |
| GET | `/api/v1/markets/<slug>/nodes/` | All active nodes for a market |
| GET | `/scan/<uuid:qr_id>/` | Resolve QR scan → current node + market |

### Vendors

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/vendors/` | List vendors (`?search=`, `?market=`, `?category=`) |
| GET | `/api/v1/vendors/<id>/` | Vendor detail with full product list |
| GET | `/api/v1/vendors/categories/` | List all product categories |

### Navigation

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/v1/navigation/route/` | Compute A* route between two nodes |
| GET | `/api/v1/navigation/search/?market=<slug>&q=<query>` | Search vendors/products |

#### Route Request Example

```http
POST /api/v1/navigation/route/
Content-Type: application/json

{
  "market_slug": "balogun-market-lagos",
  "from_node_id": 1,
  "to_node_id": 6
}
```

#### Route Response Example

```json
{
  "found": true,
  "distance": 50.0,
  "path": [1, 2, 7, 6],
  "node_labels": ["Main Entrance", "Junction A", "Junction B", "Stall G-01"],
  "steps": [
    "Head north 15m toward Junction A",
    "Continue straight 20m north toward Junction B",
    "Continue straight 15m north — arrive at Stall G-01"
  ]
}
```

#### Search Example

```http
GET /api/v1/navigation/search/?market=balogun-market-lagos&q=ankara
```

---

## Admin Panel

Visit `/admin/` after creating a superuser.

**Key admin features:**
- **Markets** — create markets, upload map images, set coordinate space
- **Zones** — add coloured sections with short codes
- **Nodes** — place nodes with x/y coordinates, set type; inline path editor
- **Edges** — define walkable paths between nodes
- **Generate QR Codes** — select nodes → Actions → "Generate QR codes for selected nodes"
- **Vendors** — assign vendors to nodes, manage categories and products
- **Products** — manage individual product listings per vendor

---

## Routing Engine

The `MarketGraph` class in `apps/navigation/routing.py` implements:

- **Graph construction** from Node/Edge DB records (in-memory)
- **A\* pathfinding** with Euclidean heuristic on map coordinates
- **Undirected edges** (A→B and B→A both traversable)
- **Step-by-step directions** with compass bearings and zone transitions
- **Zero external dependencies** — pure Python stdlib

To use programmatically:

```python
from apps.markets.models import Market
from apps.navigation.routing import MarketGraph

market = Market.objects.get(slug="balogun-market-lagos")
graph = MarketGraph(market)
result = graph.route(from_node_id=1, to_node_id=6)
print(result["steps"])
```

---

## Phase Roadmap

| Phase | Status | Focus |
|-------|--------|-------|
| **1** | ✅ Complete | Backend, models, admin, routing engine, DRF API |
| 2 | Planned | QR scan web pages, SVG map overlay, visitor UI |
| 3 | Planned | Vendor self-service login, product catalog, pilot |
| 4 | Planned | Analytics, inventory, ecommerce |
