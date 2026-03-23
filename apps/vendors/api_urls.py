from django.urls import path
from .views import VendorListView, VendorDetailView, ProductCategoryListView

urlpatterns = [
    path("", VendorListView.as_view(), name="vendor-list"),
    path("<int:pk>/", VendorDetailView.as_view(), name="vendor-detail"),
    path("categories/", ProductCategoryListView.as_view(), name="category-list"),
]
