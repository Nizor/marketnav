# apps/markets/api_views.py

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Market, Node, Edge
from .serializers import (
    NodeCreateSerializer,
    NodeUpdateCoordsSerializer,
    EdgeCreateSerializer,
    EdgeSerializer,
)


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_staff


class NodeUpdateCoordsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def post(self, request, slug):
        market = get_object_or_404(Market, slug=slug, is_active=True)
        updates = request.data.get('nodes', [])
        serializer = NodeUpdateCoordsSerializer(data=updates, many=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        updated = 0
        for item in serializer.validated_data:
            node = get_object_or_404(Node, id=item['id'], market=market)
            node.x = item['x']
            node.y = item['y']
            node.save(update_fields=['x', 'y'])
            updated += 1
        return Response({'updated': updated})


class NodeCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def post(self, request, slug):
        market = get_object_or_404(Market, slug=slug, is_active=True)
        serializer = NodeCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        node = serializer.save(market=market)
        # return full node info so frontend can add it
        from .serializers import NodeSerializer
        return Response(NodeSerializer(node).data, status=201)


class EdgeCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def post(self, request, slug):
        market = get_object_or_404(Market, slug=slug, is_active=True)
        serializer = EdgeCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        node_from = get_object_or_404(Node, id=serializer.validated_data['node_from'], market=market)
        node_to   = get_object_or_404(Node, id=serializer.validated_data['node_to'], market=market)
        edge, created = Edge.objects.get_or_create(
            market=market, node_from=node_from, node_to=node_to,
            defaults={'weight': 1.0}
        )
        return Response(EdgeSerializer(edge).data, status=201 if created else 200)


class EdgeDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def delete(self, request, slug, edge_id):
        market = get_object_or_404(Market, slug=slug, is_active=True)
        edge = get_object_or_404(Edge, id=edge_id, market=market)
        edge.delete()
        return Response(status=204)