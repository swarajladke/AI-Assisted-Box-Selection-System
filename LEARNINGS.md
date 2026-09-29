# Project Learnings

Key takeaways, architectural insights, and practical lessons learned while designing, building, and verifying the AI-Assisted Box Selection System.

---

## 1. Domain Modeling & Algorithmic Realities

### The 3D Bin Packing Problem (3D-BPP) is NP-Hard
* **Necessary vs. Sufficient Conditions**: Checking that individual item dimensions fit (with rotation) and that total order volume is less than box volume is a *necessary* condition, but **not a sufficient condition** for items to physically fit together in 3D space.
* **The Concrete Collision Edge Case**: Two 9x9x2 cm items (combined volume: 324 cm³) easily pass the volumetric check for a 10x10x3.5 cm box (volume: 350 cm³). However, they cannot physically fit together:
  * Stacking them requires a minimum height of 4.0 cm (box is 3.5 cm).
  * Placing them side-by-side requires a minimum width of 18.0 cm (box is 10.0 cm).
* **Engineering Trade-off**: An exact 3D geometric packing solver (like Branch-and-Bound or maximal empty cuboid partitioning) can introduce high latency for orders with many items. In production fulfillment systems, a fast heuristic is appropriate for real-time web responses, provided that:
  1. The non-guarantees are explicitly documented.
  2. Warehouse packers have a UI override to flag unfulfillable boxes.
  3. A known-limitation test (`test_known_limitation_volume_heuristic_false_positive`) explicitly documents this behavior.

### Standardization of Physical Units
* Ambiguity in units (e.g., product weight labelled as "grams or kg" while box capacity had no unit) creates silent conversion bugs.
* Standardizing explicitly on metric units across the entire stack—**centimeters (cm)** for dimensions and **grams (g)** for weights—eliminated dimensional mismatch and rounding errors.

---

## 2. Django Architecture & System Design

### Decoupled Pure Domain Logic
* Isolating the recommendation algorithm in `packing/services.py` with **zero database access** made the core logic:
  * Deterministic and side-effect free.
  * Extremely fast to test (25 unit tests run in ~0.2s without database writes for pure logic tests).
  * Flexible via duck-typing: functions seamlessly accept dictionaries, dataclasses, or ORM model instances.
* The API views (`packing/views.py`) strictly handle HTTP serialization, validation, and status codes (200, 400, 404, 405), delegating domain calculations entirely to the service.

### Database Validation vs. Python Validation
* Django field validators (e.g., `MinValueValidator`, `validate_strictly_positive`) are executed only during form or serializer validation. They are bypassed by direct `Model.objects.create()` or `bulk_create()`.
* For strict data integrity in production, database-level `CheckConstraint`s should complement model field validators.

### Migration Hygiene
* In new projects, omitting the initial migration file (`0001_initial.py`) immediately breaks automated testing and CI pipelines with `no such table` errors.
* When refining model fields (such as updating `help_text` during early development), regenerating a single clean `0001_initial.py` avoids cluttering the repository with trivial alteration migrations.

### Idempotency in Seed Commands
* Developing the demo seed command (`python manage.py seed_demo`) with `update_or_create` and atomic line-item reconciliation ensures that developers and CI workflows can run the command repeatedly without duplicating records or corrupting state.

---

## 3. Working Effectively with AI Coding Agents

### Automated Code Generation Requires Critical Human Review
* The AI generated clean, working service code and UI templates, but initially:
  * Omitted the database migration file.
  * Included an unused dependency (`djangorestframework`) when standard Django `JsonResponse` was sufficient.
  * Used an abstract, mathematically invalid docstring example ("cubes of volume 4").
* Independent code reviews and test coverage audits are essential to catch missing edge cases and unneeded boilerplate.

### Guardrails and Context Interference
* Persistent agent instructions (such as a global rule restricting local command execution meant for external Kaggle environments) can inadvertently prevent an agent from executing necessary local validation tasks.
* Explicit, task-specific overrides and direct verification commands (`makemigrations --check`, running tests with captured output) are necessary to maintain accountability and confirm working software.
