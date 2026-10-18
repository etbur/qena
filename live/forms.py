from django import forms
from .models import LiveStream
from store.models import Product


class LiveStreamForm(forms.ModelForm):
    class Meta:
        model  = LiveStream
        fields = ('title', 'description', 'thumbnail', 'scheduled_at')
        widgets = {
            'description':  forms.Textarea(attrs={'rows': 3}),
            'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, vendor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.vendor = vendor
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})
            else:
                field.widget.attrs.update({'class': 'form-control'})
        self.fields['scheduled_at'].required = False


class PinProductForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.none())

    def __init__(self, vendor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = vendor.products.filter(is_active=True)
        self.fields['product'].widget.attrs.update({'class': 'form-select'})
