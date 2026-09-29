from django.contrib import admin
from .models import Product, Box, Order, OrderItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'length', 'width', 'height', 'weight', 'volume_display')
    search_fields = ('name',)
    list_filter = ()

    @admin.display(description="Volume (cm³)")
    def volume_display(self, obj):
        return f"{obj.volume:.2f}"


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = ('name', 'inner_length', 'inner_width', 'inner_height', 'max_weight', 'cost', 'inner_volume_display')
    list_filter = ()
    search_fields = ('name',)
    ordering = ('cost',)

    @admin.display(description="Inner Volume (cm³)")
    def inner_volume_display(self, obj):
        return f"{obj.inner_volume:.2f}"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    min_num = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'created_at', 'total_items_count', 'total_weight_display')
    search_fields = ('order_number',)
    inlines = [OrderItemInline]

    @admin.display(description="Total Items")
    def total_items_count(self, obj):
        return sum(item.quantity for item in obj.items.all())

    @admin.display(description="Total Weight")
    def total_weight_display(self, obj):
        return f"{obj.total_weight:.2f}"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'total_weight', 'total_volume')
    list_filter = ('product',)
    search_fields = ('order__order_number', 'product__name')
