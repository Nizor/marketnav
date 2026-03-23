"""
apps/vendors/models.py

Vendor-facing models:
  ProductCategory  — shared lookup for what vendors sell
  Vendor           — a trader assigned to a Node in a Market
  Product          — optional product listing under a Vendor
"""

from django.db import models
from django.contrib.auth.models import User


class ProductCategory(models.Model):
    """
    Shared taxonomy of product categories (e.g. 'Foodstuffs', 'Electronics').
    Vendors tag themselves with one or more categories.
    """

    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional emoji or icon class for UI display, e.g. '🍅' or 'fa-apple-alt'.",
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Product Category"
        verbose_name_plural = "Product Categories"

    def __str__(self):
        return self.name


class Vendor(models.Model):
    """
    A trader assigned to a specific Node (stall) within a Market.

    One Node has at most one Vendor (OneToOne).
    Vendors can list multiple ProductCategories and an optional Product list.
    """

    # Auth: optional user account for vendor self-service login
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vendor_profile",
        help_text="Optional: link to a Django user account for vendor login.",
    )

    # Location
    node = models.OneToOneField(
        "markets.Node",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vendor",
        help_text="The stall/node this vendor occupies.",
    )
    market = models.ForeignKey(
        "markets.Market",
        on_delete=models.CASCADE,
        related_name="vendors",
    )

    # Identity
    business_name = models.CharField(max_length=200)
    owner_name = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True, help_text="Short description of what this vendor sells.")

    # Contact
    phone = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(
        max_length=20,
        blank=True,
        help_text="WhatsApp number (include country code, e.g. +234...)",
    )
    email = models.EmailField(blank=True)

    # Categories
    categories = models.ManyToManyField(
        ProductCategory,
        blank=True,
        related_name="vendors",
        help_text="What product categories this vendor sells.",
    )

    # Media
    logo = models.ImageField(upload_to="vendor_logos/", blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["business_name"]
        verbose_name = "Vendor"
        verbose_name_plural = "Vendors"

    def __str__(self):
        stall = self.node.label if self.node else "unassigned"
        return f"{self.business_name} ({stall})"

    @property
    def whatsapp_url(self):
        """Returns a wa.me link for direct WhatsApp chat."""
        if self.whatsapp:
            number = self.whatsapp.replace("+", "").replace(" ", "")
            return f"https://wa.me/{number}"
        return None


class Product(models.Model):
    """
    An item sold by a Vendor.
    MVP: simple name + optional price. Inventory & ecommerce extend this later.
    """

    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="products"
    )
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Price in Nigerian Naira (NGN). Optional for MVP.",
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["vendor", "name"]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return f"{self.name} — {self.vendor.business_name}"
