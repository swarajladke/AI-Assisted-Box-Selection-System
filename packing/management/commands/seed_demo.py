from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from packing.models import Product, Box, Order, OrderItem


class Command(BaseCommand):
    help = "Seed demo catalog with standard boxes, products, and test orders (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding demo boxes...")
        boxes_data = [
            {
                "name": "Small Box",
                "inner_length": Decimal("15.00"),
                "inner_width": Decimal("10.00"),
                "inner_height": Decimal("10.00"),
                "max_weight": Decimal("1000.00"),
                "cost": Decimal("1.00"),
            },
            {
                "name": "Medium Box",
                "inner_length": Decimal("25.00"),
                "inner_width": Decimal("20.00"),
                "inner_height": Decimal("15.00"),
                "max_weight": Decimal("3000.00"),
                "cost": Decimal("2.50"),
            },
            {
                "name": "Large Box",
                "inner_length": Decimal("40.00"),
                "inner_width": Decimal("30.00"),
                "inner_height": Decimal("25.00"),
                "max_weight": Decimal("7000.00"),
                "cost": Decimal("4.00"),
            },
            {
                "name": "Heavy-Duty Crate",
                "inner_length": Decimal("50.00"),
                "inner_width": Decimal("40.00"),
                "inner_height": Decimal("35.00"),
                "max_weight": Decimal("20000.00"),
                "cost": Decimal("8.50"),
            },
        ]

        boxes = {}
        for b_data in boxes_data:
            box, created = Box.objects.update_or_create(
                name=b_data["name"],
                defaults=b_data
            )
            boxes[box.name] = box
            action = "Created" if created else "Updated"
            self.stdout.write(f"  [{action}] {box.name}")

        self.stdout.write("Seeding demo products...")
        products_data = [
            {
                "name": "Wireless Earbuds",
                "length": Decimal("6.00"),
                "width": Decimal("5.00"),
                "height": Decimal("3.00"),
                "weight": Decimal("80.00"),
            },
            {
                "name": "Ceramic Coffee Mug",
                "length": Decimal("12.00"),
                "width": Decimal("9.00"),
                "height": Decimal("10.00"),
                "weight": Decimal("350.00"),
            },
            {
                "name": "Mechanical Gaming Keyboard",
                "length": Decimal("38.00"),
                "width": Decimal("15.00"),
                "height": Decimal("4.50"),
                "weight": Decimal("1100.00"),
            },
            {
                "name": "Desk Monitor Stand",
                "length": Decimal("45.00"),
                "width": Decimal("22.00"),
                "height": Decimal("12.00"),
                "weight": Decimal("2400.00"),
            },
            {
                "name": "Standing Desk Frame (Oversized)",
                "length": Decimal("120.00"),
                "width": Decimal("65.00"),
                "height": Decimal("25.00"),
                "weight": Decimal("28000.00"),
            },
        ]

        products = {}
        for p_data in products_data:
            prod, created = Product.objects.update_or_create(
                name=p_data["name"],
                defaults=p_data
            )
            products[prod.name] = prod
            action = "Created" if created else "Updated"
            self.stdout.write(f"  [{action}] {prod.name}")

        self.stdout.write("Seeding demo orders...")
        orders_data = [
            {
                # Order 1: Fits in the Small Box
                "order_number": "ORD-FIT-SMALL",
                "items": [
                    {"product": products["Wireless Earbuds"], "quantity": 1},
                ],
                "expected": "Fits 'Small Box'",
            },
            {
                # Order 2: Item is 38cm long, exceeds Small (15cm) and Medium (25cm), needs Large Box (40cm)
                "order_number": "ORD-NEED-LARGE",
                "items": [
                    {"product": products["Mechanical Gaming Keyboard"], "quantity": 1},
                    {"product": products["Ceramic Coffee Mug"], "quantity": 1},
                ],
                "expected": "Needs 'Large Box'",
            },
            {
                # Order 3: 120cm length and 28kg exceeds all boxes (fits no box)
                "order_number": "ORD-NO-FIT",
                "items": [
                    {"product": products["Standing Desk Frame (Oversized)"], "quantity": 1},
                ],
                "expected": "Fits no box (Exceeds capacity)",
            },
        ]

        for o_data in orders_data:
            order, created = Order.objects.get_or_create(
                order_number=o_data["order_number"]
            )
            # Idempotent item sync: remove existing order items and re-insert
            order.items.all().delete()
            for it in o_data["items"]:
                OrderItem.objects.create(
                    order=order,
                    product=it["product"],
                    quantity=it["quantity"]
                )
            action = "Created" if created else "Updated"
            self.stdout.write(f"  [{action}] {order.order_number} ({o_data['expected']})")

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully (idempotent)!"))
