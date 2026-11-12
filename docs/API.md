# API Specification: Cart Detective

This document details the REST API endpoints and Server-Sent Events (SSE) contracts exposed by the FastAPI backend.

## 1. Base URL and Headers

- Default local URL: `http://localhost:8000/api`
- Content-Type: `application/json`
- SSE Content-Type: `text/event-stream`

---

## 2. Endpoints

### 2.1 Search Operations

#### POST /api/searches
Initiates a new product research request and triggers a background execution run.
- **Request Body**:
```json
{
  "product_type": "riding jacket",
  "budget_min": 5000,
  "budget_max": 12000,
  "currency": "INR",
  "color_preferences": ["black", "grey"],
  "size_fit_gender": "men XL, touring fit",
  "must_haves": "CE level 2 armor for elbows and shoulders",
  "deal_breakers": "no mesh only construction",
  "brands_included": ["Rynox", "Royal Enfield", "Viaterra"],
  "brands_excluded": [],
  "marketplaces": ["amazon_in", "brand_sites"]
}
```
- **Response**: `201 Created`
```json
{
  "search_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "run_id": "4a7b5d1e-8e8e-4a6c-9c7a-5d4e3f2b1a0c",
  "status": "pending",
  "created_at": "2026-11-12T08:30:00Z"
}
```

#### GET /api/searches
Retrieves paginated search history.
- **Query Parameters**: `limit` (default 20), `offset` (default 0), `query` (search filter).
- **Response**: `200 OK`

---

### 2.2 Run Execution and Progress

#### GET /api/runs/{run_id}
Fetches current status, stage progress, and high-level execution logs.

#### GET /api/runs/{run_id}/stream
Server-Sent Events endpoint streaming real-time pipeline execution events.

**Event Types**:
- `stage_start`: Emitted when a pipeline stage starts.
```json
{"event": "stage_start", "stage": 1, "name": "Understand", "timestamp": "2026-11-12T08:30:01Z"}
```
- `stage_progress`: Periodic status update within a stage.
```json
{"event": "stage_progress", "stage": 2, "progress": 45.0, "message": "Discovered 6 candidate items"}
```
- `stage_complete`: Emitted when a stage succeeds.
```json
{"event": "stage_complete", "stage": 1, "duration_ms": 1420}
```
- `log`: Informational or warning message from workers.
```json
{"event": "log", "level": "INFO", "message": "Groq API key not found. Using Heuristic parser."}
```
- `complete`: Final event signaling run completion with shortlisted product summaries.
```json
{"event": "complete", "run_id": "4a7b5d1e-8e8e-4a6c-9c7a-5d4e3f2b1a0c", "product_count": 4}
```
- `error`: Emitted if an unrecoverable failure occurs.
```json
{"event": "error", "message": "Search run failed: upstream timeout"}
```

---

### 2.3 Product Results

#### GET /api/runs/{run_id}/products
Retrieves full shortlisted product details including offers, reviews, YouTube video summaries, and evidence citations.

#### GET /api/products/{product_id}
Fetches single product detail record.

---

### 2.4 User Collections

#### GET /api/wishlist
Lists all saved wishlist items.

#### POST /api/wishlist
Saves a product to the user wishlist.
- **Body**: `{"product_id": "uuid", "notes": "Watch for festive discounts"}`

#### DELETE /api/wishlist/{item_id}
Removes item from wishlist.

#### GET /api/purchases
Lists all recorded purchases.

#### POST /api/purchases
Records an acquired product.
- **Body**:
```json
{
  "product_id": "uuid",
  "price_paid": 9800.0,
  "currency": "INR",
  "store": "Amazon.in",
  "purchase_date": "2026-11-12",
  "notes": "Delivered with CE level 2 back protector"
}
```

---

### 2.5 Settings

#### GET /api/settings
Returns scoring weights, enabled marketplaces, and provider connectivity status.

#### PUT /api/settings
Updates scoring weight configuration.
