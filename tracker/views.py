from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.db.models import Count, Q, F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .forms import ApplicationForm
from .models import Application

@require_http_methods(['GET', 'POST'])
def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = UserCreationForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Welcome! Add your first application to get started.')
        return redirect('dashboard')
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def dashboard(request):
    apps = request.user.applications.all()
    today = timezone.localdate()
    active = apps.exclude(status__in=['rejected', 'withdrawn'])
    counts = {row['status']: row['count'] for row in apps.values('status').annotate(count=Count('id'))}
    return render(request, 'tracker/dashboard.html', {
        'status_counts': [(value, label, counts.get(value, 0)) for value, label in Application.Status.choices],
        'total': apps.count(), 'interviews': counts.get('interviewing', 0), 'offers': counts.get('offer', 0),
        'overdue': active.filter(follow_up_date__lt=today).count(),
        'followups': active.filter(follow_up_date__lte=today + timedelta(days=7)).order_by('follow_up_date', 'pk')[:12],
        'recent': apps[:5], 'today': today,
    })

@login_required
def application_list(request):
    apps = request.user.applications.all()
    query = request.GET.get('q', '').strip()[:200]
    status = request.GET.get('status', '')
    sort = request.GET.get('sort', 'updated')
    if query:
        apps = apps.filter(Q(company__icontains=query) | Q(job_title__icontains=query))
    if status in Application.Status.values:
        apps = apps.filter(status=status)
    else:
        status = ''
    if sort == 'followup':
        apps = apps.order_by(F('follow_up_date').asc(nulls_last=True), '-updated_at')
    else:
        sort = 'updated'
    page = Paginator(apps, 20).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'tracker/application_list.html', {'page_obj': page, 'q': query, 'status': status, 'sort': sort, 'statuses': Application.Status.choices, 'querystring': params.urlencode()})

@login_required
def application_detail(request, pk):
    application = get_object_or_404(Application, pk=pk, user=request.user)
    return render(request, 'tracker/application_detail.html', {'application': application})

@login_required
@require_http_methods(['GET', 'POST'])
def application_form(request, pk=None):
    application = get_object_or_404(Application, pk=pk, user=request.user) if pk else None
    form = ApplicationForm(request.POST if request.method == 'POST' else None, instance=application)
    if request.method == 'POST' and form.is_valid():
        application = form.save(commit=False)
        application.user = request.user
        application.save()
        messages.success(request, 'Application saved.')
        return redirect('application_detail', pk=application.pk)
    return render(request, 'tracker/application_form.html', {'form': form, 'application': application})

@login_required
@require_http_methods(['GET', 'POST'])
def application_delete(request, pk):
    application = get_object_or_404(Application, pk=pk, user=request.user)
    if request.method == 'POST':
        application.delete()
        messages.success(request, 'Application deleted.')
        return redirect('application_list')
    return render(request, 'tracker/application_confirm_delete.html', {'application': application})
