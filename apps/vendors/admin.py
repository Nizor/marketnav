"""
apps/vendors/admin.py
Admin configuration for ProductCategory, Vendor, Product.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import ProductCategory, Vendor, Product


class ProductInline(admin.TabularInline):
    model = Product
    extra = 1
    fields = ("name", "category", "price", "is_available")
    show_change_link = True


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "vendor_count", "product_count")
    search_fields = ("name",)

    def vendor_count(self, obj):
        return obj.vendors.count()
    vendor_count.short_description = "Vendors"

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Products"


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = (
        "business_name", "owner_name", "market", "stall_label",
        "phone", "category_list", "is_active",
    )
    list_filter = ("market", "is_active", "categories")
    search_fields = ("business_name", "owner_name", "phone", "whatsapp", "node__label")
    filter_horizontal = ("categories",)
    autocomplete_fields = ["node"]
    readonly_fields = ("whatsapp_link", "created_at", "updated_at")
    inlines = [ProductInline]

    fieldsets = (
        ("Business Info", {
            "fields": ("business_name", "owner_name", "description", "logo", "is_active")
        }),
        ("Market Location", {
            "fields": ("market", "node"),
            "description": "Assign this vendor to a market and specific node (stall).",
        }),
        ("Contact", {
            "fields": ("phone", "whatsapp", "whatsapp_link", "email")
        }),
        ("Categories", {
            "fields": ("categories",),
        }),
        ("Account", {
            "fields": ("user",),
            "classes": ("collapse",),
            "description": "Optional: link vendor to a Django user for self-service login.",
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def stall_label(self, obj):
        return obj.node.label if obj.node else "—"
    stall_label.short_description = "Stall"

    def category_list(self, obj):
        cats = obj.categories.all()[:3]
        names = ", ".join(c.name for c in cats)
        extra = obj.categories.count() - 3
        return f"{names} +{extra} more" if extra > 0 else names
    category_list.short_description = "Categories"

    def whatsapp_link(self, obj):
        url = obj.whatsapp_url
        if url:
            return format_html('<a href="{}" target="_blank">Open WhatsApp ↗</a>', url)
        return "—"
    whatsapp_link.short_description = "WhatsApp Link"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor", "category", "price", "is_available")
    list_filter = ("is_available", "category", "vendor__market")
    search_fields = ("name", "vendor__business_name", "category__name")
    autocomplete_fields = ["vendor"]
