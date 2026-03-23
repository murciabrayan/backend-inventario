from datetime import datetime, time

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .filters import MovementFilter, ProductFilter, UserFilter
from .models import Category, InventoryMovement, Product, User
from .permissions import IsAdminOrReadOnly, IsAdminRole
from .serializers import (
    CategorySerializer,
    DashboardSummarySerializer,
    LoginSerializer,
    MovementSerializer,
    MovementReportSerializer,
    ProductSerializer,
    RegisterUserSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-created_at")
    permission_classes = [IsAuthenticated, IsAdminRole]
    filterset_class = UserFilter
    search_fields = ["name", "email"]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return RegisterUserSerializer
        if self.action in {"partial_update", "update"}:
            return UserUpdateSerializer
        return UserSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    search_fields = ["name", "description"]
    http_method_names = ["get", "post", "put", "delete", "head", "options"]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filterset_class = ProductFilter
    search_fields = ["name", "sku", "description"]
    ordering_fields = ["name", "price", "stock", "created_at", "updated_at"]
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated, IsAdminRole])
    def deactivate(self, request, pk=None):
        product = self.get_object()
        product.is_active = False
        product.save(update_fields=["is_active", "updated_at"])
        return Response(ProductSerializer(product).data)


class MovementViewSet(viewsets.ModelViewSet):
    serializer_class = MovementSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = MovementFilter
    search_fields = ["product__name", "product__sku", "note", "user__name", "user__email"]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = InventoryMovement.objects.select_related("product", "user").all()
        if self.request.user.role == User.Roles.ADMIN:
            return queryset
        return queryset.filter(user=self.request.user)


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        recent_movements = InventoryMovement.objects.select_related("product", "user")[:10]
        payload = {
            "total_products": Product.objects.count(),
            "low_stock_products": Product.objects.filter(stock__lte=F("minimum_stock")).count(),
            "total_categories": Category.objects.count(),
            "recent_movements": recent_movements,
        }
        serializer = DashboardSummarySerializer(payload)
        return Response(serializer.data)


class MovementReportView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        movement_type = request.query_params.get("movement_type")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        queryset = InventoryMovement.objects.select_related("product", "user").all()

        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)

        applied_filters = {
            "movement_type": movement_type or "",
            "start_date": start_date or "",
            "end_date": end_date or "",
        }

        if start_date:
            start_dt = self._to_aware_datetime(start_date, is_end=False)
            queryset = queryset.filter(created_at__gte=start_dt)
        if end_date:
            end_dt = self._to_aware_datetime(end_date, is_end=True)
            queryset = queryset.filter(created_at__lte=end_dt)

        type_summary_queryset = (
            queryset.values("movement_type")
            .annotate(
                total_quantity=Sum("quantity"),
                movement_count=Count("id"),
            )
            .order_by("movement_type")
        )

        daily_summary_queryset = (
            queryset.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(
                total_quantity=Sum("quantity"),
                movement_count=Count("id"),
            )
            .order_by("day")
        )

        payload = {
            "applied_filters": applied_filters,
            "total_movements": queryset.count(),
            "total_quantity": queryset.aggregate(total=Sum("quantity"))["total"] or 0,
            "type_summary": [
                {
                    "movement_type": item["movement_type"],
                    "total_quantity": item["total_quantity"] or 0,
                    "movement_count": item["movement_count"],
                }
                for item in type_summary_queryset
            ],
            "daily_summary": [
                {
                    "label": item["day"].isoformat(),
                    "total_quantity": item["total_quantity"] or 0,
                    "movement_count": item["movement_count"],
                }
                for item in daily_summary_queryset
            ],
            "movements": queryset.order_by("-created_at")[:200],
        }

        serializer = MovementReportSerializer(payload)
        return Response(serializer.data)

    def _to_aware_datetime(self, raw_date, is_end):
        parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
        combined = datetime.combine(parsed_date, time.max if is_end else time.min)
        if timezone.is_naive(combined):
            return timezone.make_aware(combined, timezone.get_current_timezone())
        return combined
