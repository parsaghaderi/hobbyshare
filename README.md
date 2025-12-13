# ShareHobby (Django)

## Local development

1. Create and activate a virtualenv
2. Install deps: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Run server: `python manage.py runserver`

## Environment variables

Copy `.env.example` and export values (or use your process manager / systemd env file).

## Deployment (EC2)

See `deploy/EC2.md`.

