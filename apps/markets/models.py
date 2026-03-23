"""
apps/markets/models.py

Core market structure models:
  Market → Zone → Node

Nodes are the atomic units of the indoor navigation graph.
Each Node gets a unique QR code that visitors scan to identify their location.
"""

import uuid
from django.db import models
from django.utils.text import slugify


class Market(models.Model):
    """
    Top-level container representing a physical indoor market.
    A city can have multiple markets.
    """

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    address = models.TextField(blank=True)

    # Map image uploaded by admin (SVG or raster)
    map_image = models.ImageField(
        upload_to="maps/",
        blank=True,
        null=True,
        help_text="Upload an SVG or image of the market floor plan.",
    )

    # Coordinate system metadata for the map image
    map_width = models.PositiveIntegerField(
        default=1000,
        help_text="Logical width of the map coordinate space (e.g. pixels or metres).",
    )
    map_height = models.PositiveIntegerField(
        default=1000,
        help_text="Logical height of the map coordinate space.",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Market"
        verbose_name_plural = "Markets"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.city}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.city}, {self.state})"


class Zone(models.Model):
    """
    A named section or aisle within a Market.
    Examples: 'Foodstuffs Section', 'Electronics Aisle', 'Zone A'.
    Zones group related nodes together for easier navigation display.
    """

    market = models.ForeignKey(
        Market, on_delete=models.CASCADE, related_name="zones"
    )
    name = models.CharField(max_length=150)
    code = models.CharField(
        max_length=20,
        blank=True,
        help_text="Short code used in direction instructions, e.g. 'ZA', 'FOOD'.",
    )
    description = models.TextField(blank=True)
    color_hex = models.CharField(
        max_length=7,
        default="#AED6F1",
        help_text="Hex colour for rendering this zone on the SVG map overlay.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["market", "name"]
        unique_together = [("market", "name")]
        verbose_name = "Zone"
        verbose_name_plural = "Zones"

    def __str__(self):
        return f"{self.name} — {self.market.name}"


class NodeType(models.TextChoices):
    STALL = "stall", "Vendor Stall"
    INTERSECTION = "intersection", "Aisle Intersection"
    ENTRANCE = "entrance", "Market Entrance"
    EXIT = "exit", "Exit"
    AMENITY = "amenity", "Amenity (toilet, ATM, etc.)"


class Node(models.Model):
    """
    A single navigable point on the market graph.

    Nodes represent physical locations that can be:
      - Vendor stalls (scannable QR installed at the stall)
      - Aisle intersections (waypoints for routing, QR optional)
      - Entrances / exits
      - Amenities

    Coordinates (x, y) are in the market's logical map space
    (matching map_width / map_height on Market).
    """

    market = models.ForeignKey(
        Market, on_delete=models.CASCADE, related_name="nodes"
    )
    zone = models.ForeignKey(
        Zone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nodes",
    )

    # Unique identifier used in QR codes: /scan/<qr_id>
    qr_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    label = models.CharField(
        max_length=100,
        help_text="Human-readable label, e.g. 'Stall 24', 'Entrance A', 'Junction B3'.",
    )
    node_type = models.CharField(
        max_length=20,
        choices=NodeType.choices,
        default=NodeType.STALL,
    )

    # Position on the market map (logical coordinates)
    x = models.FloatField(default=0.0, help_text="Horizontal position on the map.")
    y = models.FloatField(default=0.0, help_text="Vertical position on the map.")

    # QR code image (generated and stored on demand)
    qr_image = models.ImageField(
        upload_to="qr_codes/",
        blank=True,
        null=True,
        editable=False,
    )

    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["market", "label"]
        verbose_name = "Node"
        verbose_name_plural = "Nodes"

    def __str__(self):
        return f"{self.label} ({self.market.name})"

    @property
    def scan_url_path(self):
        """Returns the relative URL path encoded in this node's QR code."""
        return f"/scan/{self.qr_id}/"


class Edge(models.Model):
    """
    A walkable path (edge) between two Nodes in the same Market.

    The graph is treated as undirected: an Edge from A→B is also traversable B→A.
    Weight is the walking distance in metres between the two nodes.
    """

    market = models.ForeignKey(
        Market, on_delete=models.CASCADE, related_name="edges"
    )
    node_from = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="edges_from"
    )
    node_to = models.ForeignKey(
        Node, on_delete=models.CASCADE, related_name="edges_to"
    )
    weight = models.FloatField(
        default=1.0,
        help_text="Walking distance in metres between the two nodes.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("node_from", "node_to")]
        verbose_name = "Edge (Path)"
        verbose_name_plural = "Edges (Paths)"

    def __str__(self):
        return f"{self.node_from.label} ↔ {self.node_to.label} ({self.weight}m)"
