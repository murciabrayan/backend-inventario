from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "admin", "Admin"
        EMPLOYEE = "employee", "Empleado"

    username = None
    first_name = None
    last_name = None

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.EMPLOYEE,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self) -> str:
        return self.email


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.IntegerField(default=0)
    minimum_stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def clean(self) -> None:
        if self.stock < 0:
            raise ValidationError({"stock": "El stock no puede ser negativo."})

    @property
    def is_low_stock(self) -> bool:
        return self.stock <= self.minimum_stock

    def __str__(self) -> str:
        return f"{self.name} ({self.sku})"


class InventoryMovement(models.Model):
    class MovementTypes(models.TextChoices):
        ENTRY = "entrada", "Entrada"
        EXIT = "salida", "Salida"
        ADJUSTMENT = "ajuste", "Ajuste"

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="movements",
    )
    movement_type = models.CharField(max_length=20, choices=MovementTypes.choices)
    quantity = models.IntegerField()
    note = models.TextField(blank=True)
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="movements",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self) -> None:
        if self.quantity <= 0:
            raise ValidationError({"quantity": "La cantidad debe ser mayor a cero."})

    def __str__(self) -> str:
        return f"{self.product} - {self.movement_type} ({self.quantity})"
