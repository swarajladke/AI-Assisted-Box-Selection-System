from django.urls import path
from .views import recommend_box_api, staff_packing_view

urlpatterns = [
    # Warehouse staff UI
    path('', staff_packing_view, name='staff_packing'),

    # JSON recommendation API
    path('api/orders/<int:id>/recommend-box/', recommend_box_api, name='api_recommend_box'),
]
