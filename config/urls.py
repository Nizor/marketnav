from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "MarketNav Admin"
admin.site.site_title  = "MarketNav"
admin.site.index_title = "Market Navigation & Vendor Management"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.navigation.urls")),
    path("", include("apps.markets.urls")),
    path("api/v1/markets/",    include("apps.markets.api_urls")),
    path("api/v1/vendors/",    include("apps.vendors.api_urls")),
    path("api/v1/navigation/", include("apps.navigation.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)