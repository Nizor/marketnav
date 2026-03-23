"""
apps/vendors/views.py
API views for Vendors and Products.
"""

from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Vendor, Product, ProductCategory
from .serializers import (
    VendorSerializer, VendorListSerializer,
    ProductSerializer, ProductCategorySerializer,
)


class VendorListView(generics.ListAPIView):
    """
    List all active vendors. Supports:
      ?search=<query>    — search by business name, category, product name
      ?market=<slug>     — filter by market slug
      ?category=<id>     — filter by category ID
    """
    serializer_class = VendorListSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["business_name", "owner_name", "categories__name", "products__name"]

    def get_queryset(self):
        qs = Vendor.objects.filter(is_active=True).prefetch_related("categories", "node")
        market_slug = self.request.query_params.get("market")
        category_id = self.request.query_params.get("category")
        if market_slug:
            qs = qs.filter(market__slug=market_slug)
        if category_id:
            qs = qs.filter(categories__id=category_id)
        return qs.distinct()


class VendorDetailView(generics.RetrieveAPIView):
    """Full vendor profile including products."""
    queryset = Vendor.objects.filter(is_active=True)
    serializer_class = VendorSerializer


class ProductCategoryListView(generics.ListAPIView):
    """List all product categories."""
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]
