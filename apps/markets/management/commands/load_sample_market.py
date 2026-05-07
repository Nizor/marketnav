"""
Management command to load sample market data for testing.

Usage:
    python manage.py load_sample_market
"""

import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.markets.models import Market, Zone, Node, Edge
from apps.vendors.models import Vendor, Product, ProductCategory


class Command(BaseCommand):
    help = "Load sample Balogun Market data for testing"

    def handle(self, *args, **options):
        data_path = os.path.join(settings.BASE_DIR, "sample_market_data.json")

        if not os.path.exists(data_path):
            self.stdout.write(
                self.style.ERROR(f"Sample data file not found: {data_path}")
            )
            self.stdout.write("Generate it first with the data generation script.")
            return

        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.stdout.write("Loading sample market data...")

        # Create Market
        market_data = data["market"]
        market, created = Market.objects.get_or_create(
            slug=market_data["slug"],
            defaults={
                "name": market_data["name"],
                "city": market_data["city"],
                "state": market_data["state"],
                "description": market_data["description"],
                "address": market_data["address"],
                "map_width": market_data["map_width"],
                "map_height": market_data["map_height"],
                "real_width_m": market_data["real_width_m"],
                "real_height_m": market_data["real_height_m"],
                "is_active": market_data["is_active"],
            }
        )
        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} market: {market.name}"))

        # Create Product Categories
        category_map = {}
        for cat_data in data["categories"]:
            cat, created = ProductCategory.objects.get_or_create(
                name=cat_data["name"],
                defaults={
                    "icon": cat_data["icon"],
                    "description": cat_data["description"],
                }
            )
            category_map[cat_data["name"]] = cat
            self.stdout.write(f"  {'Created' if created else 'Found'} category: {cat.name}")

        # Create Zones
        zone_map = {}
        for zone_data in data["zones"]:
            zone, created = Zone.objects.get_or_create(
                market=market,
                name=zone_data["name"],
                defaults={
                    "code": zone_data["code"],
                    "color_hex": zone_data["color_hex"],
                    "description": zone_data["description"],
                }
            )
            zone_map[zone_data["name"]] = zone
            self.stdout.write(f"  {'Created' if created else 'Found'} zone: {zone.name}")

        # Create Nodes
        node_map = {}
        for node_data in data["nodes"]:
            zone = None
            if node_data["zone_idx"] is not None:
                zone_name = data["zones"][node_data["zone_idx"]]["name"]
                zone = zone_map.get(zone_name)

            node, created = Node.objects.get_or_create(
                market=market,
                label=node_data["label"],
                defaults={
                    "zone": zone,
                    "node_type": node_data["node_type"],
                    "x": node_data["x"],
                    "y": node_data["y"],
                    "is_active": node_data["is_active"],
                }
            )
            node_map[node_data["id"]] = node
            if created:
                self.stdout.write(f"  Created node: {node.label} ({node.node_type})")

        # Create Edges
        for edge_data in data["edges"]:
            node_from = node_map.get(edge_data["node_from"])
            node_to = node_map.get(edge_data["node_to"])
            if node_from and node_to:
                Edge.objects.get_or_create(
                    market=market,
                    node_from=node_from,
                    node_to=node_to,
                    defaults={
                        "weight": edge_data["weight"],
                        "is_active": edge_data["is_active"],
                    }
                )

        self.stdout.write(self.style.SUCCESS(f"Created {len(data['edges'])} edges"))

        # Create Vendors and Products
        for vendor_data in data["vendors"]:
            node = node_map.get(vendor_data["node_id"])
            if not node:
                continue

            vendor, created = Vendor.objects.get_or_create(
                business_name=vendor_data["business_name"],
                defaults={
                    "market": market,
                    "node": node,
                    "owner_name": vendor_data["owner_name"],
                    "description": vendor_data["description"],
                    "phone": vendor_data["phone"],
                    "whatsapp": vendor_data["whatsapp"],
                    "email": vendor_data["email"],
                    "is_active": True,
                }
            )

            # Assign categories
            for cat_name in vendor_data["categories"]:
                cat = category_map.get(cat_name)
                if cat:
                    vendor.categories.add(cat)

            # Create products
            for prod_data in vendor_data["products"]:
                Product.objects.get_or_create(
                    vendor=vendor,
                    name=prod_data["name"],
                    defaults={
                        "price": prod_data["price"],
                        "is_available": prod_data["is_available"],
                    }
                )

            self.stdout.write(f"  {'Created' if created else 'Found'} vendor: {vendor.business_name}")

        self.stdout.write(self.style.SUCCESS("\nSample market data loaded successfully!"))
        self.stdout.write(f"\nMarket: {market.name}")
        self.stdout.write(f"  Nodes: {market.nodes.count()}")
        self.stdout.write(f"  Edges: {market.edges.count()}")
        self.stdout.write(f"  Vendors: {market.vendors.count()}")
        self.stdout.write(f"  Zones: {market.zones.count()}")
        self.stdout.write("\nNext steps:")
        self.stdout.write("  1. Copy the SVG floor plan to your MEDIA_ROOT/maps/ directory")
        self.stdout.write("  2. Update the market's map_image field in admin")
        self.stdout.write("  3. Visit /market/balogun-market-lagos/map/ to test navigation")
