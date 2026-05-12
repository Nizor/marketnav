# generate_sample_data.py
import json
import random
import math

# Market dimensions (map coordinate space)
MAP_WIDTH = 1000
MAP_HEIGHT = 800
REAL_WIDTH = 120   # metres
REAL_HEIGHT = 80   # metres

# Grid settings: rows of stalls with aisles between
STALL_ROWS = 8
STALL_COLS = 12
AISLE_WIDTH = 40   # map units (approx 4.8m)
STALL_SIZE = 70    # map units (approx 8.4m)

# Zones (sections)
ZONES = [
    {"name": "Foodstuffs", "code": "FOOD", "color": "#F9E79F", "rows": [0,1]},
    {"name": "Textiles", "code": "TEXT", "color": "#D5F5E3", "rows": [2,3]},
    {"name": "Electronics", "code": "ELEC", "color": "#D4E6F1", "rows": [4,5]},
    {"name": "Household", "code": "HOME", "color": "#FADBD8", "rows": [6,7]},
]

# Product categories
CATEGORIES = [
    {"name": "Foodstuffs", "icon": "🍅", "desc": "Rice, beans, oil, spices"},
    {"name": "Fresh Produce", "icon": "🥬", "desc": "Vegetables, fruits, yam"},
    {"name": "Meat & Fish", "icon": "🐟", "desc": "Fresh/frozen meat, fish, chicken"},
    {"name": "Textiles", "icon": "🧵", "desc": "Ankara, lace, brocade, cotton"},
    {"name": "Ready-to-wear", "icon": "👗", "desc": "Dresses, shirts, native wears"},
    {"name": "Electronics", "icon": "📱", "desc": "Phones, chargers, cables, gadgets"},
    {"name": "Home Appliances", "icon": "🔌", "desc": "Blenders, heaters, fans"},
    {"name": "Household Items", "icon": "🍽️", "desc": "Utensils, plastics, cookware"},
    {"name": "Beauty & Cosmetics", "icon": "💄", "desc": "Makeup, skincare, hair"},
    {"name": "Hardware", "icon": "🔧", "desc": "Tools, paints, building materials"},
]

# Helper to generate node ID (incremental)
def generate_nodes_and_edges():
    nodes = []
    edges = []
    node_id = 1
    zone_map = []  # list of (zone_idx, row_idx, col_idx) for each stall node

    # --- Entrances (four corners) ---
    entrance_positions = [
        {"label": "Main Entrance", "x": 50, "y": MAP_HEIGHT//2, "type": "entrance"},
        {"label": "North Entrance", "x": MAP_WIDTH//2, "y": MAP_HEIGHT-30, "type": "entrance"},
        {"label": "East Entrance", "x": MAP_WIDTH-30, "y": MAP_HEIGHT//2, "type": "entrance"},
        {"label": "West Entrance", "x": 30, "y": MAP_HEIGHT//2, "type": "entrance"},
    ]
    entrance_ids = []
    for pos in entrance_positions:
        nodes.append({
            "id": node_id,
            "label": pos["label"],
            "node_type": pos["type"],
            "zone_idx": None,
            "x": pos["x"],
            "y": pos["y"],
            "is_active": True,
        })
        entrance_ids.append(node_id)
        node_id += 1

    # Create a central intersection (hub)
    hub_x = MAP_WIDTH//2
    hub_y = MAP_HEIGHT//2
    nodes.append({
        "id": node_id,
        "label": "Central Hub",
        "node_type": "intersection",
        "zone_idx": None,
        "x": hub_x,
        "y": hub_y,
        "is_active": True,
    })
    hub_id = node_id
    node_id += 1

    # Connect entrances to hub
    for eid in entrance_ids:
        from_node = eid
        to_node = hub_id
        weight = math.hypot(
            nodes[eid-1]["x"] - nodes[hub_id-1]["x"],
            nodes[eid-1]["y"] - nodes[hub_id-1]["y"]
        ) * (REAL_WIDTH / MAP_WIDTH)  # convert to metres
        edges.append({
            "node_from": from_node,
            "node_to": to_node,
            "weight": round(weight, 1),
            "is_active": True,
        })

    # --- Generate stalls in grid ---
    start_x = 150
    start_y = 100
    for row in range(STALL_ROWS):
        for col in range(STALL_COLS):
            x = start_x + col * (STALL_SIZE + AISLE_WIDTH)
            y = start_y + row * (STALL_SIZE + AISLE_WIDTH)
            label = f"Stall {chr(65+row)}{col+1}"  # A1, A2, …, H12
            # Determine zone based on row
            zone_idx = None
            for zi, zone in enumerate(ZONES):
                if row in zone["rows"]:
                    zone_idx = zi
                    break
            nodes.append({
                "id": node_id,
                "label": label,
                "node_type": "stall",
                "zone_idx": zone_idx,
                "x": x,
                "y": y,
                "is_active": True,
            })
            zone_map.append((zone_idx, row, col, node_id))
            node_id += 1

    # --- Connect stalls to neighbours (horizontal and vertical) and to hub via aisles---
    # First, create intersection nodes at aisle crossings
    intersection_coords = set()
    # Horizontal aisles (between rows)
    for row in range(STALL_ROWS-1):
        y_aisle = start_y + (row+1)*(STALL_SIZE + AISLE_WIDTH) - AISLE_WIDTH//2
        for col in range(STALL_COLS-1):
            x_aisle = start_x + (col+1)*(STALL_SIZE + AISLE_WIDTH) - AISLE_WIDTH//2
            intersection_coords.add((x_aisle, y_aisle))
    # Intersections along the outer perimeter (to connect to hub)
    mid_row = STALL_ROWS // 2
    mid_col = STALL_COLS // 2
    center_x = start_x + mid_col*(STALL_SIZE + AISLE_WIDTH) + STALL_SIZE//2
    center_y = start_y + mid_row*(STALL_SIZE + AISLE_WIDTH) + STALL_SIZE//2
    intersection_coords.add((center_x, center_y))

    intersection_ids = {}
    for (ix, iy) in intersection_coords:
        nodes.append({
            "id": node_id,
            "label": f"J{len(intersection_ids)+1}",
            "node_type": "intersection",
            "zone_idx": None,
            "x": ix,
            "y": iy,
            "is_active": True,
        })
        intersection_ids[(ix, iy)] = node_id
        node_id += 1

    # Connect hub to nearest intersection (center aisle crossing)
    hub_to_intersection = min(intersection_ids.items(), key=lambda kv: math.hypot(kv[0][0]-hub_x, kv[0][1]-hub_y))
    edges.append({
        "node_from": hub_id,
        "node_to": hub_to_intersection[1],
        "weight": round(math.hypot(hub_x - hub_to_intersection[0][0], hub_y - hub_to_intersection[0][1]) * (REAL_WIDTH/MAP_WIDTH), 1),
        "is_active": True,
    })

    # For each stall, connect to the nearest intersection (or directly to neighbour intersections)
    for (zone_idx, row, col, stall_nid) in zone_map:
        sx = nodes[stall_nid-1]["x"]
        sy = nodes[stall_nid-1]["y"]
        # find closest intersection
        closest = min(intersection_ids.items(), key=lambda kv: math.hypot(kv[0][0]-sx, kv[0][1]-sy))
        edges.append({
            "node_from": stall_nid,
            "node_to": closest[1],
            "weight": round(math.hypot(sx-closest[0][0], sy-closest[0][1]) * (REAL_WIDTH/MAP_WIDTH), 1),
            "is_active": True,
        })

    return nodes, edges, zone_map

# Generate vendors with products
def generate_vendors(zone_map, nodes):
    vendor_names = [
        "Amina's Fabrics", "Deji Electronics", "Mama Grace Foodstuffs",
        "Tunde Hardware", "Blessing Cosmetics", "Chidi Phone World",
        "Fatima Kitchenware", "Olu Textiles", "Joy Fresh Produce",
        "Kingsley Gadgets", "Rukayat Rice & Beans", "Segun Ready-to-wear",
        "Ngozi Home Appliances", "Peter Meat Joint", "Esther Beads & Accessories",
    ]
    # Map zone names to categories
    zone_to_cats = {
        "Foodstuffs": ["Foodstuffs", "Fresh Produce", "Meat & Fish"],
        "Textiles": ["Textiles", "Ready-to-wear"],
        "Electronics": ["Electronics", "Home Appliances"],
        "Household": ["Household Items", "Hardware", "Beauty & Cosmetics"],
    }
    vendors = []
    # Assign vendors to random stalls (avoid duplicates)
    used_nodes = set()
    for vname in vendor_names:
        # pick a stall node that is not used and is of type "stall"
        available = [n for n in nodes if n["node_type"] == "stall" and n["id"] not in used_nodes]
        if not available:
            break
        stall = random.choice(available)
        used_nodes.add(stall["id"])
        zone_idx = stall["zone_idx"]
        zone_name = ZONES[zone_idx]["name"] if zone_idx is not None else "Foodstuffs"
        # Determine categories based on zone
        cat_names = zone_to_cats.get(zone_name, ["Foodstuffs", "Household Items"])
        # Select 1-2 categories
        selected_cats = random.sample(cat_names, min(2, len(cat_names)))
        # Generate 2-5 products
        products = []
        for p in range(random.randint(2,5)):
            product_templates = {
                "Foodstuffs": ["Rice (50kg)", "Beans (25kg)", "Groundnut Oil (5L)", "Garri (20kg)"],
                "Fresh Produce": ["Tomatoes (basket)", "Onions (bag)", "Yam (tubers)", "Spinach (bunch)"],
                "Meat & Fish": ["Chicken (whole)", "Beef (kg)", "Fish (tilapia)", "Goat meat (kg)"],
                "Textiles": ["Ankara (6 yards)", "Lace (5 yards)", "Brocade (6 yards)", "Cotton (metre)"],
                "Ready-to-wear": ["Men's shirt", "Women's dress", "Children's set", "Native attire"],
                "Electronics": ["Phone charger", "Power bank", "Earphones", "Phone case"],
                "Home Appliances": ["Electric kettle", "Blender", "Iron", "Fan"],
                "Household Items": ["Plastic bowl set", "Cutlery set", "Broom", "Mop"],
                "Beauty & Cosmetics": ["Lipstick", "Foundation", "Hair cream", "Nail polish"],
                "Hardware": ["Paint brush", "Hammer", "Nails (bag)", "Cement (bag)"],
            }
            cat_products = []
            for cat in selected_cats:
                cat_products.extend(product_templates.get(cat, ["Item"]))
            prod_name = random.choice(cat_products)
            price = random.randint(500, 50000)
            products.append({
                "name": prod_name,
                "price": price,
                "is_available": random.choice([True, True, True, False]),
            })
        vendors.append({
            "business_name": vname,
            "owner_name": f"Mrs/Mr {vname.split()[0]}",
            "description": f"We sell quality {', '.join(selected_cats)}. Visit our stall and get the best prices.",
            "phone": f"+234{random.randint(7000000000, 7999999999)}",
            "whatsapp": f"+234{random.randint(7000000000, 7999999999)}",
            "email": f"{vname.lower().replace(' ', '_')}@example.com",
            "node_id": stall["id"],
            "categories": selected_cats,
            "products": products,
        })
    return vendors

def main():
    nodes, edges, zone_map = generate_nodes_and_edges()
    vendors = generate_vendors(zone_map, nodes)

    # Prepare full dataset
    data = {
        "market": {
            "slug": "balogun-market-lagos",
            "name": "Balogun Market",
            "city": "Lagos Island",
            "state": "Lagos",
            "description": "One of West Africa's largest open markets, famous for textiles, electronics, and general goods.",
            "address": "Balogun Street, Lagos Island, Lagos",
            "map_width": MAP_WIDTH,
            "map_height": MAP_HEIGHT,
            "real_width_m": REAL_WIDTH,
            "real_height_m": REAL_HEIGHT,
            "is_active": True,
        },
        "zones": ZONES,
        "categories": CATEGORIES,
        "nodes": nodes,
        "edges": edges,
        "vendors": vendors,
    }

    with open("sample_market_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Generated sample_market_data.json with {} nodes, {} edges, {} vendors.".format(
        len(nodes), len(edges), len(vendors)
    ))

if __name__ == "__main__":
    main()