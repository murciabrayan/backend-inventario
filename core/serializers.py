from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Category, InventoryMovement, Product, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "role", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["role", "is_active"]

    def update(self, instance, validated_data):
        role = validated_data.get("role")
        if role is not None:
            instance.is_staff = role == User.Roles.ADMIN

        return super().update(instance, validated_data)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "description",
            "price",
            "stock",
            "minimum_stock",
            "category",
            "category_name",
            "is_active",
            "is_low_stock",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_low_stock"]

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("El stock no puede ser negativo.")
        return value


class MovementSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)

    class Meta:
        model = InventoryMovement
        fields = [
            "id",
            "product",
            "product_name",
            "product_sku",
            "movement_type",
            "quantity",
            "note",
            "user",
            "user_id",
            "created_at",
        ]
        read_only_fields = ["id", "user", "user_id", "created_at"]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a cero.")
        return value

    def validate(self, attrs):
        movement_type = attrs.get("movement_type")
        quantity = attrs.get("quantity")
        product = attrs.get("product")

        if movement_type == InventoryMovement.MovementTypes.EXIT and product and quantity:
            if quantity > product.stock:
                raise serializers.ValidationError(
                    {"quantity": "No se puede registrar una salida mayor al stock disponible."}
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        product = Product.objects.select_for_update().get(pk=validated_data["product"].pk)
        movement_type = validated_data["movement_type"]
        quantity = validated_data["quantity"]

        if movement_type == InventoryMovement.MovementTypes.ENTRY:
            product.stock += quantity
        elif movement_type == InventoryMovement.MovementTypes.EXIT:
            if quantity > product.stock:
                raise serializers.ValidationError(
                    {"quantity": "No se puede registrar una salida mayor al stock disponible."}
                )
            product.stock -= quantity
        else:
            product.stock = quantity

        if product.stock < 0:
            raise serializers.ValidationError({"quantity": "El stock no puede quedar negativo."})

        product.full_clean()
        product.save()

        validated_data["product"] = product
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class DashboardSummarySerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()
    total_categories = serializers.IntegerField()
    recent_movements = MovementSerializer(many=True)


class MovementChartPointSerializer(serializers.Serializer):
    label = serializers.CharField()
    total_quantity = serializers.IntegerField()
    movement_count = serializers.IntegerField()


class MovementTypeSummarySerializer(serializers.Serializer):
    movement_type = serializers.CharField()
    total_quantity = serializers.IntegerField()
    movement_count = serializers.IntegerField()


class MovementReportSerializer(serializers.Serializer):
    applied_filters = serializers.DictField()
    total_movements = serializers.IntegerField()
    total_quantity = serializers.IntegerField()
    type_summary = MovementTypeSummarySerializer(many=True)
    daily_summary = MovementChartPointSerializer(many=True)
    movements = MovementSerializer(many=True)


class LoginSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["name"] = user.name
        token["role"] = user.role
        token["email"] = user.email
        return token

    def validate(self, attrs):
        credentials = {
            "email": attrs.get("email"),
            "password": attrs.get("password"),
        }
        user = authenticate(request=self.context.get("request"), **credentials)

        if user is None or not user.is_active:
            raise serializers.ValidationError("Credenciales inválidas.")

        refresh = self.get_token(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "name", "email", "password", "role", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.is_staff = user.role == User.Roles.ADMIN
        user.set_password(password)
        user.save()
        return user
