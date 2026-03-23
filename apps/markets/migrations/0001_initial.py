# Generated migration for apps.markets

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Market",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(blank=True, max_length=220, unique=True)),
                ("city", models.CharField(max_length=100)),
                ("state", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("address", models.TextField(blank=True)),
                ("map_image", models.ImageField(blank=True, help_text="Upload an SVG or image of the market floor plan.", null=True, upload_to="maps/")),
                ("map_width", models.PositiveIntegerField(default=1000)),
                ("map_height", models.PositiveIntegerField(default=1000)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Market", "verbose_name_plural": "Markets", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Zone",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("code", models.CharField(blank=True, max_length=20)),
                ("description", models.TextField(blank=True)),
                ("color_hex", models.CharField(default="#AED6F1", max_length=7)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("market", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="zones", to="markets.market")),
            ],
            options={"verbose_name": "Zone", "verbose_name_plural": "Zones", "ordering": ["market", "name"], "unique_together": {("market", "name")}},
        ),
        migrations.CreateModel(
            name="Node",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("qr_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("label", models.CharField(max_length=100)),
                ("node_type", models.CharField(choices=[("stall", "Vendor Stall"), ("intersection", "Aisle Intersection"), ("entrance", "Market Entrance"), ("exit", "Exit"), ("amenity", "Amenity (toilet, ATM, etc.)")], default="stall", max_length=20)),
                ("x", models.FloatField(default=0.0)),
                ("y", models.FloatField(default=0.0)),
                ("qr_image", models.ImageField(blank=True, editable=False, null=True, upload_to="qr_codes/")),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("market", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="nodes", to="markets.market")),
                ("zone", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="nodes", to="markets.zone")),
            ],
            options={"verbose_name": "Node", "verbose_name_plural": "Nodes", "ordering": ["market", "label"]},
        ),
        migrations.CreateModel(
            name="Edge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("weight", models.FloatField(default=1.0, help_text="Walking distance in metres between the two nodes.")),
                ("is_active", models.BooleanField(default=True)),
                ("market", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="edges", to="markets.market")),
                ("node_from", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="edges_from", to="markets.node")),
                ("node_to", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="edges_to", to="markets.node")),
            ],
            options={"verbose_name": "Edge (Path)", "verbose_name_plural": "Edges (Paths)", "unique_together": {("node_from", "node_to")}},
        ),
    ]
