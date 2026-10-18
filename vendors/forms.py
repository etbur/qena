from django import forms
from .models import Vendor, VendorBankAccount, VendorInventoryItem, VendorWarehouse, VendorSupplier
from store.models import Product, Category


class VendorSetupForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = (
            'store_name', 'subdomain', 'custom_domain', 'store_tagline',
            'description', 'brand_primary', 'brand_secondary',
            'logo', 'banner', 'phone', 'email', 'address', 'city', 'country'
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tell customers about your business, expertise, and what you sell...'}),
            'store_tagline': forms.TextInput(attrs={'placeholder': 'e.g. Best Tech & Electronics Store in Addis Ababa'}),
            'subdomain': forms.TextInput(attrs={'placeholder': 'e.g. alex'}),
            'custom_domain': forms.TextInput(attrs={'placeholder': 'e.g. alex.com or www.alex.com'}),
            'brand_primary': forms.TextInput(attrs={'type': 'color', 'style': 'height:38px;padding:2px;cursor:pointer;'}),
            'brand_secondary': forms.TextInput(attrs={'type': 'color', 'style': 'height:38px;padding:2px;cursor:pointer;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'category', 'description', 'price', 'original_price',
                  'stock', 'image', 'image2', 'image3', 'is_active', 'is_featured', 'is_flash_deal')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class VendorInventoryItemForm(forms.ModelForm):
    class Meta:
        model = VendorInventoryItem
        fields = (
            'item_name', 'sku', 'barcode', 'category', 'unit', 'image',
            'unit_cost', 'selling_price',
            'quantity', 'reorder_level',
            'location', 'warehouse', 'supplier',
            'expiry_date', 'notes', 'is_public',
        )
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, vendor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if vendor:
            self.fields['warehouse'].queryset = VendorWarehouse.objects.filter(vendor=vendor)
            self.fields['supplier'].queryset = VendorSupplier.objects.filter(vendor=vendor)
        else:
            self.fields['warehouse'].queryset = VendorWarehouse.objects.none()
            self.fields['supplier'].queryset = VendorSupplier.objects.none()
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class BankAccountForm(forms.ModelForm):
    class Meta:
        model = VendorBankAccount
        fields = ('bank_name', 'account_holder', 'account_number', 'iban', 'swift_code')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

