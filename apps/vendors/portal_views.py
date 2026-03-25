"""
apps/vendors/portal_views.py

Vendor self-service portal views.

URL prefix: /portal/

Routes:
  GET/POST  /portal/login/              — vendor login
  POST      /portal/logout/             — logout
  GET       /portal/dashboard/          — overview (stats, stall info)
  GET/POST  /portal/profile/            — edit business profile
  GET       /portal/products/           — list own products
  GET/POST  /portal/products/add/       — add product
  GET/POST  /portal/products/<id>/edit/ — edit product
  POST      /portal/products/<id>/delete/ — delete product
"""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from .models import Vendor, Product, ProductCategory
from .portal_forms import (
    VendorLoginForm,
    VendorProfileForm,
    ProductForm,
)


# ── Helpers ───────────────────────────────────────────────────────

def get_vendor_or_403(user):
    """Return the vendor profile for this user, or raise 403."""
    try:
        return user.vendor_profile
    except Vendor.DoesNotExist:
        return None


# ── Auth ──────────────────────────────────────────────────────────

def portal_login(request):
    """Vendor login page."""
    # Already logged in and has a vendor profile → go to dashboard
    if request.user.is_authenticated and get_vendor_or_403(request.user):
        return redirect("portal-dashboard")

    form = VendorLoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            vendor = get_vendor_or_403(user)
            if vendor and vendor.is_active:
                login(request, user)
                next_url = request.GET.get("next", "portal-dashboard")
                return redirect(next_url)
            elif vendor and not vendor.is_active:
                form.add_error(None, "Your vendor account has been deactivated. Contact market management.")
            else:
                form.add_error(None, "This account is not linked to a vendor profile.")
        else:
            form.add_error(None, "Incorrect username or password.")

    return render(request, "portal/login.html", {"form": form})


@require_POST
def portal_logout(request):
    """Log out and redirect to login."""
    logout(request)
    return redirect("portal-login")


# ── Dashboard ─────────────────────────────────────────────────────

@login_required(login_url="portal-login")
def portal_dashboard(request):
    """Vendor dashboard — overview of profile, stall, recent stats."""
    vendor = get_vendor_or_403(request.user)
    if not vendor:
        return HttpResponseForbidden("No vendor profile linked to this account.")

    products = vendor.products.select_related("category").order_by("-created_at")
    product_count = products.count()
    available_count = products.filter(is_available=True).count()

    # Recent products (last 3)
    recent_products = products[:3]

    context = {
        "vendor": vendor,
        "product_count": product_count,
        "available_count": available_count,
        "recent_products": recent_products,
        "stall_node": vendor.node,
        "market": vendor.market,
    }
    return render(request, "portal/dashboard.html", context)


# ── Profile ───────────────────────────────────────────────────────

@login_required(login_url="portal-login")
def portal_profile(request):
    """Edit vendor business profile."""
    vendor = get_vendor_or_403(request.user)
    if not vendor:
        return HttpResponseForbidden()

    form = VendorProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=vendor,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("portal-profile")

    return render(request, "portal/profile.html", {"form": form, "vendor": vendor})


# ── Products ──────────────────────────────────────────────────────

@login_required(login_url="portal-login")
def portal_products(request):
    """List all products for this vendor."""
    vendor = get_vendor_or_403(request.user)
    if not vendor:
        return HttpResponseForbidden()

    products = (
        vendor.products
        .select_related("category")
        .order_by("category__name", "name")
    )
    categories = ProductCategory.objects.filter(
        products__vendor=vendor
    ).distinct()

    context = {
        "vendor": vendor,
        "products": products,
        "categories": categories,
        "product_count": products.count(),
    }
    return render(request, "portal/products.html", context)


@login_required(login_url="portal-login")
def portal_product_add(request):
    """Add a new product."""
    vendor = get_vendor_or_403(request.user)
    if not vendor:
        return HttpResponseForbidden()

    form = ProductForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        product.vendor = vendor
        product.save()
        messages.success(request, f"'{product.name}' added to your listings.")
        return redirect("portal-products")

    return render(request, "portal/product_form.html", {
        "form": form,
        "vendor": vendor,
        "action": "Add",
    })


@login_required(login_url="portal-login")
def portal_product_edit(request, product_id):
    """Edit an existing product."""
    vendor = get_vendor_or_403(request.user)
    if not vendor:
        return HttpResponseForbidden()

    product = get_object_or_404(Product, id=product_id, vendor=vendor)
    form = ProductForm(request.POST or None, instance=product)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"'{product.name}' updated.")
        return redirect("portal-products")

    return render(request, "portal/product_form.html", {
        "form": form,
        "vendor": vendor,
        "product": product,
        "action": "Edit",
    })


@login_required(login_url="portal-login")
@require_POST
def portal_product_delete(request, product_id):
    """Delete a product (POST only)."""
    vendor = get_vendor_or_403(request.user)
    if not vendor:
        return HttpResponseForbidden()

    product = get_object_or_404(Product, id=product_id, vendor=vendor)
    name = product.name
    product.delete()
    messages.success(request, f"'{name}' removed from your listings.")
    return redirect("portal-products")


# ── HTMX: toggle product availability ────────────────────────────

@login_required(login_url="portal-login")
@require_POST
def portal_product_toggle(request, product_id):
    """HTMX endpoint — toggle product availability inline."""
    vendor = get_vendor_or_403(request.user)
    if not vendor:
        return HttpResponseForbidden()

    product = get_object_or_404(Product, id=product_id, vendor=vendor)
    product.is_available = not product.is_available
    product.save(update_fields=["is_available"])

    return render(request, "portal/partials/product_row.html", {
        "product": product,
        "vendor": vendor,
    })
