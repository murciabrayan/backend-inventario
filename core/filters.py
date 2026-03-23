import django_filters
from django.db import models

from .models import InventoryMovement, Product, User


class ProductFilter(django_filters.FilterSet):
    category = django_filters.NumberFilter(field_name="category_id")
    is_active = django_filters.BooleanFilter()
    low_stock = django_filters.BooleanFilter(method="filter_low_stock")

    class Meta:
        model = Product
        fields = ["category", "is_active", "low_stock"]

    def filter_low_stock(self, queryset, name, value):
        if value is None:
            return queryset
        if value:
            return queryset.filter(stock__lte=models.F("minimum_stock"))
        return queryset.filter(stock__gt=models.F("minimum_stock"))


class MovementFilter(django_filters.FilterSet):
    product = django_filters.NumberFilter(field_name="product_id")
    movement_type = django_filters.CharFilter()
    user = django_filters.NumberFilter(field_name="user_id")

    class Meta:
        model = InventoryMovement
        fields = ["product", "movement_type", "user"]


class UserFilter(django_filters.FilterSet):
    role = django_filters.CharFilter()
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = User
        fields = ["role", "is_active"]
