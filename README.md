# AI-Assisted Box Selection System

A modular Django system that recommends the cheapest suitable shipping box for ecommerce orders using physical dimension rotation, weight, and volumetric constraints. Includes a pure Python packing service, a REST API endpoint, and a real-time warehouse packing station UI.

---

## 1. Setup & Installation

### Prerequisites
- Python 3.10+
- `pip` and `virtualenv`

### Clone and Initialize Environment
```bash
# Clone the repository
git clone <repo-url>
cd "AI Assisted Box Selection System"

# Create and activate virtual environment
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 2. How to Run

### 1. Apply Database Migrations
```bash
python manage.py makemigrations packing
python manage.py migrate
```

### 2. Create Superuser (for Django Admin)
```bash
python manage.py createsuperuser
```

### 3. Start Development Server
```bash
python manage.py runserver
```

### 4. Access the Application
* **Warehouse Packing Station UI**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Django Admin**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
* **Recommendation REST API**: `POST http://127.0.0.1:8000/api/orders/<id>/recommend-box/`

---

## 3. How to Run Tests

Tests run automatically on every push via **GitHub Actions** (`.github/workflows/django-tests.yml`).

To run the test suite locally or on remote execution environments (e.g., Kaggle / CI):
```bash
python manage.py test packing --verbosity=2
```

---

## 4. Key Design Decisions

1. **Decoupled Pure Domain Logic (`packing/services.py`)**:
   * The core box evaluation algorithm (`select_best_box`) has **zero database dependencies**.
   * Accepts plain Python dictionaries, dataclasses, or ORM model instances via duck typing.
   * Can be executed inside Celery workers, AWS Lambda, or unit tests without initializing a database.

2. **Orthogonal Item Rotation**:
   * Cardboard boxes and items can be oriented in 3D space.
   * Both item dimensions `(length, width, height)` and box internal dimensions are sorted in ascending order `(min, mid, max)`.
   * An individual item fits if and only if:
     $$\text{item.min} \le \text{box.min} \quad\land\quad \text{item.mid} \le \text{box.mid} \quad\land\quad \text{item.max} \le \text{box.max}$$

3. **Deterministic Selection & Tie-Breaking**:
   * Candidate boxes that satisfy dimension, weight, and volume constraints are sorted by:
     1. **Cost (Ascending)**: Picks the cheapest packaging option.
     2. **Inner Volume (Ascending)**: Minimizes void fill, dunnage, and carrier dimensional weight (DIM weight) penalties.
     3. **Name (Alphabetical)**: Guarantees deterministic, reproducible results across warehouse shifts.

4. **Auditability & Explainable Rejections**:
   * The service returns not only the recommended box, but also a structured list of `rejected_boxes` with specific failure reasons (e.g., exact item dimension overflow, weight capacity exceeded, or volume deficit).

---

## 5. Algorithm Limits & Theoretical Constraints

> [!WARNING]
> **Important Physical & Mathematical Non-Guarantees**

1. **3D Bin Packing Problem (3D-BPP) is NP-Hard**:
   * This algorithm uses a fast heuristic combining **single-item bounding clearance** with **aggregate volume and weight constraints**.
   * **False Positives**: Passing aggregate volume and individual dimension checks is a *necessary* condition, but **not a sufficient condition** for multiple items to fit simultaneously in 3D space.
   * *Example*: Two items of $9 \times 9 \times 2\text{ cm}$ (total volume $324\text{ cm}^3$) will pass all checks for a $10 \times 10 \times 3.5\text{ cm}$ box (volume $350\text{ cm}^3$). However, they cannot physically fit together because stacking them requires $4.0\text{ cm}$ height, and side-by-side placement requires $18.0\text{ cm}$ width.
2. **Zero-Margin Tolerance**:
   * Does not currently subtract dunnage (bubble wrap, kraft paper) or corrugated wall flex allowances. Real-world fulfillment should apply a $5\text{–}10\%$ buffer.
3. **Weight Distribution & Crushing**:
   * Assumes rigid rectangular cuboids. Does not account for center of gravity, liquid orientation (`must_stay_upright`), or fragile items being crushed beneath heavy items.

---

## 6. Example API Requests and Responses

### Endpoint
`POST /api/orders/<id>/recommend-box/`

---

### Example 1: Successful Recommendation (`200 OK`)

#### Request:
```bash
curl -X POST http://127.0.0.1:8000/api/orders/1/recommend-box/ \
     -H "Content-Type: application/json"
```

#### Response:
```json
{
  "status": "success",
  "order": {
    "id": 1,
    "order_number": "ORD-1001",
    "total_items": 3,
    "total_weight": 1450.0,
    "total_volume": 4200.0
  },
  "has_recommendation": true,
  "recommended_box": {
    "id": 2,
    "name": "Medium Parcel Box",
    "cost": 1.75,
    "inner_length": 25.0,
    "inner_width": 20.0,
    "inner_height": 10.0,
    "inner_volume": 5000.0,
    "max_weight": 3000.0
  },
  "reason": "Selected 'Medium Parcel Box' as the cheapest suitable box (Cost: $1.75, Volume: 5000.00 cm³).",
  "rejected_boxes": [
    {
      "id": 1,
      "name": "Small Pouch",
      "cost": 0.85,
      "reason": "Item 'Desk Lamp' with dimensions 15.0x20.0x25.0 cm exceeds box dimensions 5.0x10.0x15.0 cm."
    },
    {
      "id": 3,
      "name": "Heavy Duty Crate",
      "cost": 4.50,
      "reason": "Total order volume (4200.00 cm³) exceeds box inner volume (3200.00 cm³)."
    }
  ]
}
```

---

### Example 2: Order Not Found (`404 Not Found`)

#### Request:
```bash
curl -X POST http://127.0.0.1:8000/api/orders/99999/recommend-box/ \
     -H "Content-Type: application/json"
```

#### Response:
```json
{
  "error": "Order with ID 99999 not found."
}
```

---

### Example 3: Empty Order Line Items (`400 Bad Request`)

#### Request:
```bash
curl -X POST http://127.0.0.1:8000/api/orders/42/recommend-box/ \
     -H "Content-Type: application/json"
```

#### Response:
```json
{
  "error": "Order #ORD-EMPTY-01 has no items to pack.",
  "order_id": 42,
  "order_number": "ORD-EMPTY-01"
}
```

---

### Example 4: Disallowed HTTP Method (`405 Method Not Allowed`)

#### Request:
```bash
curl -X GET http://127.0.0.1:8000/api/orders/1/recommend-box/
```

#### Response:
```json
{
  "error": "Method GET not allowed. Use POST."
}
```
