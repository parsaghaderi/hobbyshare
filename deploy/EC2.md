# EC2 deployment (Ubuntu + Nginx + Gunicorn + systemd)

These steps assume you deploy behind Nginx and run Gunicorn via systemd.

## Server prerequisites

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip nginx
```

## App setup

```bash
sudo mkdir -p /srv/sharehobby
sudo chown -R ubuntu:ubuntu /srv/sharehobby
```

Upload the repo to `/srv/sharehobby/app` (via `git clone`, `rsync`, or `scp`).

```bash
cd /srv/sharehobby/app
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

## Environment

Create `/srv/sharehobby/env`:

```bash
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=change-me
DJANGO_ALLOWED_HOSTS=your-domain,ec2-3-144-197-137.us-east-2.compute.amazonaws.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain,https://ec2-3-144-197-137.us-east-2.compute.amazonaws.com
DJANGO_SECURE_SSL_REDIRECT=1
DJANGO_SESSION_COOKIE_SECURE=1
DJANGO_CSRF_COOKIE_SECURE=1
DJANGO_SECURE_PROXY_SSL_HEADER=1
```

## systemd unit

Create `/etc/systemd/system/sharehobby.service`:

```ini
[Unit]
Description=ShareHobby Gunicorn
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/srv/sharehobby/app
EnvironmentFile=/srv/sharehobby/env
ExecStart=/srv/sharehobby/app/.venv/bin/gunicorn hobbyhub.wsgi:application --bind 127.0.0.1:8000 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sharehobby
sudo systemctl status sharehobby --no-pager
```

## Nginx

Create `/etc/nginx/sites-available/sharehobby`:

```nginx
server {
    listen 80;
    server_name your-domain ec2-3-144-197-137.us-east-2.compute.amazonaws.com;

    location /static/ {
        alias /srv/sharehobby/app/staticfiles/;
    }

    location /media/ {
        alias /srv/sharehobby/app/media/;
    }

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

Enable and reload:

```bash
sudo ln -sf /etc/nginx/sites-available/sharehobby /etc/nginx/sites-enabled/sharehobby
sudo nginx -t
sudo systemctl reload nginx
```

Add TLS (recommended) using certbot or your preferred method.

