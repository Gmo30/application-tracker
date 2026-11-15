from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from .models import Application

@override_settings(STORAGES={'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'}, 'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}})
class TrackerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('alice', password='test-long-pass-472!')
        cls.other = get_user_model().objects.create_user('bob', password='test-long-pass-921!')

    def setUp(self):
        self.client.force_login(self.user)

    def make_application(self, **kwargs):
        data = {'user': self.user, 'company': 'Example', 'job_title': 'Engineer'}
        data.update(kwargs)
        return Application.objects.create(**data)

    def test_login_required(self):
        self.client.logout()
        for route in ['dashboard', 'application_list', 'application_create']:
            self.assertRedirects(self.client.get(reverse(route)), f'/accounts/login/?next={reverse(route)}')

    def test_signup_and_logout(self):
        self.client.logout()
        response = self.client.post(reverse('signup'), {'username': 'new-user', 'password1': 'unique-long-password-274!', 'password2': 'unique-long-password-274!'})
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(get_user_model().objects.filter(username='new-user').exists())
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.assertRedirects(self.client.post(reverse('logout')), reverse('login'))

    def test_create_update_delete_lifecycle(self):
        response = self.client.post(reverse('application_create'), {'company': 'Acme', 'job_title': 'Developer', 'status': 'saved', 'user': self.other.pk})
        app = Application.objects.get(company='Acme')
        self.assertEqual(app.user, self.user)
        self.assertRedirects(response, reverse('application_detail', args=[app.pk]))
        response = self.client.post(reverse('application_edit', args=[app.pk]), {'company': 'Acme', 'job_title': 'Developer', 'status': 'applied', 'application_date': timezone.localdate().isoformat(), 'notes': 'Sent application'})
        self.assertEqual(response.status_code, 302)
        app.refresh_from_db()
        self.assertEqual(app.status, 'applied')
        self.assertEqual(app.notes, 'Sent application')
        self.assertEqual(self.client.get(reverse('application_delete', args=[app.pk])).status_code, 200)
        self.assertTrue(Application.objects.filter(pk=app.pk).exists())
        self.assertRedirects(self.client.post(reverse('application_delete', args=[app.pk])), reverse('application_list'))
        self.assertFalse(Application.objects.filter(pk=app.pk).exists())

    def test_other_user_records_are_inaccessible(self):
        app = self.make_application(user=self.other, company='PrivateCompanySecret')
        for route in ['application_detail', 'application_edit', 'application_delete']:
            url = reverse(route, args=[app.pk])
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.post(url, {'company': 'Stolen', 'job_title': 'Changed', 'status': 'saved'}).status_code, 404)
        self.assertNotContains(self.client.get(reverse('application_list')), 'PrivateCompanySecret')
        self.assertEqual(self.client.get(reverse('dashboard')).context['total'], 0)
        app.refresh_from_db()
        self.assertEqual(app.company, 'PrivateCompanySecret')

    def test_validation(self):
        for data in [
            {'company': '', 'job_title': 'Engineer', 'status': 'saved'},
            {'company': 'Acme', 'job_title': 'Engineer', 'status': 'applied'},
            {'company': 'Acme', 'job_title': 'Engineer', 'status': 'saved', 'job_url': 'javascript:alert(1)'},
            {'company': 'Acme', 'job_title': 'Engineer', 'status': 'applied', 'application_date': (timezone.localdate() + timedelta(days=1)).isoformat()},
        ]:
            response = self.client.post(reverse('application_create'), data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['form'].errors)
        self.assertEqual(Application.objects.count(), 0)

    def test_search_filter_sort(self):
        first = self.make_application(company='Acme', status='applied', follow_up_date=timezone.localdate())
        self.make_application(company='Other', status='saved')
        response = self.client.get(reverse('application_list'), {'q': 'ACME', 'status': 'applied'})
        self.assertEqual(list(response.context['page_obj']), [first])
        response = self.client.get(reverse('application_list'), {'sort': 'followup'})
        self.assertEqual(list(response.context['page_obj'])[0], first)

    def test_dashboard_followups(self):
        today = timezone.localdate()
        overdue = self.make_application(status='applied', follow_up_date=today - timedelta(days=1))
        due_today = self.make_application(follow_up_date=today)
        self.make_application(status='rejected', follow_up_date=today - timedelta(days=2))
        self.make_application(status='withdrawn', follow_up_date=today - timedelta(days=3))
        self.make_application(follow_up_date=today + timedelta(days=8))
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['total'], 5)
        self.assertEqual(response.context['overdue'], 1)
        self.assertEqual(list(response.context['followups']), [overdue, due_today])

    def test_notes_are_escaped(self):
        app = self.make_application(notes='<script>alert(1)</script>')
        response = self.client.get(reverse('application_detail', args=[app.pk]))
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;')

    def test_csrf_is_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse('application_create'), {'company': 'Acme', 'job_title': 'Engineer', 'status': 'saved'}).status_code, 403)

    def test_pagination_preserves_query(self):
        Application.objects.bulk_create([Application(user=self.user, company='Acme', job_title=f'Engineer {i}') for i in range(22)])
        response = self.client.get(reverse('application_list'), {'q': 'Acme', 'status': 'saved', 'page': 2})
        self.assertEqual(len(response.context['page_obj']), 2)
        self.assertIn('q=Acme', response.context['querystring'])
        self.assertNotIn('page=', response.context['querystring'])
