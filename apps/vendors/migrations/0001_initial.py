# Generated migration for apps.vendors

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("markets", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("icon", models.CharField(blank=True, max_length=50)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "Product Category", "verbose_name_plural": "Product Categories", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Vendor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("business_name", models.CharField(max_length=200)),
                ("owner_name", models.CharField(blank=True, max_length=150)),
                ("description", models.TextField(blank=True)),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("whatsapp", models.CharField(blank=True, max_length=20)),
                ("email", models.EmailField(blank=True)),
                ("logo", models.ImageField(blank=True, null=True, upload_to="vendor_logos/")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vendor_profile", to=settings.AUTH_USER_MODEL)),
                ("node", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vendor", to="markets.node")),
                ("market", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="vendors", to="markets.market")),
                ("categories", models.ManyToManyField(blank=True, related_name="vendors", to="vendors.productcategory")),
            ],
            options={"verbose_name": "Vendor", "verbose_name_plural": "Vendors", "ordering": ["business_name"]},
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("price", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("is_available", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("vendor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="products", to="vendors.vendor")),
                ("category", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="products", to="vendors.productcategory")),
            ],
            options={"verbose_name": "Product", "verbose_name_plural": "Products", "ordering": ["vendor", "name"]},
        ),
    ]
