"""
apps/vendors/serializers.py
DRF serializers for Vendor, Product, ProductCategory.
"""

from rest_framework import serializers
from .models import Vendor, Product, ProductCategory


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ["id", "name", "icon", "description"]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "category", "category_name", "is_available"]


class VendorSerializer(serializers.ModelSerializer):
    categories = ProductCategorySerializer(many=True, read_only=True)
    node_label = serializers.CharField(source="node.label", read_only=True)
    whatsapp_url = serializers.CharField(read_only=True)
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Vendor
        fields = [
            "id", "business_name", "owner_name", "description",
            "phone", "whatsapp", "whatsapp_url", "email",
            "logo", "node", "node_label", "market",
            "categories", "products", "is_active",
        ]


class VendorListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views — excludes full product list."""
    categories = ProductCategorySerializer(many=True, read_only=True)
    node_label = serializers.CharField(source="node.label", read_only=True)

    class Meta:
        model = Vendor
        fields = [
            "id", "business_name", "owner_name",
            "phone", "whatsapp", "node", "node_label",
            "categories", "is_active",
        ]
