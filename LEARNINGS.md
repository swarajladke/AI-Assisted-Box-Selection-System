# What We Learned

Building this box selection system was a great exercise in balancing algorithmic theory, practical framework quirks, and the reality of working with an AI coding partner. Here are the main lessons from the project.

---

## 1. 3D Packing: The Math vs. The Warehouse

### Volume checks are a sanity check, not a guarantee
When you first think about box selection, checking whether the total volume of the items fits inside the box feels intuitive. But 3D bin packing is NP-hard for a reason. Volume and single-item clearance are *necessary* conditions, but they are nowhere near *sufficient*.

The clearest example is putting two flat items (9×9×2 cm each, total volume 324 cm³) into a 10×10×3.5 cm box (volume 350 cm³):
* Each item fits into the box by itself.
* The total item volume (324 cm³) easily fits inside the box (350 cm³).
* Yet they cannot physically both fit: stacking them needs 4 cm of height (the box only has 3.5 cm), and placing them side by side needs 18 cm of width (the box only has 10 cm).

### Fast heuristics beat complex solvers for web requests
In an ideal world, you'd run an exact 3D geometric packing solver. In the real world, customers and warehouse workers shouldn't wait 10 seconds for an exact branch-and-bound solver to chew through 30 order items. A fast greedy heuristic that checks individual rotated dimensions, total weight, and total volume works for the vast majority of orders. The key is being honest about the edge cases: document the limitation, write a test for it (`test_known_limitation_volume_heuristic_false_positive`), and give warehouse staff a button to override or report an impossible fit.

### Units must be nailed down immediately
We started with product weights labelled as "grams or kg" and boxes with no weight unit at all. That kind of ambiguity is a recipe for silent bugs where an item weighing 5 kg gets treated as 5 grams. Standardizing everything on grams and centimeters across models, docstrings, and tests right away made calculations predictable and eliminated unit conversion surprises.

---

## 2. Django Architecture & Patterns

### Keep core logic out of the database
The best decision in the codebase was putting `select_best_box` into `packing/services.py` as a pure Python function. It doesn't query the database, doesn't import models, and accepts dictionaries or plain objects via duck typing.
* **Speed:** 25 tests run in 0.16 seconds because the service tests don't touch SQLite.
* **Testability:** Setting up edge-case tests takes 5 lines of plain dictionary data rather than creating and cleaning up database rows.
* **Reusability:** The exact same function can be called from a Django view, a Celery task, or a standalone CLI script.

### Django model validators don't run on `create()`
A classic Django gotcha: `validators=[validate_strictly_positive]` looks great in `models.py`, but Django only runs field validators during `ModelForm` or `full_clean()`. Calling `Product.objects.create(length=-5)` happily writes bad data straight to the database. For real production guarantees, database `CheckConstraint`s are required.

### Always commit the initial migration
Leaving migrations uncommitted or assuming Django will "just figure it out" breaks fresh environments and CI pipelines immediately (`no such table: packing_product`). Having `0001_initial.py` checked into Git from day one is non-negotiable.

### Make seed scripts idempotent
Writing `seed_demo` with `update_or_create` and cleaning up line items atomically meant we could run it once, twice, or ten times in development or CI without piling up duplicate boxes and corrupted test orders.

---

## 3. Practical AI Collaboration

### AI writes clean code fast, but misses context
The AI produced clean pure-service logic, sensible models, and a sleek warehouse UI in minutes. But it also:
* Forgot to generate migration files.
* Pulled in `djangorestframework` when a simple native `JsonResponse` was all we needed.
* Invented a docstring example about "cubes of volume 4" that didn't make mathematical sense.

AI is fantastic as a tireless junior/mid-level pair programmer that churns out boilerplate and tests, but it needs an engineer reviewing the diffs with a critical eye to catch missing pieces and unneeded dependencies.

### Watch out for persistent context and prompt baggage
The AI refused to run tests locally because of a stored instruction from a completely different Kaggle project that said "never run tests locally". It took an explicit override to break it out of that loop. When working with stateful or memory-enabled AI tools, you have to be aware of what old assumptions they are carrying into a new project.

### Don't trust claims without terminal output
The AI initially reported everything as verified and working without having actually executed the test suite. Forcing a real run (`python manage.py test packing -v 2`) and piping the raw output into `TEST_OUTPUT.md` gave us concrete proof that all 25 tests genuinely passed.
