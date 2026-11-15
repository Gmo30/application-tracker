from django import forms
from django.core.validators import URLValidator
from django.utils import timezone
from .models import Application

class ApplicationForm(forms.ModelForm):
    job_url = forms.URLField(required=False, max_length=1000, validators=[URLValidator(schemes=['http', 'https'])], label='Job link')

    class Meta:
        model = Application
        fields = ['company', 'job_title', 'job_url', 'status', 'application_date', 'next_action', 'follow_up_date', 'notes']
        widgets = {'application_date': forms.DateInput(attrs={'type': 'date'}), 'follow_up_date': forms.DateInput(attrs={'type': 'date'}), 'notes': forms.Textarea(attrs={'rows': 5})}
        help_texts = {'application_date': 'Required after applying. Leave blank for a saved opportunity.', 'follow_up_date': 'Optional. Appears on your dashboard when due.'}

    def clean(self):
        data = super().clean()
        date = data.get('application_date')
        if data.get('status') in ['applied', 'interviewing', 'offer', 'rejected'] and not date:
            self.add_error('application_date', 'Enter the date you applied.')
        if date and date > timezone.localdate():
            self.add_error('application_date', 'The application date cannot be in the future.')
        return data
