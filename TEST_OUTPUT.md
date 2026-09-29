# Test Output

**Command:**
```bash
python manage.py test packing -v 2
```

**Date:** 2026-09-29  
**Python Version:** Python 3.11.0  
**Django Version:** 5.2.17  
**GitHub Actions Run:** https://github.com/swarajladke/AI-Assisted-Box-Selection-System/actions/runs/36578199314

---

## Terminal Output

```text
Creating test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Found 25 test(s).
Operations to perform:
  Synchronize unmigrated apps: messages, staticfiles
  Apply all migrations: admin, auth, contenttypes, packing, sessions
Synchronizing apps without migrations:
  Creating tables...
    Running deferred SQL...
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying packing.0001_initial... OK
  Applying sessions.0001_initial...test_api_404_not_found (packing.tests.BoxSelectionAPITests.test_api_404_not_found) ... ok
test_api_case_where_no_box_fits_returns_200_with_has_recommendation_false (packing.tests.BoxSelectionAPITests.test_api_case_where_no_box_fits_returns_200_with_has_recommendation_false) ... ok
test_api_get_request_returns_405 (packing.tests.BoxSelectionAPITests.test_api_get_request_returns_405) ... ok
test_api_no_boxes_in_db_returns_400 (packing.tests.BoxSelectionAPITests.test_api_no_boxes_in_db_returns_400) ... ok
test_api_order_with_no_items_returns_400 (packing.tests.BoxSelectionAPITests.test_api_order_with_no_items_returns_400) ... ok
test_api_success_case (packing.tests.BoxSelectionAPITests.test_api_success_case) ... ok
test_all_items_with_quantity_zero (packing.tests.BoxSelectionServiceTests.test_all_items_with_quantity_zero) ... ok
test_cheapest_box_selection (packing.tests.BoxSelectionServiceTests.test_cheapest_box_selection) ... ok
test_empty_box_list (packing.tests.BoxSelectionServiceTests.test_empty_box_list) ... ok
test_empty_order (packing.tests.BoxSelectionServiceTests.test_empty_order) ... ok
test_item_only_fits_when_rotated (packing.tests.BoxSelectionServiceTests.test_item_only_fits_when_rotated) ... ok
test_item_too_big_for_every_box (packing.tests.BoxSelectionServiceTests.test_item_too_big_for_every_box) ... ok
test_known_limitation_volume_heuristic_false_positive (packing.tests.BoxSelectionServiceTests.test_known_limitation_volume_heuristic_false_positive) ... ok
test_order_item_with_quantity_zero_ignored (packing.tests.BoxSelectionServiceTests.test_order_item_with_quantity_zero_ignored) ... ok
test_order_weight_exactly_equal_to_box_max_weight (packing.tests.BoxSelectionServiceTests.test_order_weight_exactly_equal_to_box_max_weight) ... ok
test_order_weight_one_gram_over_max_weight (packing.tests.BoxSelectionServiceTests.test_order_weight_one_gram_over_max_weight) ... ok
test_quantity_greater_than_one (packing.tests.BoxSelectionServiceTests.test_quantity_greater_than_one) ... ok
test_several_items_volume_passes_but_one_item_dimensions_fail (packing.tests.BoxSelectionServiceTests.test_several_items_volume_passes_but_one_item_dimensions_fail) ... ok
test_single_item_fits_exactly (packing.tests.BoxSelectionServiceTests.test_single_item_fits_exactly) ... ok
test_single_item_heavier_than_every_box_max_weight (packing.tests.BoxSelectionServiceTests.test_single_item_heavier_than_every_box_max_weight) ... ok
test_tie_breaking_by_volume_then_name (packing.tests.BoxSelectionServiceTests.test_tie_breaking_by_volume_then_name) ... ok
test_weight_exceeding_capacity_even_though_dimensions_fit (packing.tests.BoxSelectionServiceTests.test_weight_exceeding_capacity_even_though_dimensions_fit) ... ok
test_staff_packing_view_landing_page_renders_200 (packing.tests.StaffPackingViewTests.test_staff_packing_view_landing_page_renders_200) ... ok
test_staff_packing_view_with_nonexistent_order_shows_error_message (packing.tests.StaffPackingViewTests.test_staff_packing_view_with_nonexistent_order_shows_error_message) ... ok
test_staff_packing_view_with_valid_order_shows_recommendation (packing.tests.StaffPackingViewTests.test_staff_packing_view_with_valid_order_shows_recommendation) ... ok

----------------------------------------------------------------------
Ran 25 tests in 0.247s

OK
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
 OK
System check identified no issues (0 silenced).
```
