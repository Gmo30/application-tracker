from django.conf import settings
from django.db import models
from django.utils import timezone

class Application(models.Model):
    class Status(models.TextChoices):
        SAVED = 'saved', 'Saved'
        APPLIED = 'applied', 'Applied'
        INTERVIEWING = 'interviewing', 'Interviewing'
        OFFER = 'offer', 'Offer'
        REJECTED = 'rejected', 'Rejected'
        WITHDRAWN = 'withdrawn', 'Withdrawn'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    company = models.CharField(max_length=160)
    job_title = models.CharField(max_length=200)
    job_url = models.URLField(max_length=1000, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SAVED)
    application_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    next_action = models.CharField(max_length=240, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-pk']
        indexes = [models.Index(fields=['user', 'status']), models.Index(fields=['user', 'follow_up_date'])]

    @property
    def is_overdue(self):
        return bool(self.follow_up_date and self.follow_up_date < timezone.localdate() and self.status not in [self.Status.REJECTED, self.Status.WITHDRAWN])

    def __str__(self):
        return f'{self.job_title} at {self.company}'
