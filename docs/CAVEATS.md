# Caveats & shortcomings

## Production readiness

- `hobbyhub/settings.py` is now env-driven, but production still requires you to set a real `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, and `DJANGO_CSRF_TRUSTED_ORIGINS`.
- TLS termination/HTTPS redirect depends on your reverse proxy setup; review `DJANGO_SECURE_SSL_REDIRECT` and `DJANGO_SECURE_PROXY_SSL_HEADER`.
- Static/media serving needs a reverse proxy (recommended) and `collectstatic` for production; local `DEBUG` media serving does not apply.

## Database

- Default DB is SQLite (`db.sqlite3`). This is convenient but a poor choice for concurrent production traffic; consider Postgres.
- Migrations were missing for `Hobby.start_datetime`, `Hobby.end_datetime`, and `Hobby.recurrence`; `core/migrations/0006_hobby_schedule_fields.py` fixes this. Any deployed DB must be migrated.

## API / DRF

- Pagination warnings were caused by unordered querysets; API viewsets now apply deterministic ordering.
- Auth is currently session/basic based. For a public API, consider token/JWT and rate limiting.

## Security

- Do not run with `DJANGO_DEBUG=1` in production.
- Do not keep secrets in git; use env files, SSM, or a secrets manager.

## Ops / tooling

- No CI pipeline, formatting/linting, or dependency scanning is set up.
- `Pillow` is not pinned to an exact version; builds may become non-reproducible.

