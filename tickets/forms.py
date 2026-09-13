from django import forms
from django.contrib.auth.models import User

from .models import Ticket, Comment, Category


class BootstrapFormMixin:
    """Adds Bootstrap CSS classes to every field's widget automatically."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            css_class = 'form-select' if isinstance(field.widget, (forms.Select, forms.SelectMultiple)) else 'form-control'
            field.widget.attrs['class'] = f"{existing} {css_class}".strip()


class TicketForm(BootstrapFormMixin, forms.ModelForm):
    """
    Used by customers to create a ticket, and by agents/admins to update one.
    The view decides which subset of fields is actually editable per role.
    """

    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 5:
            raise forms.ValidationError("Title must be at least 5 characters long.")
        return title


class TicketManageForm(BootstrapFormMixin, forms.ModelForm):
    """Extra fields only Agents/Admins are allowed to edit."""

    assigned_agent = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label="Unassigned",
    )

    class Meta:
        model = Ticket
        fields = ['status', 'priority', 'assigned_agent', 'resolution_notes']
        widgets = {
            'resolution_notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Evaluated fresh on every instantiation (not cached at import time),
        # so newly registered agents show up immediately.
        self.fields['assigned_agent'].queryset = User.objects.filter(profile__role='AGENT')


class CommentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Add a comment...'}),
        }
        labels = {'body': ''}


class CategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']


class TicketFilterForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(required=False, label='Search', widget=forms.TextInput(
        attrs={'placeholder': 'Search by title or ticket ID...'}))
    status = forms.ChoiceField(required=False, choices=[('', 'All Statuses')] + list(Ticket.Status.choices))
    priority = forms.ChoiceField(required=False, choices=[('', 'All Priorities')] + list(Ticket.Priority.choices))
    category = forms.ModelChoiceField(required=False, queryset=Category.objects.all(), empty_label="All Categories")
    assigned_agent = forms.ModelChoiceField(
        required=False, queryset=User.objects.none(), empty_label="All Agents")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['assigned_agent'].queryset = User.objects.filter(profile__role='AGENT')
