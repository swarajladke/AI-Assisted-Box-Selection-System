import json
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from .models import Order, Box
from .services import select_best_box


def _serialize_box(box):
    if not box:
        return None
    return {
        "id": box.id,
        "name": box.name,
        "cost": float(box.cost),
        "inner_length": float(box.inner_length),
        "inner_width": float(box.inner_width),
        "inner_height": float(box.inner_height),
        "inner_volume": float(box.inner_volume),
        "max_weight": float(box.max_weight),
    }


@csrf_exempt
def recommend_box_api(request, id):
    """
    POST /api/orders/<id>/recommend-box/
    Evaluates all available boxes for the specified order and returns the
    cheapest suitable box, or rejection reasons for all considered boxes.
    """
    if request.method != 'POST':
        return JsonResponse(
            {"error": f"Method {request.method} not allowed. Use POST."},
            status=405
        )

    # Validate order existence
    try:
        order = Order.objects.prefetch_related('items__product').get(pk=id)
    except Order.DoesNotExist:
        return JsonResponse(
            {"error": f"Order with ID {id} not found."},
            status=404
        )

    # Validate items exist in the order
    order_items = list(order.items.all())
    if not order_items:
        return JsonResponse(
            {
                "error": f"Order #{order.order_number} has no items to pack.",
                "order_id": order.id,
                "order_number": order.order_number,
            },
            status=400
        )

    # Retrieve all active boxes
    boxes = list(Box.objects.all())
    if not boxes:
        return JsonResponse(
            {
                "error": "No shipping boxes exist in the system to evaluate.",
                "order_id": order.id,
                "order_number": order.order_number,
            },
            status=400
        )

    # Prepare pure data for the service function (decoupled from DB)
    items_payload = [
        {
            "name": item.product.name,
            "length": item.product.length,
            "width": item.product.width,
            "height": item.product.height,
            "weight": item.product.weight,
            "quantity": item.quantity,
        }
        for item in order_items
    ]

    # Execute decoupled domain logic
    result = select_best_box(items=items_payload, boxes=boxes)

    # Return structured response with HTTP 200
    return JsonResponse({
        "status": "success",
        "order": {
            "id": order.id,
            "order_number": order.order_number,
            "total_items": sum(i.quantity for i in order_items),
            "total_weight": float(order.total_weight),
            "total_volume": float(order.total_volume),
        },
        "has_recommendation": result.has_recommendation,
        "recommended_box": _serialize_box(result.recommended_box),
        "reason": result.reason,
        "rejected_boxes": [
            {
                "id": getattr(r.box, 'id', None),
                "name": getattr(r.box, 'name', str(r.box)),
                "cost": float(getattr(r.box, 'cost', 0)),
                "reason": r.reason,
            }
            for r in result.rejected_boxes
        ]
    }, status=200)


def staff_packing_view(request):
    """
    Warehouse staff dashboard to pick an order and view real-time box recommendation.
    """
    orders = Order.objects.prefetch_related('items__product').all()
    selected_order_id = request.GET.get('order_id')
    selected_order = None
    recommendation_data = None
    error_message = None

    if selected_order_id:
        try:
            selected_order = Order.objects.prefetch_related('items__product').get(pk=selected_order_id)
            order_items = list(selected_order.items.all())
            boxes = list(Box.objects.all())

            if not order_items:
                error_message = f"Order #{selected_order.order_number} contains no items."
            elif not boxes:
                error_message = "No packaging boxes configured in the database."
            else:
                items_payload = [
                    {
                        "name": item.product.name,
                        "length": item.product.length,
                        "width": item.product.width,
                        "height": item.product.height,
                        "weight": item.product.weight,
                        "quantity": item.quantity,
                    }
                    for item in order_items
                ]
                result = select_best_box(items=items_payload, boxes=boxes)
                recommendation_data = {
                    "has_recommendation": result.has_recommendation,
                    "recommended_box": result.recommended_box,
                    "reason": result.reason,
                    "rejected_boxes": result.rejected_boxes,
                }
        except Order.DoesNotExist:
            error_message = f"Order #{selected_order_id} does not exist."

    context = {
        "orders": orders,
        "selected_order": selected_order,
        "recommendation": recommendation_data,
        "error_message": error_message,
    }
    return render(request, "packing/order_packing.html", context)
