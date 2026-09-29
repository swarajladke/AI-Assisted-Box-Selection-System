from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse

from .models import Product, Box, Order, OrderItem
from .services import select_best_box


class BoxSelectionServiceTests(TestCase):
    """Unit tests for pure box selection domain logic in packing/services.py."""

    def test_single_item_fits_exactly(self):
        # Catches off-by-one / strict inequality bugs where exact dimension or weight boundaries (<= vs <) cause false rejections.
        item = {
            'name': 'Exact Cube',
            'length': Decimal('10.00'),
            'width': Decimal('10.00'),
            'height': Decimal('10.00'),
            'weight': Decimal('500.00'),
            'quantity': 1
        }
        box = {
            'name': 'Snug Box',
            'inner_length': Decimal('10.00'),
            'inner_width': Decimal('10.00'),
            'inner_height': Decimal('10.00'),
            'max_weight': Decimal('500.00'),
            'cost': Decimal('1.50')
        }
        result = select_best_box(items=[item], boxes=[box])
        self.assertTrue(result.has_recommendation)
        self.assertEqual(result.recommended_box['name'], 'Snug Box')
        self.assertEqual(len(result.rejected_boxes), 0)

    def test_item_only_fits_when_rotated(self):
        # Catches failure to sort item and box dimensions prior to comparison, causing false rejections due to item orientation.
        item = {
            'name': 'Long Ruler',
            'length': Decimal('30.00'),
            'width': Decimal('10.00'),
            'height': Decimal('5.00'),
            'weight': Decimal('100.00'),
            'quantity': 1
        }
        # Box has matching dimensions but declared in permuted order:
        box = {
            'name': 'Rotated Box',
            'inner_length': Decimal('10.00'),
            'inner_width': Decimal('5.00'),
            'inner_height': Decimal('30.00'),
            'max_weight': Decimal('1000.00'),
            'cost': Decimal('2.00')
        }
        result = select_best_box(items=[item], boxes=[box])
        self.assertTrue(result.has_recommendation)
        self.assertEqual(result.recommended_box['name'], 'Rotated Box')

    def test_item_too_big_for_every_box(self):
        # Catches false-positive recommendations when an oversized item exceeds all dimensions of every available box.
        item = {
            'name': 'Giant Poster',
            'length': Decimal('100.00'),
            'width': Decimal('80.00'),
            'height': Decimal('10.00'),
            'weight': Decimal('500.00'),
            'quantity': 1
        }
        boxes = [
            {
                'name': 'Small Box',
                'inner_length': Decimal('20.00'),
                'inner_width': Decimal('20.00'),
                'inner_height': Decimal('20.00'),
                'max_weight': Decimal('2000.00'),
                'cost': Decimal('1.00')
            },
            {
                'name': 'Medium Box',
                'inner_length': Decimal('40.00'),
                'inner_width': Decimal('40.00'),
                'inner_height': Decimal('40.00'),
                'max_weight': Decimal('5000.00'),
                'cost': Decimal('3.00')
            }
        ]
        result = select_best_box(items=[item], boxes=boxes)
        self.assertFalse(result.has_recommendation)
        self.assertIsNone(result.recommended_box)
        self.assertEqual(len(result.rejected_boxes), 2)
        self.assertIn("exceeds box dimensions", result.rejected_boxes[0].reason)

    def test_weight_exceeding_capacity_even_though_dimensions_fit(self):
        # Catches missing or unenforced weight capacity checks when volumetric dimensions pass without issue.
        item = {
            'name': 'Lead Brick',
            'length': Decimal('10.00'),
            'width': Decimal('10.00'),
            'height': Decimal('10.00'),
            'weight': Decimal('8000.00'),
            'quantity': 1
        }
        box = {
            'name': 'Spacious Cardboard Box',
            'inner_length': Decimal('50.00'),
            'inner_width': Decimal('50.00'),
            'inner_height': Decimal('50.00'),
            'max_weight': Decimal('5000.00'),
            'cost': Decimal('2.50')
        }
        result = select_best_box(items=[item], boxes=[box])
        self.assertFalse(result.has_recommendation)
        self.assertEqual(len(result.rejected_boxes), 1)
        self.assertIn("exceeds box max weight capacity", result.rejected_boxes[0].reason)

    def test_several_items_volume_passes_but_one_item_dimensions_fail(self):
        # Catches bugs where algorithms rely purely on total order volume and fail to check each individual item's dimensional bounds.
        items = [
            {
                'name': 'Tiny Bead',
                'length': Decimal('2.00'),
                'width': Decimal('2.00'),
                'height': Decimal('2.00'),
                'weight': Decimal('10.00'),
                'quantity': 5
            },
            {
                'name': 'Thin Skewer',
                'length': Decimal('45.00'),
                'width': Decimal('1.00'),
                'height': Decimal('1.00'),
                'weight': Decimal('20.00'),
                'quantity': 1
            }
        ]
        # Total volume is tiny (~85 cm³), easily smaller than 27000 cm³ box, but 45cm skewer cannot fit into 30x30x30 box if max dimension is 30.
        box = {
            'name': 'Cube Box 30',
            'inner_length': Decimal('30.00'),
            'inner_width': Decimal('30.00'),
            'inner_height': Decimal('30.00'),
            'max_weight': Decimal('10000.00'),
            'cost': Decimal('3.00')
        }
        result = select_best_box(items=items, boxes=[box])
        self.assertFalse(result.has_recommendation)
        self.assertEqual(len(result.rejected_boxes), 1)
        self.assertIn("Thin Skewer", result.rejected_boxes[0].reason)

    def test_cheapest_box_selection(self):
        # Catches prioritizing smaller volume over procurement cost or reversing the sort order when picking suitable boxes.
        item = {
            'name': 'Standard Book',
            'length': Decimal('15.00'),
            'width': Decimal('10.00'),
            'height': Decimal('4.00'),
            'weight': Decimal('400.00'),
            'quantity': 1
        }
        expensive_small_box = {
            'name': 'Premium Custom Box',
            'inner_length': Decimal('16.00'),
            'inner_width': Decimal('12.00'),
            'inner_height': Decimal('6.00'),
            'max_weight': Decimal('2000.00'),
            'cost': Decimal('4.50')
        }
        cheaper_large_box = {
            'name': 'Economy Bulk Box',
            'inner_length': Decimal('30.00'),
            'inner_width': Decimal('30.00'),
            'inner_height': Decimal('30.00'),
            'max_weight': Decimal('5000.00'),
            'cost': Decimal('1.20')
        }
        result = select_best_box(items=[item], boxes=[expensive_small_box, cheaper_large_box])
        self.assertTrue(result.has_recommendation)
        self.assertEqual(result.recommended_box['name'], 'Economy Bulk Box')

    def test_tie_breaking_by_volume_then_name(self):
        # Catches non-deterministic box recommendations when multiple suitable boxes share the exact same cost.
        item = {
            'name': 'Watch',
            'length': Decimal('8.00'),
            'width': Decimal('8.00'),
            'height': Decimal('5.00'),
            'weight': Decimal('250.00'),
            'quantity': 1
        }
        same_cost_boxes = [
            {
                'name': 'Box C (Big)',
                'inner_length': Decimal('25.00'),
                'inner_width': Decimal('25.00'),
                'inner_height': Decimal('20.00'),  # Volume: 12500
                'max_weight': Decimal('2000.00'),
                'cost': Decimal('2.00')
            },
            {
                'name': 'Box B (Small)',
                'inner_length': Decimal('10.00'),
                'inner_width': Decimal('10.00'),
                'inner_height': Decimal('10.00'),  # Volume: 1000
                'max_weight': Decimal('2000.00'),
                'cost': Decimal('2.00')
            },
            {
                'name': 'Box A (Small Identical Volume)',
                'inner_length': Decimal('10.00'),
                'inner_width': Decimal('10.00'),
                'inner_height': Decimal('10.00'),  # Volume: 1000, alphabetically precedes Box B
                'max_weight': Decimal('2000.00'),
                'cost': Decimal('2.00')
            }
        ]
        result = select_best_box(items=[item], boxes=same_cost_boxes)
        self.assertTrue(result.has_recommendation)
        # Should pick lowest cost ($2.00), lowest volume (1000), and first alphabetically ("Box A (Small Identical Volume)")
        self.assertEqual(result.recommended_box['name'], 'Box A (Small Identical Volume)')

    def test_empty_order(self):
        # Catches crash bugs (IndexError, ZeroDivisionError) when order contains no items or is empty.
        box = {
            'name': 'Box 1',
            'inner_length': Decimal('10.00'),
            'inner_width': Decimal('10.00'),
            'inner_height': Decimal('10.00'),
            'max_weight': Decimal('1000.00'),
            'cost': Decimal('1.00')
        }
        result = select_best_box(items=[], boxes=[box])
        self.assertFalse(result.has_recommendation)
        self.assertIsNone(result.recommended_box)
        self.assertEqual(result.reason, "No items provided to pack.")

    def test_quantity_greater_than_one(self):
        # Catches bugs where item quantity is ignored, preventing accurate total order weight and volume calculation.
        item = {
            'name': 'Heavy Mug',
            'length': Decimal('10.00'),
            'width': Decimal('10.00'),
            'height': Decimal('10.00'),
            'weight': Decimal('600.00'),
            'quantity': 3  # Total weight: 1800, Total volume: 3000
        }
        # Box max weight 1500 is enough for 1 or 2 mugs, but fails 3 mugs:
        box_insufficient_weight = {
            'name': 'Weight Fail Box',
            'inner_length': Decimal('20.00'),
            'inner_width': Decimal('20.00'),
            'inner_height': Decimal('20.00'),
            'max_weight': Decimal('1500.00'),
            'cost': Decimal('1.50')
        }
        box_sufficient = {
            'name': 'Sufficient Box',
            'inner_length': Decimal('20.00'),
            'inner_width': Decimal('20.00'),
            'inner_height': Decimal('20.00'),
            'max_weight': Decimal('2500.00'),
            'cost': Decimal('2.00')
        }
        result = select_best_box(items=[item], boxes=[box_insufficient_weight, box_sufficient])
        self.assertTrue(result.has_recommendation)
        self.assertEqual(result.recommended_box['name'], 'Sufficient Box')
        self.assertEqual(len(result.rejected_boxes), 1)
        self.assertIn("exceeds box max weight capacity", result.rejected_boxes[0].reason)

    def test_single_item_heavier_than_every_box_max_weight(self):
        # Catches failure to reject all boxes when a single item's weight exceeds the max weight capacity of every box.
        heavy_item = {
            'name': 'Anvil',
            'length': Decimal('10.00'),
            'width': Decimal('10.00'),
            'height': Decimal('10.00'),
            'weight': Decimal('99999.00'),
            'quantity': 1
        }
        boxes = [
            {
                'name': 'Light Box',
                'inner_length': Decimal('20.00'),
                'inner_width': Decimal('20.00'),
                'inner_height': Decimal('20.00'),
                'max_weight': Decimal('1000.00'),
                'cost': Decimal('1.00')
            },
            {
                'name': 'Medium Box',
                'inner_length': Decimal('30.00'),
                'inner_width': Decimal('30.00'),
                'inner_height': Decimal('30.00'),
                'max_weight': Decimal('5000.00'),
                'cost': Decimal('2.00')
            }
        ]
        result = select_best_box(items=[heavy_item], boxes=boxes)
        self.assertFalse(result.has_recommendation)
        self.assertIsNone(result.recommended_box)
        self.assertEqual(len(result.rejected_boxes), 2)
        self.assertIn("exceeds box max weight capacity", result.rejected_boxes[0].reason)
        self.assertIn("exceeds box max weight capacity", result.rejected_boxes[1].reason)

    def test_order_weight_exactly_equal_to_box_max_weight(self):
        # Catches boundary off-by-one errors where strictly less (<) is mistakenly used instead of less-than-or-equal (<=) for max weight.
        item = {
            'name': 'Exact Weight Item',
            'length': Decimal('10.00'),
            'width': Decimal('10.00'),
            'height': Decimal('10.00'),
            'weight': Decimal('2500.00'),
            'quantity': 1
        }
        box = {
            'name': 'Exact Threshold Box',
            'inner_length': Decimal('20.00'),
            'inner_width': Decimal('20.00'),
            'inner_height': Decimal('20.00'),
            'max_weight': Decimal('2500.00'),
            'cost': Decimal('2.00')
        }
        result = select_best_box(items=[item], boxes=[box])
        self.assertTrue(result.has_recommendation)
        self.assertEqual(result.recommended_box['name'], 'Exact Threshold Box')

    def test_order_weight_one_gram_over_max_weight(self):
        # Catches precision or rounding bugs where an order exceeding max weight by a single gram is erroneously approved.
        item = {
            'name': 'Overweight Item',
            'length': Decimal('10.00'),
            'width': Decimal('10.00'),
            'height': Decimal('10.00'),
            'weight': Decimal('2501.00'),
            'quantity': 1
        }
        box = {
            'name': 'Strict Threshold Box',
            'inner_length': Decimal('20.00'),
            'inner_width': Decimal('20.00'),
            'inner_height': Decimal('20.00'),
            'max_weight': Decimal('2500.00'),
            'cost': Decimal('2.00')
        }
        result = select_best_box(items=[item], boxes=[box])
        self.assertFalse(result.has_recommendation)
        self.assertEqual(len(result.rejected_boxes), 1)
        self.assertIn("exceeds box max weight capacity", result.rejected_boxes[0].reason)

    def test_order_item_with_quantity_zero_ignored(self):
        # Catches bugs where zero-quantity line items add phantom weight, volume, or dimension conflicts to an otherwise valid order.
        items = [
            {
                'name': 'Cancelled Giant Sofa',
                'length': Decimal('300.00'),
                'width': Decimal('200.00'),
                'height': Decimal('150.00'),
                'weight': Decimal('50000.00'),
                'quantity': 0
            },
            {
                'name': 'Active Pen',
                'length': Decimal('14.00'),
                'width': Decimal('1.00'),
                'height': Decimal('1.00'),
                'weight': Decimal('25.00'),
                'quantity': 1
            }
        ]
        box = {
            'name': 'Small Parcel',
            'inner_length': Decimal('20.00'),
            'inner_width': Decimal('10.00'),
            'inner_height': Decimal('5.00'),
            'max_weight': Decimal('500.00'),
            'cost': Decimal('1.00')
        }
        result = select_best_box(items=items, boxes=[box])
        self.assertTrue(result.has_recommendation)
        self.assertEqual(result.recommended_box['name'], 'Small Parcel')

    def test_all_items_with_quantity_zero(self):
        # Catches failure to return the explicit 'zero or non-positive quantity' error result when all order line items have quantity 0.
        items = [
            {
                'name': 'Cancelled Item 1',
                'length': Decimal('10.00'),
                'width': Decimal('10.00'),
                'height': Decimal('10.00'),
                'weight': Decimal('100.00'),
                'quantity': 0
            },
            {
                'name': 'Cancelled Item 2',
                'length': Decimal('5.00'),
                'width': Decimal('5.00'),
                'height': Decimal('5.00'),
                'weight': Decimal('50.00'),
                'quantity': 0
            }
        ]
        box = {
            'name': 'Box 1',
            'inner_length': Decimal('20.00'),
            'inner_width': Decimal('20.00'),
            'inner_height': Decimal('20.00'),
            'max_weight': Decimal('1000.00'),
            'cost': Decimal('1.00')
        }
        result = select_best_box(items=items, boxes=[box])
        self.assertFalse(result.has_recommendation)
        self.assertIsNone(result.recommended_box)
        self.assertEqual(result.reason, "All order items have zero or non-positive quantity.")

    def test_empty_box_list(self):
        # Catches unhandled exceptions or missing failure reason when the box catalog is completely empty.
        item = {
            'name': 'Item',
            'length': Decimal('10.00'),
            'width': Decimal('10.00'),
            'height': Decimal('10.00'),
            'weight': Decimal('100.00'),
            'quantity': 1
        }
        result = select_best_box(items=[item], boxes=[])
        self.assertFalse(result.has_recommendation)
        self.assertIsNone(result.recommended_box)
        self.assertEqual(result.reason, "No candidate boxes available for selection.")

    def test_known_limitation_volume_heuristic_false_positive(self):
        # Documents known limitation: total volume and individual dimensions pass, but items physically collide in 3D space.
        # Two 9x9x2 items (total volume 324 cm3) pass into a 10x10x3.5 box (volume 350 cm3) because each 9x9x2 fits
        # individually and 324 <= 350, even though stacking requires height 4.0 and side-by-side requires width 18.0.
        items = [
            {
                'name': 'Flat Block A',
                'length': Decimal('9.00'),
                'width': Decimal('9.00'),
                'height': Decimal('2.00'),
                'weight': Decimal('100.00'),
                'quantity': 1
            },
            {
                'name': 'Flat Block B',
                'length': Decimal('9.00'),
                'width': Decimal('9.00'),
                'height': Decimal('2.00'),
                'weight': Decimal('100.00'),
                'quantity': 1
            }
        ]
        box = {
            'name': 'Tight Shallow Box',
            'inner_length': Decimal('10.00'),
            'inner_width': Decimal('10.00'),
            'inner_height': Decimal('3.50'),
            'max_weight': Decimal('1000.00'),
            'cost': Decimal('1.50')
        }
        result = select_best_box(items=items, boxes=[box])
        # Documents that the current heuristic approves this box despite physical 3D impossibility
        self.assertTrue(result.has_recommendation)
        self.assertEqual(result.recommended_box['name'], 'Tight Shallow Box')


class BoxSelectionAPITests(TestCase):
    """Integration tests for the REST API endpoint POST /api/orders/<id>/recommend-box/."""

    def setUp(self):
        self.client = Client()

    def test_api_404_not_found(self):
        # Catches unhandled ObjectDoesNotExist exceptions or returning 500/200 when requesting a non-existent order.
        response = self.client.post('/api/orders/99999/recommend-box/')
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Order with ID 99999 not found.")

    def test_api_get_request_returns_405(self):
        # Catches failure to restrict the recommendation endpoint to POST requests only.
        order = Order.objects.create(order_number="ORD-METHOD-TEST")
        response = self.client.get(f'/api/orders/{order.id}/recommend-box/')
        self.assertEqual(response.status_code, 405)
        self.assertIn("error", response.json())

    def test_api_order_with_no_items_returns_400(self):
        # Catches missing validation when an order exists in the DB but has no line items attached.
        order = Order.objects.create(order_number="ORD-NO-ITEMS")
        Box.objects.create(
            name="Sample Box",
            inner_length=Decimal('20.00'),
            inner_width=Decimal('20.00'),
            inner_height=Decimal('20.00'),
            max_weight=Decimal('2000.00'),
            cost=Decimal('1.00')
        )
        response = self.client.post(f'/api/orders/{order.id}/recommend-box/')
        self.assertEqual(response.status_code, 400)
        self.assertIn("has no items to pack", response.json()["error"])

    def test_api_no_boxes_in_db_returns_400(self):
        # Catches unhandled 500 errors when the Box table has zero records available for recommendation.
        product = Product.objects.create(
            name="Book",
            length=Decimal('20.00'),
            width=Decimal('15.00'),
            height=Decimal('3.00'),
            weight=Decimal('300.00')
        )
        order = Order.objects.create(order_number="ORD-NO-BOXES")
        OrderItem.objects.create(order=order, product=product, quantity=1)

        response = self.client.post(f'/api/orders/{order.id}/recommend-box/')
        self.assertEqual(response.status_code, 400)
        self.assertIn("No shipping boxes exist in the system", response.json()["error"])

    def test_api_case_where_no_box_fits_returns_200_with_has_recommendation_false(self):
        # Catches returning 400/500 instead of a valid 200 result with has_recommendation false when an order exceeds all boxes.
        huge_product = Product.objects.create(
            name="Kayak",
            length=Decimal('300.00'),
            width=Decimal('80.00'),
            height=Decimal('40.00'),
            weight=Decimal('25000.00')
        )
        Box.objects.create(
            name="Small Parcel",
            inner_length=Decimal('30.00'),
            inner_width=Decimal('30.00'),
            inner_height=Decimal('30.00'),
            max_weight=Decimal('5000.00'),
            cost=Decimal('2.00')
        )
        order = Order.objects.create(order_number="ORD-TOO-LARGE")
        OrderItem.objects.create(order=order, product=huge_product, quantity=1)

        response = self.client.post(f'/api/orders/{order.id}/recommend-box/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["has_recommendation"])
        self.assertIsNone(data["recommended_box"])
        self.assertGreater(len(data["rejected_boxes"]), 0)

    def test_api_success_case(self):
        # Catches serialization failures, database relation prefetching bugs, or broken payload contracts in the API endpoint.
        product = Product.objects.create(
            name="Mechanical Keyboard",
            length=Decimal('35.00'),
            width=Decimal('15.00'),
            height=Decimal('5.00'),
            weight=Decimal('900.00')
        )
        box = Box.objects.create(
            name="Medium Parcel Box",
            inner_length=Decimal('40.00'),
            inner_width=Decimal('20.00'),
            inner_height=Decimal('10.00'),
            max_weight=Decimal('3000.00'),
            cost=Decimal('2.15')
        )
        order = Order.objects.create(order_number="ORD-API-TEST-001")
        OrderItem.objects.create(order=order, product=product, quantity=1)

        response = self.client.post(f'/api/orders/{order.id}/recommend-box/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["has_recommendation"])
        self.assertIsNotNone(data["recommended_box"])
        self.assertEqual(data["recommended_box"]["id"], box.id)
        self.assertEqual(data["recommended_box"]["name"], "Medium Parcel Box")
        self.assertEqual(data["recommended_box"]["cost"], 2.15)
        self.assertEqual(data["order"]["order_number"], "ORD-API-TEST-001")
        self.assertEqual(data["order"]["total_items"], 1)


class StaffPackingViewTests(TestCase):
    """Integration tests for the warehouse staff packing UI view."""

    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(
            name="Desk Clock",
            length=Decimal('12.00'),
            width=Decimal('8.00'),
            height=Decimal('6.00'),
            weight=Decimal('350.00')
        )
        self.box = Box.objects.create(
            name="Clock Box",
            inner_length=Decimal('15.00'),
            inner_width=Decimal('10.00'),
            inner_height=Decimal('8.00'),
            max_weight=Decimal('1000.00'),
            cost=Decimal('1.80')
        )
        self.order = Order.objects.create(order_number="ORD-UI-001")
        OrderItem.objects.create(order=self.order, product=self.product, quantity=1)

    def test_staff_packing_view_landing_page_renders_200(self):
        # Catches template rendering errors, syntax issues in order_packing.html, or missing template context variables on GET /.
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select Order for Packing Inspection")

    def test_staff_packing_view_with_valid_order_shows_recommendation(self):
        # Catches view failure to compute and display recommended box specifications when a valid order_id query param is supplied.
        response = self.client.get(f'/?order_id={self.order.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Clock Box")
        self.assertContains(response, "Recommended Box")
        self.assertContains(response, "Desk Clock")

    def test_staff_packing_view_with_nonexistent_order_shows_error_message(self):
        # Catches unhandled 404/500 errors or failure to present a user-friendly error notice when an unknown order_id is requested.
        response = self.client.get('/?order_id=99999')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Order #99999 does not exist.")
