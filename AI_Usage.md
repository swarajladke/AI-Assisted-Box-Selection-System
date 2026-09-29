# AI_USAGE.md

## 1. AI tools used

| Tool | Used for |
|---|---|
| Notion AI (custom name "n") | Planning: it wrote the prompts I gave to my coding agent. It also reviewed the repo against the assignment brief and ran the tests in its own sandbox to find problems. It did not write the repo code. |
| Google Antigravity (Gemini 3.8 Flash) | Wrote and edited the repo code, tests, README, seed command, and commits. |

## 2. Prompts I gave

Prompts written by Notion AI and given to the coding agent, in order:

1. **Initial design proposal:** Prompted the agent with the problem domain (Product, Box, Order, OrderItem), requiring a model architecture, step-by-step box selection algorithm, edge-case breakdown, algorithm limitations, and API/UI specs.
2. **Project and app scaffolding:** Created the Django project (`box_selection`), the `packing` app, models (`Product`, `Box`, `Order`, `OrderItem`), strict dimensional and positive validators, Django admin configuration, `requirements.txt`, and `.gitignore`.
3. **Core domain service implementation:** Implemented `packing/services.py` as a pure Python function (`select_best_box`) with zero database access, orthogonal item dimension rotation, weight and volume capacity checks, cheapest-box selection with volume and alphabetical tie-breaking, and structured rejection reason tracking.
4. **API and UI creation:** Added `POST /api/orders/<id>/recommend-box/` with status code validation (200, 400, 404, 405) and a modern warehouse packing station web page at `/` displaying orders, recommended boxes, and full rejection breakdowns.
5. **Initial test suite:** Implemented unit and integration tests covering exact fit, rotation, oversized items, weight limits, volume vs dimension mismatches, cheapest selection, tie-breaking, empty orders, quantity multipliers, and API 404/200 scenarios with one-line bug-catching comments.
6. **Senior engineer code review:** Instructed the agent to review the codebase skeptically to surface bugs, wrong assumptions, N+1 query patterns, and misleading tests.
7. **CI workflow and README:** Added `.github/workflows/django-tests.yml` testing Python 3.10–3.12 and a comprehensive `README.md` covering setup, limits, and API examples.
8. **Git push:** Linked the repository to `https://github.com/swarajladke/AI-Assisted-Box-Selection-System.git` and pushed the `main` branch.
9. **"Fix all" prompt (eight numbered steps):**
   - Step 1: Generate and commit `packing/migrations/0001_initial.py`.
   - Step 2: Standardize weight units to grams across models, migrations, `__str__`, and docstrings.
   - Step 3: Add 12 extra tests covering weight boundaries, zero quantities, empty catalogs, API error statuses, staff UI, and the documented 3D volume heuristic false-positive.
   - Step 4: Fix misleading docstring example in `services.py` to use $9\times9\times2\text{ cm}$ items in a $10\times10\times3.5\text{ cm}$ box.
   - Step 5: Fix README (corrected GitHub clone URL, removed `makemigrations`, added `@csrf_exempt` note, documented `seed_demo`, specified grams).
   - Step 6: Remove unused `djangorestframework` from `requirements.txt`.
   - Step 7: Add idempotent `seed_demo` management command.
   - Step 8: Verification.
10. **"Run and verify" prompt:** Explicitly authorized local Django command execution, ran `makemigrations --check --dry-run`, executed all 25 tests, ran `seed_demo` twice to verify zero duplicates, started `runserver` in the background, curled each seeded order, and added `test_output.txt` to `.gitignore`.

## 3. Output I accepted

- Core algorithm in `packing/services.py`: item rotation via sorted dimensions, total weight and volume checks, and cheapest-box selection with tie-breaks by volume, then by name. It also returns reasons for each rejected box.
- Models, the API endpoint, and the staff UI page.
- GitHub Actions CI workflow matrix (`.github/workflows/django-tests.yml`) testing Python 3.10, 3.11, and 3.12.
- From the "fix all" round, after I checked the diff:
  - `0001_initial.py` migration
  - grams as the standard unit
  - 12 new tests, bringing the total to 25
  - docstring and README fixes
  - `seed_demo` command
  - removal of `djangorestframework`
  - `test_output.txt` added to `.gitignore`

## 4. Output I rejected or modified

- **Removed `djangorestframework`:** Initially included in `requirements.txt`, but since standard Django `JsonResponse` was cleaner and avoided unneeded framework overhead, it was removed.
- **Overrode persistent local execution restriction:** The agent initially refused to run test commands locally due to a global rule meant for another environment (Kaggle). I explicitly issued an override prompt allowing local test and command execution for this Django repository.
- **Replaced abstract docstring example:** The initial docstring in `services.py` referenced "two non-overlapping cubes of volume 4", which is geometrically impossible for integer cuboids. I had the agent replace it with the concrete $9\times9\times2\text{ cm}$ in $10\times10\times3.5\text{ cm}$ collision example from the README.
- **Regenerated migration on help_text update:** When weight units were updated to grams, rather than creating a secondary migration `0002_...`, I required regenerating a single clean `0001_initial.py` before committing.

## 5. Mistakes the AI made

1. **Migrations were never committed.** `packing/migrations/` only had `__init__.py`, so `python manage.py test packing` failed 2 of 11 tests with `no such table: packing_product`, and the GitHub Actions run would have failed. This was found in the review, and the migration was added in the fix round.
2. **Unclear weight units.** `Product.weight` said "grams or kg" and `Box.max_weight` had no unit. Fixed by standardizing on grams.
3. **Misleading docstring example.** The "two cubes of volume 4" example in `services.py` was not a valid cube example. It was replaced with the 9×9×2 cm items in a 10×10×3.5 cm box example.
4. **README problems.** A placeholder clone URL and folder name. It also told users to run `makemigrations` even though migrations should be committed.
5. **Unused dependency.** `djangorestframework` was listed in `requirements.txt` but never used.
6. **Missing edge-case tests.** These were missing: weight boundary, zero quantity, empty box list, API 400/405, no-fit API response, and the staff UI view.
7. **Skipped verification.** After the fix round the coding agent reported the work as done without running any tests, citing an old rule in its setup meant for another project. I overrode the rule for this repo and had it run everything.
8. **N+1 query in warehouse UI template:** In `order_packing.html`, the template initially called `{{ o.items.count }}` inside the dropdown loop, which triggered an extra `COUNT(*)` query for each order rather than using the prefetched cache.
9. **Missing `.gitignore` entry for test logs:** The initial `.gitignore` lacked `test_output.txt`, causing command artifacts to appear in `git status`.

**Known limitation, not a bug:** the algorithm checks single-item dimensions, total weight and total volume. Those are necessary but not sufficient conditions for a real 3D fit, so it can give false positives. This is documented in `services.py`, in the README, and in `test_known_limitation_volume_heuristic_false_positive`.

## 6. How I verified the final code

- Ran `python manage.py makemigrations --check --dry-run`, which reported no changes.
- Ran `python manage.py test packing -v 2`, which ran 25 tests and passed.
- Ran `python manage.py seed_demo` twice. Row counts stayed at 4 boxes, 5 products and 3 orders, so it is idempotent.
- Called the API with curl for each seeded order:
  - `ORD-FIT-SMALL` recommended the Small Box.
  - `ORD-NEED-LARGE` recommended the Large Box.
  - `ORD-NO-FIT` returned `has_recommendation: false`.
- Confirmed `db.sqlite3`, `venv/`, `__pycache__/` and `test_output.txt` are not tracked in git.
- GitHub Actions run: `https://github.com/swarajladke/AI-Assisted-Box-Selection-System/actions`
- Verified each git commit diff locally to confirm that code modifications remained targeted and minimal without introducing unneeded dependencies.
