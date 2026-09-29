# AI_USAGE.md

## 1. AI tools used

| Tool | Used for |
|---|---|
| Notion AI (custom name "n") | Planning: it suggested prompt ideas for the initial build, and later wrote the "fix all" and "run and verify" prompts given to the coding agent. It also reviewed the repo against the assignment brief and ran the tests in its own sandbox to find problems. It did not write the repo code. |
| Google Antigravity (Gemini 3.8 Flash) | Wrote and edited the repo code, tests, README, seed command, and commits. |

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

- `djangorestframework` was removed from `requirements.txt` because it was unused.
- The persistent local-execution restriction was overridden to allow running Django management and test commands locally.
- The docstring example in `services.py` was replaced with the 9x9x2 cm items in a 10x10x3.5 cm box example.
- The migration was kept as a single clean `0001_initial.py` after standardizing weight units rather than creating a secondary migration.
- [FILL IN BY ME: anything I personally rejected or changed after reading the code]

## 5. Mistakes the AI made

1. **Migrations were never committed.** `packing/migrations/` only had `__init__.py`, so `python manage.py test packing` failed 2 of 11 tests with `no such table: packing_product`, and the GitHub Actions run would have failed. This was found in the review, and the migration was added in the fix round.
2. **Unclear weight units.** `Product.weight` said "grams or kg" and `Box.max_weight` had no unit. Fixed by standardizing on grams.
3. **Misleading docstring example.** The "two cubes of volume 4" example in `services.py` was not a valid cube example. It was replaced with the 9x9x2 cm items in a 10x10x3.5 cm box example.
4. **README problems.** A placeholder clone URL and folder name. It also told users to run `makemigrations` even though migrations should be committed.
5. **Unused dependency.** `djangorestframework` was listed in `requirements.txt` but never used.
6. **Missing edge-case tests.** These were missing: weight boundary, zero quantity, empty box list, API 400/405, no-fit API response, and the staff UI view.
7. **Skipped verification.** After the fix round the coding agent reported the work as done without running any tests, citing an old rule in its setup meant for another project. I overrode the rule for this repo and had it run everything.

**Known limitation, not a bug:** the algorithm checks single-item dimensions, total weight and total volume. Those are necessary but not sufficient conditions for a real 3D fit, so it can give false positives. This is documented in `services.py`, in the README, and in `test_known_limitation_volume_heuristic_false_positive`.

## 6. How I verified the final code

- Ran `python manage.py makemigrations --check --dry-run`, which reported no changes.
- Ran `python manage.py test packing -v 2`, which ran 25 tests and passed. Output is in `TEST_OUTPUT.md`.
- Ran `python manage.py seed_demo` twice. Row counts stayed at 4 boxes, 5 products and 3 orders, so it is idempotent.
- Called the API with curl for each seeded order:
  - `ORD-FIT-SMALL` recommended the Small Box.
  - `ORD-NEED-LARGE` recommended the Large Box.
  - `ORD-NO-FIT` returned `has_recommendation: false`.
- Confirmed `db.sqlite3`, `venv/`, `__pycache__/` and `test_output.txt` are not tracked in git.
- GitHub Actions run: `https://github.com/swarajladke/AI-Assisted-Box-Selection-System/actions`
- [FILL IN BY ME: what I personally checked]
