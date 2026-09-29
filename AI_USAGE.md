# AI_USAGE.md

## 1. AI tools used

| Tool | Used for |
|---|---|
| Notion AI (custom name "n") | Planning: suggested prompt ideas for the initial build, and wrote the "fix all" and "run and verify" prompts. It also reviewed the repo against the assignment requirements and ran tests in its own sandbox to identify problems. It did not write repository code directly. |
| Google Antigravity (Gemini 3.8 Flash) | Wrote and edited the application code, tests, documentation, seed command, and git commits. |

## 2. Prompts I gave

Prompts given to the coding agent, in order:

1. [FILL IN BY ME: paste the exact prompt I sent]
2. [FILL IN BY ME: paste the exact prompt I sent]
3. [FILL IN BY ME: paste the exact prompt I sent]
4. [FILL IN BY ME: paste the exact prompt I sent]
5. [FILL IN BY ME: paste the exact prompt I sent]
6. [FILL IN BY ME: paste the exact prompt I sent]
7. [FILL IN BY ME: paste the exact prompt I sent]
8. [FILL IN BY ME: paste the exact prompt I sent]
9. **"Fix all" prompt (eight numbered steps):**
   - Step 1: Generate and commit `packing/migrations/0001_initial.py`.
   - Step 2: Standardize weight units to grams across models, migrations, `__str__`, and docstrings.
   - Step 3: Add 12 extra tests covering weight boundaries, zero quantities, empty catalogs, API error statuses, staff UI, and the documented 3D volume heuristic false-positive.
   - Step 4: Fix misleading docstring example in `services.py` to use 9x9x2 cm items in a 10x10x3.5 cm box.
   - Step 5: Fix README (corrected GitHub clone URL, removed `makemigrations`, added `@csrf_exempt` note, documented `seed_demo`, specified grams).
   - Step 6: Remove unused `djangorestframework` from `requirements.txt`.
   - Step 7: Add idempotent `seed_demo` management command.
   - Step 8: Verification.
10. **"Run and verify" prompt:** I explicitly authorized the agent to run Django commands locally after it refused because of a stored rule about not running tests locally. It had to run `makemigrations --check`, the tests, `seed_demo` twice, and curl each seeded order.

## 3. Output I accepted

- The core packing algorithm in `packing/services.py`: item rotation via sorted dimensions, total weight and volume checks, and cheapest-box selection with tie-breaking by volume, then alphabetically by name. Also accepted the structured rejection reasons for non-fitting boxes.
- The Django models, the REST endpoint, and the warehouse packing station UI.
- The GitHub Actions CI matrix (`.github/workflows/django-tests.yml`) testing on Python 3.10, 3.11, and 3.12.
- From the "fix all" round, after reviewing the diffs:
  - The `0001_initial.py` migration file.
  - Standardizing on grams across the codebase.
  - 12 new test cases, bringing the total suite to 25 passing tests.
  - Fixes to the docstrings and README.
  - The `seed_demo` management command.
  - Dropping `djangorestframework` from `requirements.txt`.
  - Adding `test_output.txt` to `.gitignore`.

## 4. Output I rejected or modified

- `djangorestframework` was removed from `requirements.txt` because standard Django views and `JsonResponse` were simpler and avoided an unneeded dependency.
- The persistent local-execution restriction was overridden so Django management commands and the test suite could actually run locally on this machine.
- The docstring example in `services.py` was replaced with the concrete 9x9x2 cm items in a 10x10x3.5 cm box example.
- The migration was kept as a single clean `0001_initial.py` when standardizing weight units rather than creating an extra migration.
- [FILL IN BY ME: anything I personally rejected or changed after reading the code]

## 5. Mistakes the AI made

1. **Migrations were never committed.** `packing/migrations/` only had an empty `__init__.py`, meaning `python manage.py test packing` failed immediately with `no such table: packing_product`, and GitHub Actions would have broken.
2. **Unclear weight units.** `Product.weight` said "grams or kg" and `Box.max_weight` had no unit at all, risking silent calculation bugs.
3. **Misleading docstring example.** The "two cubes of volume 4" example in `services.py` was mathematically nonsense for integer cuboids. It was replaced with the 9x9x2 cm items in a 10x10x3.5 cm box example.
4. **README problems.** The README had placeholder clone URLs and told users to run `makemigrations` locally even though migrations belong in version control.
5. **Unused dependency.** `djangorestframework` was added to `requirements.txt` despite never being imported or used.
6. **Missing edge-case tests.** The initial test suite omitted tests for exact weight thresholds, zero-quantity line items, empty box catalogs, HTTP 400/405 API validation, and the staff UI views.
7. **Skipped verification.** The coding agent initially marked the work finished without running tests, blocked by an old rule from a different project. It took an explicit override to get the agent to actually run the commands.

**Known limitation, not a bug:** The algorithm checks single-item dimensions, total weight, and total volume. These are necessary but not sufficient conditions for items to physically fit together in 3D space, which can produce false positives. This is clearly documented in `services.py`, the README, and tested in `test_known_limitation_volume_heuristic_false_positive`.

## 6. How I verified the final code

- Ran `python manage.py makemigrations --check --dry-run` to confirm migrations and models are completely in sync (no changes detected).
- Ran `python manage.py test packing -v 2` and confirmed all 25 tests pass. Output is captured in `TEST_OUTPUT.md`.
- Ran `python manage.py seed_demo` twice and verified row counts stayed steady at 4 boxes, 5 products, and 3 orders with zero duplicates.
- Tested the API with `curl` against each seeded order:
  - `ORD-FIT-SMALL` correctly recommended the Small Box.
  - `ORD-NEED-LARGE` correctly recommended the Large Box.
  - `ORD-NO-FIT` correctly returned `has_recommendation: false`.
- Confirmed `db.sqlite3`, `venv/`, `__pycache__/`, and `test_output.txt` remain untracked by git.
- GitHub Actions run: `https://github.com/swarajladke/AI-Assisted-Box-Selection-System/actions`
- [FILL IN BY ME: what I personally checked]
