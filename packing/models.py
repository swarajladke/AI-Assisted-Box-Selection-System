from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


def validate_strictly_positive(value):
    """Ensure value is strictly greater than 0."""
    if value is not None and value <= 0:
        raise ValidationError("Value must be strictly greater than 0.")


class Product(models.Model):
    name = models.CharField(max_length=255)
    length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[validate_strictly_positive],
        help_text="Length in cm (must be > 0)"
    )
    width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[validate_strictly_positive],
        help_text="Width in cm (must be > 0)"
    )
    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[validate_strictly_positive],
        help_text="Height in cm (must be > 0)"
    )
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[validate_strictly_positive],
        help_text="Weight in grams (must be > 0)"
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.length}x{self.width}x{self.height} cm, {self.weight}g)"

    @property
    def volume(self):
        return self.length * self.width * self.height


class Box(models.Model):
    name = models.CharField(max_length=255)
    inner_length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[validate_strictly_positive],
        help_text="Internal length in cm (must be > 0)"
    )
    inner_width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[validate_strictly_positive],
        help_text="Internal width in cm (must be > 0)"
    )
    inner_height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[validate_strictly_positive],
        help_text="Internal height in cm (must be > 0)"
    )
    max_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[validate_strictly_positive],
        help_text="Maximum allowed weight in grams (must be > 0)"
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Box procurement/shipping cost (must be >= 0)"
    )

    class Meta:
        verbose_name_plural = "Boxes"
        ordering = ['cost', 'name']

    def __str__(self):
        return f"{self.name} (${self.cost}, max {self.max_weight}g)"

    @property
    def inner_volume(self):
        return self.inner_length * self.inner_width * self.inner_height


class Order(models.Model):
    order_number = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number}"

    @property
    def total_weight(self):
        return sum(item.total_weight for item in self.items.all())

    @property
    def total_volume(self):
        return sum(item.total_volume for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        related_name='order_items',
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Quantity must be at least 1"
    )

    class Meta:
        unique_together = ('order', 'product')

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Order #{self.order.order_number})"

    @property
    def total_weight(self):
        return self.product.weight * self.quantity

    @property
    def total_volume(self):
        return self.product.volume * self.quantity
