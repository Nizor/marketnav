"""
apps/vendors/management/commands/create_vendor_accounts.py

Management command to create Django user accounts for vendors
that don't already have one, and link them.

Usage:
    # Create accounts for ALL vendors without a user
    python manage.py create_vendor_accounts

    # Create account for a specific vendor by ID
    python manage.py create_vendor_accounts --vendor-id 42

    # Create accounts for all vendors in a specific market
    python manage.py create_vendor_accounts --market kuje-ultramodern-market

    # Preview what would be created without doing it
    python manage.py create_vendor_accounts --dry-run

Generated credentials are printed to stdout.
Advise: pipe to a file, then distribute to vendors securely:
    python manage.py create_vendor_accounts > vendor_credentials.txt
"""

import secrets
import string
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils.text import slugify

from apps.vendors.models import Vendor


def generate_password(length=12):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits
    # Ensure at least one digit and one uppercase
    while True:
        pwd = ''.join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.isupper() for c in pwd) and
                any(c.isdigit() for c in pwd)):
            return pwd


def make_username(vendor):
    """
    Derive a username from the business name + stall label.
    e.g. 'aminafabrics_a_gf_01'
    Ensures uniqueness by appending a counter if needed.
    """
    base = slugify(vendor.business_name).replace("-", "")[:20]
    if vendor.node:
        stall = slugify(vendor.node.label).replace("-", "_")[:10]
        base = f"{base}_{stall}"
    base = base[:30]

    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}_{counter}"
        counter += 1
    return username


class Command(BaseCommand):
    help = "Create Django user accounts for vendors and link them."

    def add_arguments(self, parser):
        parser.add_argument(
            "--vendor-id",
            type=int,
            help="Create account for a single vendor by primary key.",
        )
        parser.add_argument(
            "--market",
            type=str,
            help="Create accounts for all vendors in this market (slug).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be created without saving anything.",
        )

    def handle(self, *args, **options):
        qs = Vendor.objects.filter(user__isnull=True, is_active=True)

        if options["vendor_id"]:
            qs = qs.filter(pk=options["vendor_id"])
        if options["market"]:
            qs = qs.filter(market__slug=options["market"])

        if not qs.exists():
            self.stdout.write(self.style.WARNING(
                "No vendors found matching criteria (or all already have accounts)."
            ))
            return

        dry = options["dry_run"]
        if dry:
            self.stdout.write(self.style.WARNING("DRY RUN — nothing will be saved.\n"))

        self.stdout.write(
            f"{'VENDOR':<35} {'STALL':<20} {'USERNAME':<30} {'PASSWORD':<15}"
        )
        self.stdout.write("-" * 105)

        created = 0
        for vendor in qs.select_related("node", "market"):
            username = make_username(vendor)
            password = generate_password()

            if not dry:
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=vendor.email or "",
                    first_name=vendor.owner_name.split()[0] if vendor.owner_name else "",
                )
                vendor.user = user
                vendor.save(update_fields=["user"])

            stall = vendor.node.label if vendor.node else "unassigned"
            self.stdout.write(
                f"{vendor.business_name:<35} {stall:<20} {username:<30} {password:<15}"
            )
            created += 1

        self.stdout.write("-" * 105)
        action = "Would create" if dry else "Created"
        self.stdout.write(self.style.SUCCESS(
            f"\n{action} {created} vendor account(s)."
        ))
        if not dry:
            self.stdout.write(
                "⚠  Share these credentials securely. "
                "Vendors should change their password on first login.\n"
            )
