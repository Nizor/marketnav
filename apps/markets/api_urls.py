from django.urls import path
from .views import MarketListView, MarketDetailView, MarketNodesView

urlpatterns = [
    path("", MarketListView.as_view(), name="market-list"),
    path("<slug:slug>/", MarketDetailView.as_view(), name="market-detail"),
    path("<slug:slug>/nodes/", MarketNodesView.as_view(), name="market-nodes"),
]
