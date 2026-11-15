from django.contrib import admin
from .models import Application

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['company', 'job_title', 'user', 'status', 'follow_up_date']
    list_filter = ['status']
    search_fields = ['company', 'job_title', 'user__username']
