from django import forms
from django.core.validators import FileExtensionValidator, RegexValidator
from django.core.exceptions import ValidationError
from .models import Vendor, Product, ProductCategory


# ------------------------------------------------------------------
# Shared validators
# ------------------------------------------------------------------

phone_validator = RegexValidator(
    regex=r'^\+?[1-9]\d{1,14}$',
    message="Enter a valid phone number with country code, e.g. +2348000000000",
)


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add file extension validator to logo field
        self.fields["logo"].validators.append(
            FileExtensionValidator(
                allowed_extensions=["png", "jpg", "jpeg", "webp"],
                message="Only PNG, JPG, JPEG, and WEBP images are allowed.",
            )
        )
        # Add phone validators
        self.fields["phone"].validators.append(phone_validator)
        self.fields["whatsapp"].validators.append(phone_validator)

    def clean_logo(self):
        """Validate logo file size (max 2MB)."""
        logo = self.cleaned_data.get("logo")
        if logo:
            max_size = 2 * 1024 * 1024  # 2MB in bytes
            if logo.size > max_size:
                raise ValidationError(
                    f"Logo must be under 2MB. Your file is {logo.size / (1024 * 1024):.1f}MB."
                )
        return logo

    def clean_whatsapp(self):
        """Normalize WhatsApp number to international format."""
        whatsapp = self.cleaned_data.get("whatsapp", "")
        if whatsapp:
            # Remove spaces and dashes, ensure starts with +
            cleaned = whatsapp.replace(" ", "").replace("-", "")
            if not cleaned.startswith("+"):
                # If no country code, we can't assume one - require it
                raise ValidationError(
                    "WhatsApp number must include a country code (e.g. +234...)."
                )
            return cleaned
        return whatsapp


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
            "price": "Price in Nigerian Naira (N). Leave blank if price varies.",
            "is_available": "Uncheck to hide this item from shoppers temporarily.",
        }