from django import forms
from .models import MakerspaceOrder, MakerspaceProfile


class MakerspaceOrderForm(forms.ModelForm):
    """Customer submits a new makerspace order."""

    class Meta:
        model  = MakerspaceOrder
        fields = (
            'service_type', 'material', 'infill', 'quantity',
            'color', 'notes', 'design_file',
        )
        widgets = {
            'notes':   forms.Textarea(attrs={'rows': 3}),
            'color':   forms.TextInput(attrs={'placeholder': 'e.g. White, Black, Transparent'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select,)):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
        # File field special styling
        self.fields['design_file'].widget.attrs.update({'class': 'form-control', 'accept': '.stl,.dxf,.dwg,.svg,.pdf,.obj,.step,.stp,.iges,.igs'})
        self.fields['design_file'].help_text = (
            'Accepted: STL, OBJ, DXF, DWG, SVG, PDF, STEP, IGES. '
            'Max 50 MB. STL files get automatic volume/weight calculation.'
        )

    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity', 1)
        if qty < 1:
            raise forms.ValidationError('Quantity must be at least 1.')
        if qty > 1000:
            raise forms.ValidationError('Maximum quantity is 1000 per order.')
        return qty


class VendorQuoteForm(forms.ModelForm):
    """Vendor sets final price and notes."""

    class Meta:
        model  = MakerspaceOrder
        fields = ('vendor_price', 'vendor_note')
        widgets = {
            'vendor_note': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Message to customer...'}),
            'vendor_price': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class VendorStatusForm(forms.ModelForm):
    """Vendor updates order status."""

    class Meta:
        model  = MakerspaceOrder
        fields = ('status', 'vendor_note')
        widgets = {
            'vendor_note': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Vendor can only set these statuses
        self.fields['status'].choices = [
            (MakerspaceOrder.STATUS_QUOTED,        'Quoted — Send quote to customer'),
            (MakerspaceOrder.STATUS_IN_PRODUCTION, 'In Production — Start work'),
            (MakerspaceOrder.STATUS_READY,         'Ready — Notify customer'),
            (MakerspaceOrder.STATUS_DELIVERED,     'Delivered — Mark complete'),
            (MakerspaceOrder.STATUS_REJECTED,      'Rejected — Decline order'),
        ]
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 2})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class MakerspaceProfileForm(forms.ModelForm):
    """Vendor configures their makerspace pricing."""

    class Meta:
        model  = MakerspaceProfile
        fields = (
            'is_active', 'description',
            'price_pla_per_gram', 'price_petg_per_gram',
            'price_abs_per_gram', 'price_resin_per_gram',
            'price_laser_per_cm2', 'price_cnc_per_cm2',
            'price_design_service',
            'min_lead_time_days', 'max_lead_time_days',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})
            else:
                field.widget.attrs.update({'class': 'form-control'})
