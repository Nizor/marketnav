from django.urls import path
from .views import RouteView, SearchAPIView

urlpatterns = [
    path("route/",  RouteView.as_view(),     name="route"),
    path("search/", SearchAPIView.as_view(), name="api-search"),
]
