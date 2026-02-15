# Production Deployment (Ubuntu 24.04 + Gunicorn + Nginx)

This guide deploys **ClubiFy** on a fresh Ubuntu 24.04 VM using **PostgreSQL**, **Gunicorn**, and **Nginx**.

---

## 1. System Packages

Install required packages:

```bash
sudo apt update
sudo apt install -y python3-venv python3-dev build-essential \
  libpq-dev postgresql postgresql-contrib git nginx
```

Why:
- `python3-venv`, `python3-dev`, `build-essential` for Python deps
- `libpq-dev` for PostgreSQL driver build
- `postgresql` for DB
- `nginx` for static files + reverse proxy

---

## 2. PostgreSQL Database + User

Create database and user:

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE clubify_db;
CREATE USER clubify_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE clubify_db TO clubify_user;
\q
```

### IMPORTANT: Grant schema permissions (fixes "permission denied for schema public")

```bash
sudo -u postgres psql -d clubify_db
```

```sql
ALTER SCHEMA public OWNER TO clubify_user;
GRANT ALL ON SCHEMA public TO clubify_user;
GRANT ALL PRIVILEGES ON DATABASE clubify_db TO clubify_user;
\q
```

---

## 3. Clone Repo

```bash
cd ~
git clone https://github.com/Radib-BK/ClubiFy.git
cd ClubiFy
```

---

## 4. Virtualenv + Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -r requirements.txt
```

Optional (AI summarizer):

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

---

## 5. Create `.env`

Create `.env` in the project root:

```bash
SECRET_KEY=your-strong-secret
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,VM_IP_OR_DOMAIN

DB_NAME=clubify_db
DB_USER=clubify_user
DB_PASSWORD=strong_password
DB_HOST=localhost
DB_PORT=5432

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

SKIP_SUMMARIZER_PRELOAD=true
HF_HOME=/home/youruser/.cache/huggingface
```

---

## 6. Django Setup

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

---

## 7. Gunicorn (Test Run)

```bash
gunicorn --bind 0.0.0.0:8000 clubify.wsgi:application
```

Visit `http://VM_IP:8000` then stop with `Ctrl+C`.

---

## 8. systemd Service (Gunicorn)

Create:

```bash
sudo nano /etc/systemd/system/clubify.service
```

Paste (update `User` + paths):

```ini
[Unit]
Description=ClubiFy Gunicorn
After=network.target

[Service]
User=youruser
Group=www-data
WorkingDirectory=/home/youruser/ClubiFy
EnvironmentFile=/home/youruser/ClubiFy/.env
RuntimeDirectory=clubify
ExecStart=/home/youruser/ClubiFy/.venv/bin/gunicorn \
  --access-logfile - \
  --workers 3 \
  --bind unix:/run/clubify/clubify.sock \
  clubify.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now clubify
sudo systemctl status clubify
```

---

## 9. Nginx Config (Static + Proxy)

Create:

```bash
sudo nano /etc/nginx/sites-available/clubify
```

```nginx
server {
    listen 80;
    server_name VM_IP_OR_DOMAIN;

    client_max_body_size 20M;

    location /static/ {
        alias /home/youruser/ClubiFy/staticfiles/;
    }

    location /media/ {
        alias /home/youruser/ClubiFy/media/;
    }

    location / {
        proxy_pass http://unix:/run/clubify/clubify.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/clubify /etc/nginx/sites-enabled/clubify
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

---

## 10. Static File Permissions

Ensure Nginx can read static files:

```bash
sudo chmod 755 /home/youruser
sudo chmod 755 /home/youruser/ClubiFy
sudo find /home/youruser/ClubiFy/staticfiles -type d -exec chmod 755 {} \;
sudo find /home/youruser/ClubiFy/staticfiles -type f -exec chmod 644 {} \;
```

If you get `403` for static files, also check AppArmor:

```bash
sudo aa-status | grep nginx
sudo tail -n 50 /var/log/syslog | grep -i apparmor
```

---

## 11. Firewall (Optional)

```bash
sudo ufw allow 'Nginx Full'
sudo ufw status
```

---

## 12. Google OAuth on Private IP

Google OAuth blocks private IPs like `http://172.16.x.x`.
Use a hostname:

1. Add in your **host machine** `/etc/hosts`:
   ```
   172.16.x.x clubify.local
   ```
2. Update `.env` `ALLOWED_HOSTS` with `clubify.local`
3. In Google Cloud Console:
   - Authorized JS origin: `http://clubify.local`
   - Redirect URI: `http://clubify.local/accounts/google/login/callback/`

---

## 13. Visit the App

Open:
- `http://VM_IP_OR_DOMAIN/`

---

## Common Fixes

- **Permission denied for schema public**:
  Run the schema grants in Step 2.
- **No CSS / static 403**:
  Check Nginx `alias` and permissions in Step 10.
- **OAuth error on private IP**:
  Use a hostname as in Step 12.
