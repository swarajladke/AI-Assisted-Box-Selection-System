"""
Services for box selection and packaging recommendation.

IMPORTANT LIMITATIONS & NON-GUARANTEES:
---------------------------------------
This box selection algorithm uses a fast heuristic based on:
1. Item-level orthogonal rotation check (sorted item dimensions <= sorted box dimensions)
2. Cumulative order weight vs. box maximum weight capacity (both in grams)
3. Cumulative order volume vs. box usable internal volume (both in cm³)

WHAT THIS ALGORITHM DOES NOT GUARANTEE:
1. 3D Bin Packing Feasibility:
   Satisfying the total volume check and single-item bounding dimension check is a
   NECESSARY condition, but NOT a SUFFICIENT condition for multiple items to physically
   fit together into the 3D space of the box. 3D Bin Packing is NP-hard. For instance,
   two items of 9x9x2 cm (total volume 324 cm³) will pass all checks for a 10x10x3.5 cm
   box (volume 350 cm³). However, they cannot physically fit together because stacking
   them requires 4.0 cm height, and side-by-side placement requires 18.0 cm width.
2. Dunnage & Void Padding:
   This logic assumes zero-margin rigid placement without accounting for bubble wrap,
   kraft paper, or corrugated wall thickness tolerances.
3. Structural Integrity & Stacking Rules:
   It does not guarantee structural load bearing (e.g. heavy items crushing fragile items)
   or balance/center-of-gravity constraints required by some shipping carriers.
4. Non-Cuboidal / Flexible Items:
   All items and boxes are treated as rigid rectangular cuboids. Nested items (e.g., cups)
   or malleable items (e.g., apparel) are not compressed.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, List, Optional, Sequence


@dataclass(frozen=True)
class RejectedBox:
    box: Any
    reason: str


@dataclass(frozen=True)
class BoxSelectionResult:
    recommended_box: Optional[Any]
    reason: str
    rejected_boxes: List[RejectedBox]

    @property
    def has_recommendation(self) -> bool:
        return self.recommended_box is not None


def _get_dimension_triplet(obj: Any, length_attr: str, width_attr: str, height_attr: str) -> tuple[Decimal, Decimal, Decimal]:
    """Helper to extract dimensions whether from model instances, dataclasses, or dicts."""
    if isinstance(obj, dict):
        l = Decimal(str(obj[length_attr]))
        w = Decimal(str(obj[width_attr]))
        h = Decimal(str(obj[height_attr]))
    else:
        l = Decimal(str(getattr(obj, length_attr)))
        w = Decimal(str(getattr(obj, width_attr)))
        h = Decimal(str(getattr(obj, height_attr)))
    return (l, w, h)


def _get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """Helper to get attribute from dict or object."""
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)


def select_best_box(items: Sequence[Any], boxes: Sequence[Any]) -> BoxSelectionResult:
    """
    Pure function to recommend the cheapest suitable box for a collection of order items.

    Args:
        items: An iterable of order items or dicts. Each item must provide:
               - length, width, height (dimensions in cm)
               - weight (in grams)
               - quantity
               - optional name or sku for reporting
        boxes: An iterable of available boxes or dicts. Each box must provide:
               - inner_length, inner_width, inner_height (internal dimensions in cm)
               - max_weight (in grams)
               - cost
               - name

    Returns:
        BoxSelectionResult containing:
        - recommended_box: Selected Box instance, dict, or None if no box fits.
        - reason: Explanation of selection or failure.
        - rejected_boxes: List of RejectedBox(box, reason).
    """
    rejected_boxes: List[RejectedBox] = []

    # If no items provided or empty box list
    if not items:
        return BoxSelectionResult(
            recommended_box=None,
            reason="No items provided to pack.",
            rejected_boxes=[]
        )

    if not boxes:
        return BoxSelectionResult(
            recommended_box=None,
            reason="No candidate boxes available for selection.",
            rejected_boxes=[]
        )

    # Calculate total order weight and volume, and normalize item dimensions
    total_order_weight = Decimal('0.00')
    total_order_volume = Decimal('0.00')
    normalized_items = []

    for idx, item in enumerate(items):
        qty = int(_get_attr(item, 'quantity', 1))
        if qty <= 0:
            continue

        item_name = _get_attr(item, 'name') or _get_attr(item, 'sku') or f"Item #{idx + 1}"
        weight = Decimal(str(_get_attr(item, 'weight', 0)))

        # Handle dimension attributes
        if hasattr(item, 'inner_length'):
            l, w, h = _get_dimension_triplet(item, 'inner_length', 'inner_width', 'inner_height')
        else:
            l, w, h = _get_dimension_triplet(item, 'length', 'width', 'height')

        # Rotation allowed: sort item dimensions ascending
        sorted_item_dims = tuple(sorted([l, w, h]))
        item_volume = l * w * h

        total_order_weight += weight * qty
        total_order_volume += item_volume * qty

        normalized_items.append({
            'name': item_name,
            'dims': sorted_item_dims,
            'weight': weight,
            'quantity': qty,
            'volume': item_volume,
        })

    if not normalized_items:
        return BoxSelectionResult(
            recommended_box=None,
            reason="All order items have zero or non-positive quantity.",
            rejected_boxes=[]
        )

    passing_boxes = []

    for box in boxes:
        # Extract box dimensions
        if hasattr(box, 'inner_length') or (isinstance(box, dict) and 'inner_length' in box):
            bl, bw, bh = _get_dimension_triplet(box, 'inner_length', 'inner_width', 'inner_height')
        else:
            bl, bw, bh = _get_dimension_triplet(box, 'length', 'width', 'height')

        box_dims = tuple(sorted([bl, bw, bh]))
        box_volume = bl * bw * bh
        box_max_weight = Decimal(str(_get_attr(box, 'max_weight', 0)))
        box_cost = Decimal(str(_get_attr(box, 'cost', 0)))
        box_name = str(_get_attr(box, 'name', 'Unnamed Box'))

        # Check 1: Individual item dimension fit (with rotation allowed)
        item_too_large = None
        for item in normalized_items:
            idims = item['dims']
            if idims[0] > box_dims[0] or idims[1] > box_dims[1] or idims[2] > box_dims[2]:
                item_too_large = item
                break

        if item_too_large is not None:
            rejected_boxes.append(RejectedBox(
                box=box,
                reason=(
                    f"Item '{item_too_large['name']}' with dimensions "
                    f"{item_too_large['dims'][0]}x{item_too_large['dims'][1]}x{item_too_large['dims'][2]} cm "
                    f"exceeds box dimensions {box_dims[0]}x{box_dims[1]}x{box_dims[2]} cm."
                )
            ))
            continue

        # Check 2: Total weight capacity
        if total_order_weight > box_max_weight:
            rejected_boxes.append(RejectedBox(
                box=box,
                reason=(
                    f"Total order weight ({total_order_weight}) exceeds "
                    f"box max weight capacity ({box_max_weight})."
                )
            ))
            continue

        # Check 3: Total volume capacity
        if total_order_volume > box_volume:
            rejected_boxes.append(RejectedBox(
                box=box,
                reason=(
                    f"Total order volume ({total_order_volume:.2f} cm³) exceeds "
                    f"box inner volume ({box_volume:.2f} cm³)."
                )
            ))
            continue

        # Passed all criteria
        passing_boxes.append({
            'box': box,
            'cost': box_cost,
            'volume': box_volume,
            'name': box_name,
        })

    if not passing_boxes:
        return BoxSelectionResult(
            recommended_box=None,
            reason="No suitable box found: all candidate boxes were rejected.",
            rejected_boxes=rejected_boxes
        )

    # Pick the cheapest. Break ties by smallest volume, then by name.
    passing_boxes.sort(key=lambda candidate: (
        candidate['cost'],
        candidate['volume'],
        candidate['name']
    ))

    winner = passing_boxes[0]
    reason = (
        f"Selected '{winner['name']}' as the cheapest suitable box "
        f"(Cost: ${winner['cost']:.2f}, Volume: {winner['volume']:.2f} cm³)."
    )

    return BoxSelectionResult(
        recommended_box=winner['box'],
        reason=reason,
        rejected_boxes=rejected_boxes
    )
