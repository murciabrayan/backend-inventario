from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    DashboardSummaryView,
    LoginView,
    MeView,
    MovementViewSet,
    MovementReportView,
    ProductViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("categories", CategoryViewSet, basename="categories")
router.register("products", ProductViewSet, basename="products")
router.register("movements", MovementViewSet, basename="movements")

urlpatterns = [
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/me", MeView.as_view(), name="auth-me"),
    path("dashboard/summary", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("reports/movements", MovementReportView.as_view(), name="movement-reports"),
    path("", include(router.urls)),
]
