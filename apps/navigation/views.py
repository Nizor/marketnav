"""
apps/navigation/views.py  (Phase 2 - full web + API views)
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Q

from apps.markets.models import Market, Node, Edge
from apps.vendors.models import Vendor, ProductCategory
from apps.vendors.serializers import VendorListSerializer


# ── API Views ────────────────────────────────────────────────────────

class RouteView(APIView):
    def post(self, request):
        market_slug = request.data.get("market_slug")
        from_id     = request.data.get("from_node_id")
        to_id       = request.data.get("to_node_id")

        if not all([market_slug, from_id, to_id]):
            return Response({"error": "market_slug, from_node_id, and to_node_id are required."}, status=400)

        market = get_object_or_404(Market, slug=market_slug, is_active=True)
        try:
            from_id, to_id = int(from_id), int(to_id)
        except (TypeError, ValueError):
            return Response({"error": "Node IDs must be integers."}, status=400)

        from .routing import MarketGraph
        graph  = MarketGraph(market)
        result = graph.route(from_id, to_id)
        return Response(result, status=200 if result["found"] else 404)


class SearchAPIView(APIView):
    def get(self, request):
        query       = request.query_params.get("q", "").strip()
        market_slug = request.query_params.get("market", "").strip()
        if not query:
            return Response({"error": "q is required."}, status=400)

        qs = Vendor.objects.filter(is_active=True).prefetch_related("categories", "node")
        if market_slug:
            qs = qs.filter(market__slug=market_slug)
        qs = qs.filter(
            Q(business_name__icontains=query)
            | Q(categories__name__icontains=query)
            | Q(products__name__icontains=query)
            | Q(node__label__icontains=query)
        ).distinct()

        return Response({"query": query, "count": qs.count(), "results": VendorListSerializer(qs, many=True).data})


# ── Web Views ────────────────────────────────────────────────────────

def scan_view(request, qr_id):
    """QR scan landing page — identifies current location."""
    node   = get_object_or_404(Node, qr_id=qr_id, is_active=True)
    market = node.market
    vendor = getattr(node, "vendor", None)
    all_nodes = Node.objects.filter(market=market, is_active=True).select_related("zone")
    edges     = Edge.objects.filter(market=market, is_active=True).select_related("node_from", "node_to")
    return render(request, "navigation/scan.html", {
        "node": node, "market": market, "vendor": vendor,
        "all_nodes": all_nodes, "edges": edges,
    })


def scan_by_id_view(request, node_id):
    """Redirect integer node ID to QR scan view (used by map tooltip)."""
    node = get_object_or_404(Node, id=node_id, is_active=True)
    return redirect("node-scan-web", qr_id=node.qr_id)


def market_map_view(request, slug):
    """Full interactive SVG map."""
    market = get_object_or_404(Market, slug=slug, is_active=True)
    from_node_id = request.GET.get("from")

    from_node = None
    if from_node_id:
        try:
            from_node = Node.objects.select_related("zone").get(
                id=int(from_node_id), market=market, is_active=True)
        except (Node.DoesNotExist, ValueError):
            pass

    nodes = Node.objects.filter(market=market, is_active=True).select_related("zone").prefetch_related("vendor")
    edges = Edge.objects.filter(market=market, is_active=True).select_related("node_from", "node_to")
    return render(request, "navigation/map.html", {
        "market": market, "nodes": nodes, "edges": edges,
        "from_node": from_node, "to_node_id": request.GET.get("to"),
    })


def search_view(request):
    """Search page — full page load."""
    market_slug  = request.GET.get("market", "")
    from_node_id = request.GET.get("from", "")
    market = None
    if market_slug:
        try:
            market = Market.objects.get(slug=market_slug, is_active=True)
        except Market.DoesNotExist:
            pass
    categories = ProductCategory.objects.all()
    return render(request, "navigation/search.html", {
        "market": market, "market_slug": market_slug,
        "from_node_id": from_node_id, "categories": categories,
    })


def search_results_view(request):
    """HTMX partial — returns search results fragment."""
    query        = request.GET.get("q", "").strip()
    market_slug  = request.GET.get("market", "").strip()
    from_node_id = request.GET.get("from", "")
    category_id  = request.GET.get("category", "")

    market_obj  = None
    market_name = market_slug
    if market_slug:
        try:
            market_obj  = Market.objects.get(slug=market_slug)
            market_name = market_obj.name
        except Market.DoesNotExist:
            pass

    qs = Vendor.objects.filter(is_active=True).select_related("market", "node__zone").prefetch_related("categories", "products")
    if market_obj:
        qs = qs.filter(market=market_obj)
    if category_id:
        try:
            qs = qs.filter(categories__id=int(category_id))
        except ValueError:
            pass
    if query:
        qs = qs.filter(
            Q(business_name__icontains=query)
            | Q(owner_name__icontains=query)
            | Q(categories__name__icontains=query)
            | Q(products__name__icontains=query)
            | Q(node__label__icontains=query)
            | Q(description__icontains=query)
        ).distinct()
    elif not category_id:
        qs = qs[:20]

    return render(request, "navigation/partials/search_results.html", {
        "vendors": qs, "query": query, "market_slug": market_slug,
        "market_name": market_name, "from_node_id": from_node_id,
    })


def landing_view(request):
    """Homepage — lists all active markets with stats."""
    from apps.markets.models import Market
    from apps.vendors.models import Vendor

    markets_qs = Market.objects.filter(is_active=True).prefetch_related("zones", "nodes", "vendors")

    # Annotate with counts
    markets = []
    for m in markets_qs:
        m.node_count   = m.nodes.filter(is_active=True).count()
        m.vendor_count = m.vendors.filter(is_active=True).count()
        m.zone_count   = m.zones.count()
        markets.append(m)

    total_vendors = Vendor.objects.filter(is_active=True).count()

    return render(request, "landing.html", {
        "markets": markets,
        "total_vendors": total_vendors,
    })