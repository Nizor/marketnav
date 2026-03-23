"""
apps/markets/views.py
API views for Markets.
"""

from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Market, Zone, Node
from .serializers import (
    MarketSerializer, MarketDetailSerializer,
    ZoneSerializer, NodeSerializer,
)


class MarketListView(generics.ListAPIView):
    """List all active markets."""
    queryset = Market.objects.filter(is_active=True).prefetch_related("zones")
    serializer_class = MarketSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "city", "state"]


class MarketDetailView(generics.RetrieveAPIView):
    """Full market detail including nodes and edges (for map rendering)."""
    queryset = Market.objects.filter(is_active=True)
    serializer_class = MarketDetailSerializer
    lookup_field = "slug"


class MarketNodesView(generics.ListAPIView):
    """All active nodes for a given market."""
    serializer_class = NodeSerializer

    def get_queryset(self):
        market = get_object_or_404(Market, slug=self.kwargs["slug"], is_active=True)
        return Node.objects.filter(market=market, is_active=True).select_related("zone")


class NodeScanView(APIView):
    """
    Resolves a QR scan: given a node's qr_id, returns the node's
    location data and market context. This is the entry point for
    the visitor navigation flow.
    """

    def get(self, request, qr_id):
        node = get_object_or_404(Node, qr_id=qr_id, is_active=True)
        market = node.market
        return Response({
            "current_node": NodeSerializer(node).data,
            "market": MarketSerializer(market).data,
        })
