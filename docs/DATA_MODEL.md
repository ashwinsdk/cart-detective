# Data Model Specification: Cart Detective

This document defines the relational database schema implemented via SQLAlchemy 2.0. The schema is designed for SQLite by default and is fully compatible with PostgreSQL.

## 1. Entity-Relationship Overview

```
[Search] 1 --- * [Run] 1 --- * [Product]
                                   |
           +-----------------------+-----------------------+
           |                       |                       |
           v                       v                       v
       [Offer]                 [Review]                 [Video]
           |                       |                       |
           +-----------------------+-----------------------+
                                   |
                                   v
                              [Evidence]

[Product] 1 --- * [WishlistItem]
[Product] 1 --- * [Purchase]
[Setting] (Singleton configuration table)
```

## 2. Table Specifications

### searches
- `id`: String (UUIDv4), Primary Key.
- `created_at`: DateTime (UTC).
- `product_type`: String (non-nullable).
- `budget_min`: Float (nullable).
- `budget_max`: Float (nullable).
- `currency`: String(3), default 'INR'.
- `color_preferences`: JSON array of strings.
- `size_fit_gender`: String (nullable).
- `must_haves`: Text (nullable).
- `deal_breakers`: Text (nullable).
- `brands_included`: JSON array of strings.
- `brands_excluded`: JSON array of strings.
- `marketplaces`: JSON array of strings.

### runs
- `id`: String (UUIDv4), Primary Key.
- `search_id`: String (UUIDv4), Foreign Key -> searches.id.
- `status`: String (pending, running, completed, failed, cancelled).
- `current_stage`: Integer (1 to 8).
- `stage_progress`: Float (0.0 to 100.0).
- `error_message`: Text (nullable).
- `started_at`: DateTime (UTC).
- `completed_at`: DateTime (nullable).
- `logs`: JSON array of log event objects.

### products
- `id`: String (UUIDv4), Primary Key.
- `run_id`: String (UUIDv4), Foreign Key -> runs.id.
- `canonical_brand`: String.
- `canonical_model`: String.
- `title`: String.
- `description`: Text.
- `primary_category`: String.
- `specs`: JSON object of verified specifications.
- `score`: Float (0.0 to 100.0).
- `confidence`: Float (0.0 to 100.0).
- `pros`: JSON array of strings.
- `cons`: JSON array of strings.
- `verdict`: Text.
- `created_at`: DateTime (UTC).

### offers
- `id`: String (UUIDv4), Primary Key.
- `product_id`: String (UUIDv4), Foreign Key -> products.id.
- `seller_name`: String.
- `url`: Text.
- `price`: Float.
- `currency`: String(3).
- `in_stock`: Boolean.
- `color_available`: Boolean.
- `size_available`: Boolean.
- `checked_at`: DateTime (UTC).
- `status`: String (verified, stale, suspicious, unavailable).

### reviews
- `id`: String (UUIDv4), Primary Key.
- `product_id`: String (UUIDv4), Foreign Key -> products.id.
- `source`: String (amazon, flipkart, reddit, forum).
- `url`: Text.
- `author`: String.
- `rating`: Float (nullable).
- `content`: Text.
- `sentiment_score`: Float (-1.0 to 1.0).
- `is_verified_purchase`: Boolean.
- `fake_probability`: Float (0.0 to 1.0).
- `published_at`: DateTime (nullable).

### videos
- `id`: String (UUIDv4), Primary Key.
- `product_id`: String (UUIDv4), Foreign Key -> products.id.
- `youtube_video_id`: String.
- `title`: String.
- `channel_title`: String.
- `url`: Text.
- `transcript_summary`: Text.
- `is_sponsored`: Boolean.
- `view_count`: Integer.
- `published_at`: DateTime (nullable).

### evidence
- `id`: String (UUIDv4), Primary Key.
- `product_id`: String (UUIDv4), Foreign Key -> products.id.
- `claim`: Text.
- `source_url`: Text.
- `source_title`: String.
- `verification_status`: String (verified, unverified, disputed).
- `created_at`: DateTime (UTC).

### wishlist_items
- `id`: String (UUIDv4), Primary Key.
- `product_id`: String (UUIDv4), Foreign Key -> products.id.
- `notes`: Text (nullable).
- `added_at`: DateTime (UTC).

### purchases
- `id`: String (UUIDv4), Primary Key.
- `product_id`: String (UUIDv4), Foreign Key -> products.id.
- `price_paid`: Float.
- `currency`: String(3).
- `store`: String.
- `purchase_date`: Date.
- `notes`: Text (nullable).
- `created_at`: DateTime (UTC).

### settings
- `key`: String, Primary Key.
- `value`: JSON.
- `updated_at`: DateTime (UTC).
