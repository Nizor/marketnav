"""
apps/markets/admin.py

Admin configuration for Market, Zone, Node, Edge.
Includes inline editors, QR code generation action, and map preview.
"""

import io
import os
import qrcode
from django.contrib import admin
from django.utils.html import format_html
from django.core.files.base import ContentFile
from django.conf import settings

from .models import Market, Zone, Node, Edge


class ZoneInline(admin.TabularInline):
    model = Zone
    extra = 1
    fields = ("name", "code", "color_hex", "description")
    show_change_link = True


class NodeInline(admin.TabularInline):
    model = Node
    extra = 0
    fields = ("label", "node_type", "zone", "x", "y", "is_active")
    readonly_fields = ()
    show_change_link = True


class EdgeInline(admin.TabularInline):
    model = Edge
    fk_name = "node_from"
    extra = 1
    fields = ("node_to", "weight", "is_active")
    verbose_name = "Outgoing Path"
    verbose_name_plural = "Outgoing Paths (Edges)"


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "state", "zone_count", "node_count", "is_active", "created_at")
    list_filter = ("state", "is_active")
    search_fields = ("name", "city", "state")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at", "map_preview")
    inlines = [ZoneInline]

    fieldsets = (
        ("Market Info", {
            "fields": ("name", "slug", "city", "state", "address", "description", "is_active")
        }),
        ("Map Configuration", {
            "fields": ("map_image", "map_preview", "map_width", "map_height"),
            "description": "Upload a floor plan image (SVG recommended). Set width/height to match the coordinate space used for node positions.",
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def zone_count(self, obj):
        return obj.zones.count()
    zone_count.short_description = "Zones"

    def node_count(self, obj):
        return obj.nodes.count()
    node_count.short_description = "Nodes"

    def map_preview(self, obj):
        if obj.map_image:
            return format_html(
                '<img src="{}" style="max-width:400px; max-height:300px; border:1px solid #ccc; border-radius:4px;" />',
                obj.map_image.url,
            )
        return "No map uploaded."
    map_preview.short_description = "Map Preview"


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "market", "node_count", "color_preview", "created_at")
    list_filter = ("market",)
    search_fields = ("name", "code", "market__name")

    def node_count(self, obj):
        return obj.nodes.count()
    node_count.short_description = "Nodes"

    def color_preview(self, obj):
        return format_html(
            '<span style="display:inline-block;width:20px;height:20px;'
            'background:{};border:1px solid #999;border-radius:3px;"></span>',
            obj.color_hex,
        )
    color_preview.short_description = "Colour"


def generate_qr_codes(modeladmin, request, queryset):
    """Admin action: generate and save QR code images for selected nodes."""
    base_url = getattr(settings, "SITE_BASE_URL", "https://marketnav.ng")
    generated = 0
    for node in queryset:
        url = f"{base_url}/scan/{node.qr_id}/"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        filename = f"qr_{node.qr_id}.png"
        node.qr_image.save(filename, ContentFile(buffer.read()), save=True)
        generated += 1
    modeladmin.message_user(request, f"Generated QR codes for {generated} node(s).")

generate_qr_codes.short_description = "Generate QR codes for selected nodes"


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = (
        "label", "market", "zone", "node_type", "x", "y",
        "has_vendor", "qr_preview", "is_active",
    )
    list_filter = ("market", "zone", "node_type", "is_active")
    search_fields = ("label", "market__name", "zone__name", "qr_id")
    readonly_fields = ("qr_id", "qr_image_preview", "scan_url_display", "created_at", "updated_at")
    actions = [generate_qr_codes]
    inlines = [EdgeInline]

    fieldsets = (
        ("Location", {
            "fields": ("market", "zone", "label", "node_type", "description", "is_active")
        }),
        ("Map Coordinates", {
            "fields": ("x", "y"),
            "description": "Coordinates in the market's logical map space.",
        }),
        ("QR Code", {
            "fields": ("qr_id", "scan_url_display", "qr_image_preview"),
            "description": "QR codes are generated via the 'Generate QR codes' action. The QR encodes the scan URL below.",
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def has_vendor(self, obj):
        return hasattr(obj, "vendor")
    has_vendor.boolean = True
    has_vendor.short_description = "Vendor?"

    def qr_preview(self, obj):
        if obj.qr_image:
            return format_html(
                '<img src="{}" style="width:40px;height:40px;" />',
                obj.qr_image.url,
            )
        return "—"
    qr_preview.short_description = "QR"

    def qr_image_preview(self, obj):
        if obj.qr_image:
            return format_html(
                '<img src="{}" style="width:200px;height:200px;" />'
                '<br><a href="{}" download>Download QR PNG</a>',
                obj.qr_image.url,
                obj.qr_image.url,
            )
        return "No QR code yet. Use the 'Generate QR codes' action."
    qr_image_preview.short_description = "QR Code Image"

    def scan_url_display(self, obj):
        return format_html("<code>/scan/{}/</code>", obj.qr_id)
    scan_url_display.short_description = "Scan URL"


@admin.register(Edge)
class EdgeAdmin(admin.ModelAdmin):
    list_display = ("node_from", "node_to", "weight", "market", "is_active")
    list_filter = ("market", "is_active")
    search_fields = ("node_from__label", "node_to__label")
    autocomplete_fields = ["node_from", "node_to"]
