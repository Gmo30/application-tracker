# Application Tracker — Django MVP

A job application tracker for individual job seekers. Built with Python, Django 5.2, server-rendered HTML, and a small local CSS file. No JavaScript build process or external assets required.

## What works

- Username/password signup, login, and POST-only logout.
- Private records: every application view and mutation is scoped to its owner.
- Create, view, edit, and delete applications with a confirmation screen.
- Company, role, job URL, six statuses, application date, notes, next action, and follow-up date.
- Company/role search, status filters, recent-update and follow-up sorting, 20 records per page.
- Dashboard totals, counts for all statuses, recently updated applications, and due/overdue follow-ups through seven days ahead.
- Responsive CSS, keyboard focus styles, labeled fields, inline errors, and an empty state.

This is an initial prototype. Email login, password reset, email reminders, uploads, and account deletion are not implemented. No demo accounts, personal records, or production secrets are included.

## Run locally (Python 3.12 recommended)

Extract this folder and open a terminal inside it.

macOS/Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export DJANGO_DEBUG=true
python manage.py migrate
python manage.py runserver
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DJANGO_DEBUG="true"
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000 and create an account. The address works on your computer only; it is not the deployed link.

Local SQLite records live in db.sqlite3. Keep that file if you want to retain local records. The .env.example is a reference; the app does not automatically load .env files.

## Publish to Render

The included render.yaml creates a Python web service and a PostgreSQL database. It selects PAID compute plans for a persistent pilot; review current charges in Render before creating resources. No resources have been created or charged by this project.

1. Create a GitHub repository and upload the contents of this folder at the repository root, including render.yaml and build.sh. Do not upload .env files, db.sqlite3, virtual environments, or secrets.
2. Connect the repository to Render and create a new Blueprint from render.yaml.
3. Review the service/database configuration and displayed costs before deploying. Rename both resource names and the database reference together if they conflict with existing resources.
4. Render installs the requirements and collects CSS/static assets during the build. Its pre-deploy command applies database migrations.
5. The configuration generates a secret key, connects the database internally, and turns debug off. Render's external hostname is added to Django's allowed hosts automatically.
6. When deployment succeeds, open the exact HTTPS URL shown in the Render dashboard. Create a fresh account and run the pilot checklist below. No deployed URL exists until that step succeeds.

The app uses a Render PostgreSQL database so data survives service restarts and redeployments. Backups and restores still depend on the selected database plan. Review those settings before storing important records. External database access is disabled in the Blueprint; the web service uses the private connection.

For a custom domain, add its hostname to DJANGO_ALLOWED_HOSTS (comma-separated). If requests originate on another trusted HTTPS domain, configure DJANGO_CSRF_TRUSTED_ORIGINS with complete HTTPS origins. Never use a wildcard for either setting.

Official references:
- https://render.com/docs/deploy-django
- https://render.com/docs/blueprint-spec
- https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

## Verify

With the virtual environment active and DJANGO_DEBUG=true:

```sh
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py collectstatic --noinput
```

Ten automated tests cover login enforcement, signup/logout, full record lifecycle, owner isolation for reads/writes/deletes, validation, search/filter/sort, follow-up calculations, HTML escaping, CSRF enforcement, and pagination.

Pilot checklist after deployment:

- Create two accounts; verify neither can view or edit the other's applications, including a copied detail URL.
- Save an opportunity, apply with today's date, edit notes and next action, and set a follow-up date.
- Confirm dashboard totals and search/filter results.
- Sign out, sign in, and confirm records remain.
- Refresh and redeploy, then confirm records remain in PostgreSQL.
- Try core screens at phone and desktop sizes and with keyboard navigation.
- Confirm deletion requires a confirmation screen and an explicit POST.

Backend tests and static collection were verified in the development workspace. Real-browser visual verification was blocked by the workspace browser's access gateway. A live PostgreSQL deployment has not yet been tested. Django's deployment check intentionally retains warnings for HSTS subdomains/preload: these should only be enabled after deciding the final domain policy.

## Project map

- manage.py: Django command-line entry point.
- config/settings.py: environment variables, database, authentication, and security.
- config/urls.py: project routes.
- tracker/models.py: database fields and statuses.
- tracker/forms.py: input rules.
- tracker/views.py: request handling, ownership checks, filtering, dashboard.
- tracker/urls.py: application routes.
- tracker/tests.py: automated behavioral tests.
- tracker/migrations/: versioned database schema.
- templates/: HTML screens.
- static/app.css: layout and styling.
- requirements.txt: exact tested package versions.
- render.yaml and build.sh: hosting configuration.

## Decisions and field rules

- Company and job title are required. New opportunities default to Saved.
- Applied, Interviewing, Offer, and Rejected require the original application date; future application dates are rejected. Withdrawn can be used for an opportunity never submitted.
- Notes, next action, URL, and follow-up dates are optional. URLs must be HTTP or HTTPS.
- Follow-up dates before today are overdue; today is due, not overdue. Rejected and Withdrawn records are excluded from follow-up attention lists. Clear the date when an action is complete.
- Date calculations use America/New_York by default, configurable via DJANGO_TIME_ZONE.
- Authentication uses usernames for this prototype. Password recovery requires a later email setup.
- Production refuses to start without DJANGO_SECRET_KEY and DATABASE_URL. Debug is off by default. HTTPS and secure cookies are enabled in production.

## Suggested next iteration

Complete a small pilot before adding features. Prioritize any workflow issues first, then email-based recovery and login throttling before a broad public launch. Resume files, imports, calendar events, and notifications remain outside this MVP.
