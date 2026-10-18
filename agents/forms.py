from django import forms
from .models import Agent, Client, Deal, Inquiry


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ('full_name', 'email', 'phone', 'company', 'tier', 'notes')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = ('client', 'title', 'value', 'status', 'notes')
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, agent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.filter(agent=agent)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class InquiryResponseForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ('status', 'response')
        widgets = {
            'response': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class TaskForm(forms.ModelForm):
    class Meta:
        from .models import Task
        model = Task
        fields = ('client', 'title', 'notes', 'priority', 'status', 'due_date')
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, agent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.filter(agent=agent)
        self.fields['client'].required = False
        for field in self.fields.values():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 2})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class ProposalForm(forms.ModelForm):
    class Meta:
        from .models import Proposal
        model = Proposal
        fields = ('client', 'title', 'content', 'value', 'status')
        widgets = {'content': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, agent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.filter(agent=agent)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 4})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class InquiryCreateForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ('client', 'subject', 'message', 'status')
        widgets = {'message': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, agent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.filter(agent=agent)
        self.fields['client'].required = False
        for field in self.fields.values():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 4})
            else:
                field.widget.attrs.update({'class': 'form-control'})
