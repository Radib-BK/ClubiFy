# PythonAnywhere Deployment Guide for ClubiFy

This guide will walk you through deploying your ClubiFy Django project to PythonAnywhere.

## Prerequisites

1. A PythonAnywhere account (free or paid)
2. Your project code (preferably in a Git repository)
3. Basic knowledge of Django and PythonAnywhere

## Step 1: Create a PythonAnywhere Account

1. Go to [pythonanywhere.com](https://www.pythonanywhere.com)
2. Sign up for a free account (or use an existing account)
3. Note your username - you'll need it later

## Step 2: Upload Your Code

### Option A: Using Git (Recommended)

1. **In PythonAnywhere Bash Console:**
   ```bash
   cd ~
   git clone https://github.com/yourusername/ClubiFy.git
   # Or use your Git repository URL
   cd ClubiFy
   ```

### Option B: Using Files Tab

1. Go to the **Files** tab in PythonAnywhere
2. Navigate to `/home/yourusername/`
3. Upload your project files (or use the upload button)

## Step 3: Set Up Virtual Environment

1. **In PythonAnywhere Bash Console:**
   ```bash
   cd ~/ClubiFy
   
   # Create virtual environment
   python3.10 -m venv venv
   # Or python3.9, python3.11, etc. - check what Python versions are available
   
   # Activate virtual environment
   source venv/bin/activate
   
   # Upgrade pip
   pip install --upgrade pip
   ```

## Step 4: Install Dependencies

1. **Still in the virtual environment:**
   ```bash
   # Install MySQL client if using MySQL (free accounts)
   pip install mysqlclient
   
   # Install all other dependencies
   pip install -r requirements.txt
   ```

   **Note:** If you're using MySQL (free accounts), you may need to install `mysqlclient`. If that fails, try:
   ```bash
   pip install pymysql
   ```
   Then add this to your `settings.py` (already handled in the updated settings):
   ```python
   import pymysql
   pymysql.install_as_MySQLdb()
   ```

## Step 5: Set Up Database

### For MySQL (Free Accounts):

1. **In PythonAnywhere Dashboard:**
   - Go to **Databases** tab
   - Create a new MySQL database
   - Note the database name, username, and password

2. **Create a `.env` file in your project root:**
   ```bash
   cd ~/ClubiFy
   nano .env
   ```

3. **Add these variables to `.env`:**
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   PA_USERNAME=yourusername
   DB_ENGINE=mysql
   DB_NAME=yourusername$clubify_db
   DB_USER=yourusername
   DB_PASSWORD=your-database-password
   DB_HOST=yourusername.mysql.pythonanywhere-services.com
   DB_PORT=3306
   ```

### For PostgreSQL (Paid Accounts):

1. **In PythonAnywhere Dashboard:**
   - Go to **Databases** tab
   - Create a new PostgreSQL database
   - Note the connection details

2. **Add these variables to `.env`:**
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   PA_USERNAME=yourusername
   DB_ENGINE=postgresql
   DB_NAME=your-database-name
   DB_USER=your-database-user
   DB_PASSWORD=your-database-password
   DB_HOST=your-database-host
   DB_PORT=5432
   ```

## Step 6: Run Migrations

1. **In PythonAnywhere Bash Console (with venv activated):**
   ```bash
   cd ~/ClubiFy
   source venv/bin/activate
   
   # Run migrations
   python manage.py migrate
   
   # Create superuser (optional)
   python manage.py createsuperuser
   ```

## Step 7: Collect Static Files

1. **In PythonAnywhere Bash Console (with venv activated):**
   ```bash
   python manage.py collectstatic --noinput
   ```

## Step 8: Configure WSGI File

1. **Edit the WSGI file:**
   - Go to **Web** tab in PythonAnywhere
   - Click on **WSGI configuration file** link
   - Replace the entire content with:

   ```python
   import os
   import sys
   
   # Add your project directory to the Python path
   path = '/home/yourusername/ClubiFy'  # CHANGE 'yourusername' to your actual username
   if path not in sys.path:
       sys.path.insert(0, path)
   
   # Set the Django settings module
   os.environ['DJANGO_SETTINGS_MODULE'] = 'clubify.settings'
   
   # Set PythonAnywhere username
   os.environ['PA_USERNAME'] = 'yourusername'  # CHANGE 'yourusername' to your actual username
   
   # Import Django's WSGI application
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

   **OR** use the provided `wsgi_pythonanywhere.py` file:
   - Edit `/home/yourusername/ClubiFy/clubify/wsgi_pythonanywhere.py`
   - Replace `yourusername` with your actual PythonAnywhere username
   - Point the WSGI configuration file to: `/home/yourusername/ClubiFy/clubify/wsgi_pythonanywhere.py`

## Step 9: Configure Web App

1. **In PythonAnywhere Web tab:**
   - **Source code:** `/home/yourusername/ClubiFy`
   - **Working directory:** `/home/yourusername/ClubiFy`
   - **WSGI configuration file:** `/home/yourusername/ClubiFy/clubify/wsgi_pythonanywhere.py`
   - **Virtualenv:** `/home/yourusername/ClubiFy/venv`

## Step 10: Configure Static Files Mapping

1. **In PythonAnywhere Web tab, add Static files mapping:**
   - **URL:** `/static/`
   - **Directory:** `/home/yourusername/ClubiFy/staticfiles`

2. **If you have media files, add Media files mapping:**
   - **URL:** `/media/`
   - **Directory:** `/home/yourusername/ClubiFy/media`

## Step 11: Reload Web App

1. **In PythonAnywhere Web tab:**
   - Click the green **Reload** button
   - Wait for the reload to complete

## Step 12: Test Your Application

1. Visit your website: `https://yourusername.pythonanywhere.com`
2. Test the main functionality
3. Check error logs if something doesn't work:
   - Go to **Web** tab → **Error log** link

## Troubleshooting

### Common Issues:

1. **Import Errors:**
   - Make sure your virtual environment is activated
   - Check that all dependencies are installed
   - Verify the Python path in WSGI file

2. **Database Connection Errors:**
   - Verify database credentials in `.env` file
   - Check that database is created in PythonAnywhere
   - For MySQL, ensure `mysqlclient` or `pymysql` is installed

3. **Static Files Not Loading:**
   - Run `python manage.py collectstatic`
   - Check static files mapping in Web tab
   - Verify `STATIC_ROOT` path

4. **500 Internal Server Error:**
   - Check error logs in Web tab
   - Verify `ALLOWED_HOSTS` includes your domain
   - Check `.env` file exists and has correct values

5. **Module Not Found (spacy/pytextrank):**
   - These packages can be large. If installation fails:
     ```bash
     pip install --no-cache-dir spacy
     python -m spacy download en_core_web_sm
     ```
   - Or consider removing these dependencies if not critical

### Viewing Logs:

- **Error log:** Web tab → Error log link
- **Server log:** Web tab → Server log link
- **Access log:** Web tab → Access log link

## Updating Your Application

When you make changes to your code:

1. **Pull latest changes (if using Git):**
   ```bash
   cd ~/ClubiFy
   git pull
   ```

2. **Run migrations if needed:**
   ```bash
   source venv/bin/activate
   python manage.py migrate
   ```

3. **Collect static files if changed:**
   ```bash
   python manage.py collectstatic --noinput
   ```

4. **Reload web app:**
   - Go to Web tab → Click Reload button

## Security Checklist

- [ ] `DEBUG = False` in production
- [ ] Strong `SECRET_KEY` set in `.env`
- [ ] `.env` file is in `.gitignore` (already done)
- [ ] Database credentials are secure
- [ ] `ALLOWED_HOSTS` is properly configured
- [ ] Static files are properly served

## Additional Notes

- **Free accounts:** Limited to MySQL, 1 web app, and some restrictions
- **Paid accounts:** Can use PostgreSQL, multiple web apps, more resources
- **Scheduled tasks:** Use Tasks tab for cron jobs or scheduled tasks
- **Consoles:** Use Bash console for command-line operations
- **Files:** Use Files tab to browse and edit files

## Support

- PythonAnywhere Help: https://help.pythonanywhere.com
- Django Deployment: https://docs.djangoproject.com/en/4.1/howto/deployment/
- PythonAnywhere Community: https://www.pythonanywhere.com/community/
