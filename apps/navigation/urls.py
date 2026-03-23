from django.urls import path
from .views import (
    landing_view,
    scan_view, scan_by_id_view,
    market_map_view,
    search_view, search_results_view,
)

urlpatterns = [
    path("",                             landing_view,        name="landing"),
    path("scan/<uuid:qr_id>/",           scan_view,           name="node-scan-web"),
    path("scan/node/<int:node_id>/",     scan_by_id_view,     name="node-scan-by-id"),
    path("market/<slug:slug>/map/",      market_map_view,     name="market-map"),
    path("search/",                      search_view,         name="search"),
    path("search/results/",              search_results_view, name="search-results"),
]