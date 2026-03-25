"""
apps/vendors/portal_forms.py

Forms for the vendor self-service portal.
"""

from django import forms
from .models import Vendor, Product, ProductCategory


class VendorLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "placeholder": "Username",
            "autocomplete": "username",
            "autofocus": True,
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Password",
            "autocomplete": "current-password",
        }),
    )


class VendorProfileForm(forms.ModelForm):
    """
    Let vendors update their public-facing profile.
    Excludes: user, node, market, is_active (admin-only fields).
    """

    categories = forms.ModelMultipleChoiceField(
        queryset=ProductCategory.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        help_text="Select all categories that apply to your stall.",
    )

    class Meta:
        model = Vendor
        fields = [
            "business_name",
            "owner_name",
            "description",
            "phone",
            "whatsapp",
            "email",
            "categories",
            "logo",
        ]
        widgets = {
            "business_name": forms.TextInput(attrs={"placeholder": "e.g. Amina Fabrics"}),
            "owner_name":    forms.TextInput(attrs={"placeholder": "Your full name"}),
            "description":   forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "What do you sell? What makes your stall special?",
            }),
            "phone":    forms.TextInput(attrs={"placeholder": "+234 800 000 0000"}),
            "whatsapp": forms.TextInput(attrs={"placeholder": "+234 800 000 0000"}),
            "email":    forms.EmailInput(attrs={"placeholder": "Optional business email"}),
        }
        help_texts = {
            "whatsapp": "Include country code. Shoppers will see a 'Chat on WhatsApp' button.",
            "logo": "PNG or JPG, square crop works best. Max 2MB.",
        }


class ProductForm(forms.ModelForm):
    """Add or edit a product listing."""

    class Meta:
        model = Product
        fields = ["name", "category", "description", "price", "is_available"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Ankara Fabric (6 yards)"}),
            "description": forms.Textarea(attrs={
                "rows": 2,
                "placeholder": "Optional: colour, material, size, etc.",
            }),
            "price": forms.NumberInput(attrs={
                "placeholder": "0.00",
                "min": "0",
                "step": "0.01",
            }),
            "category": forms.Select(),
            "is_available": forms.CheckboxInput(),
        }
        help_texts = {
            "price": "Price in Nigerian Naira (₦). Leave blank if price varies.",
            "is_available": "Uncheck to hide this item from shoppers temporarily.",
        }
