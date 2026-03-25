"""
apps/vendors/portal_urls.py

URL patterns for the vendor self-service portal.
Included in config/urls.py under the /portal/ prefix.
"""

from django.urls import path
from . import portal_views

urlpatterns = [
    # Auth
    path("login/",  portal_views.portal_login,  name="portal-login"),
    path("logout/", portal_views.portal_logout, name="portal-logout"),

    # Main portal pages
    path("dashboard/", portal_views.portal_dashboard, name="portal-dashboard"),
    path("profile/",   portal_views.portal_profile,   name="portal-profile"),

    # Products
    path("products/",                        portal_views.portal_products,       name="portal-products"),
    path("products/add/",                    portal_views.portal_product_add,    name="portal-product-add"),
    path("products/<int:product_id>/edit/",  portal_views.portal_product_edit,   name="portal-product-edit"),
    path("products/<int:product_id>/delete/",portal_views.portal_product_delete, name="portal-product-delete"),

    # HTMX endpoint
    path("products/<int:product_id>/toggle/",portal_views.portal_product_toggle, name="portal-product-toggle"),
]
