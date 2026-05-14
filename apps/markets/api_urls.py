from django.urls import path
from .views import MarketListView, MarketDetailView, MarketNodesView
from . import api_views

urlpatterns = [
    path("", MarketListView.as_view(), name="market-list"),
    path("<slug:slug>/", MarketDetailView.as_view(), name="market-detail"),
    path("<slug:slug>/nodes/", MarketNodesView.as_view(), name="market-nodes"),
    path("<slug:slug>/nodes/update-coordinates/", api_views.NodeUpdateCoordsView.as_view(), name="node-update-coords"),
    path("<slug:slug>/edges/create/", api_views.EdgeCreateView.as_view(), name="edge-create"),
    path("<slug:slug>/edges/<int:edge_id>/", api_views.EdgeDeleteView.as_view(), name="edge-delete"),
    path("<slug:slug>/nodes/create/", api_views.NodeCreateView.as_view(), name="node-create"),
]
