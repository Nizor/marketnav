"""
apps/markets/serializers.py
DRF serializers for Market, Zone, Node, Edge.
"""

from rest_framework import serializers
from .models import Market, Zone, Node, Edge


class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ["id", "name", "code", "color_hex", "description"]


class NodeSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source="zone.name", read_only=True)
    node_type_display = serializers.CharField(source="get_node_type_display", read_only=True)
    scan_url = serializers.CharField(source="scan_url_path", read_only=True)

    class Meta:
        model = Node
        fields = [
            "id", "qr_id", "label", "node_type", "node_type_display",
            "zone", "zone_name", "x", "y", "scan_url",
            "description", "is_active",
        ]


class EdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edge
        fields = ["id", "node_from", "node_to", "weight", "is_active"]


class MarketSerializer(serializers.ModelSerializer):
    zones = ZoneSerializer(many=True, read_only=True)
    node_count = serializers.SerializerMethodField()

    class Meta:
        model = Market
        fields = [
            "id", "name", "slug", "city", "state", "address",
            "description", "map_width", "map_height",
            "is_active", "zones", "node_count",
        ]

    def get_node_count(self, obj):
        return obj.nodes.filter(is_active=True).count()


class MarketDetailSerializer(MarketSerializer):
    """Full market detail including all nodes and edges for map rendering."""
    nodes = NodeSerializer(many=True, read_only=True)
    edges = EdgeSerializer(many=True, read_only=True)

    class Meta(MarketSerializer.Meta):
        fields = MarketSerializer.Meta.fields + ["nodes", "edges"]
