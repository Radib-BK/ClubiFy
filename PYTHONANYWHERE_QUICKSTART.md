# PythonAnywhere Quick Start Checklist

## Pre-Deployment Checklist

- [ ] Code is committed to Git (recommended)
- [ ] `.env` file is in `.gitignore` (already done)
- [ ] All migrations are created locally
- [ ] Static files are working locally

## Deployment Steps

1. **Upload Code**
   ```bash
   cd ~
   git clone <your-repo-url>
   cd ClubiFy
   ```

2. **Create Virtual Environment**
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create Database** (in PythonAnywhere Dashboard → Databases tab)
   - Note: Database name format for MySQL: `yourusername$dbname`

5. **Create `.env` File**
   ```bash
   nano .env
   ```
   Add:
   ```env
   SECRET_KEY=<generate-a-secret-key>
   DEBUG=False
   PA_USERNAME=yourusername
   DB_ENGINE=mysql
   DB_NAME=yourusername$clubify_db
   DB_USER=yourusername
   DB_PASSWORD=<your-db-password>
   DB_HOST=yourusername.mysql.pythonanywhere-services.com
   DB_PORT=3306
   ```

6. **Run Migrations**
   ```bash
   source venv/bin/activate
   python manage.py migrate
   python manage.py createsuperuser
   ```

7. **Collect Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

8. **Configure Web App** (in Web tab)
   - Source code: `/home/yourusername/ClubiFy`
   - Working directory: `/home/yourusername/ClubiFy`
   - WSGI file: `/home/yourusername/ClubiFy/clubify/wsgi_pythonanywhere.py`
   - Virtualenv: `/home/yourusername/ClubiFy/venv`

9. **Edit WSGI File**
   - Update `wsgi_pythonanywhere.py` with your username

10. **Configure Static Files** (in Web tab)
    - URL: `/static/` → Directory: `/home/yourusername/ClubiFy/staticfiles`
    - URL: `/media/` → Directory: `/home/yourusername/ClubiFy/media` (if needed)

11. **Reload Web App**
    - Click the green "Reload" button

12. **Test**
    - Visit: `https://yourusername.pythonanywhere.com`

## Generate Secret Key

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Common Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Check for errors
python manage.py check
```

## Troubleshooting

- **Check error logs:** Web tab → Error log
- **Verify database:** Make sure database is created and credentials are correct
- **Check static files:** Ensure `collectstatic` ran successfully
- **Verify WSGI:** Check that WSGI file path is correct

For detailed instructions, see `PYTHONANYWHERE_DEPLOYMENT.md`
