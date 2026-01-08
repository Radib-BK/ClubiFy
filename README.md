<h1>
  <img src="screenshots/clubify_logo.png" alt="ClubiFy logo" height="52" style="vertical-align:  middle; margin-right: 10px;">
  ClubiFy
</h1>

## A Django-powered club management platform for discovering clubs, managing role-based memberships, and publishing news/blog posts.


## Highlights
- Authentication (signup, login, logout)
- Create and browse clubs
- Role-based memberships (Admin, Moderator, Member)
- Membership requests with approve / reject workflow
- Publish blog posts (members) and news posts (mods / admins)
- Delete posts (mods/admins) and remove members (admins)
- AI post summarizer
- User profiles with memberships and pending requests
- Responsive UI with Tailwind CSS

---

## Tech Stack

| Backend | Frontend | Infra/Tooling |
| --- | --- | --- |
| ![Django](https://img.shields.io/badge/Django-092E20?logo=django&logoColor=white) ![Python](https://img.shields.io/badge/Python_3.10+-3776AB?logo=python&logoColor=white) | ![Tailwind](https://img.shields.io/badge/Tailwind_CSS-06B6D4?logo=tailwindcss&logoColor=white) | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white) ![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white) ![Gunicorn](https://img.shields.io/badge/Gunicorn-499848?logo=gunicorn&logoColor=white) ![WhiteNoise](https://img.shields.io/badge/WhiteNoise-555?logo=python&logoColor=white) |

---

## Quick Links
- [Screenshots](#screenshots-user-flow)
- [Setup (Local)](#option-1-local-development-setup)
- [Setup (Docker)](#option-2-docker-setup-recommended-for-development)
- [Project Structure](#project-structure)
- [Role Permissions](#role-permissions)

---

## Screenshots (User Flow)

1) Discover clubs  
![Club List](screenshots/club-list.png)

2) Learn about a club  
![Club Details](screenshots/club-details.png)

3) Join and manage members  
![Club Members](screenshots/club-members.png)

4) Register and get started  
![Registration](screenshots/registration.png)

5) Create a new club  
![Create Club](screenshots/create-club.png)

6) Browse posts inside a club  
![All Posts](screenshots/all-posts.png)

7) Read a post and interact  
![Post Details](screenshots/post-details.png)

8) Summarize with AI  
![AI Summarize](screenshots/ai-summarize.png)

9) Your profile at a glance  
![Profile](screenshots/profile.png)



---

## Setup Instructions

### Prerequisites

**For Local Development:**
- Python 3.10+
- PostgreSQL 13+
- Node.js (for Tailwind CSS)

**For Docker Setup:**
- Docker and Docker Compose
- (Node.js and Python are included in the container)

---

### Option 1: Local Development Setup

#### 1. Clone the repository

```bash
git clone https://github.com/your-username/clubify.git
cd clubify
```

#### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

#### 3. Install dependencies

```bash
pip install -r requirements.txt
```

#### 4. Create environment file

Create a `.env` file in the project root:

```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=clubify_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```

#### 5. Create PostgreSQL database

```bash
psql -U postgres
CREATE DATABASE clubify_db;
\q
```

#### 6. Run migrations

```bash
python manage.py migrate
```

#### 7. Create superuser (admin account)

```bash
python manage.py createsuperuser
```

Follow the prompts to set username, email, and password.

#### 8. Run the development server

```bash
python manage.py runserver
```

Access the application at `http://localhost:8000`

Admin panel at `http://localhost:8000/admin`

---

### Option 2: Docker Setup (Recommended)

The entrypoint auto-runs migrations and Tailwind watch. Use these commands:

```bash
# Start (first time or after Dockerfile changes)
docker-compose up -d --build

# Follow logs (Django + Tailwind)
docker-compose logs -f web

# Create admin user
docker-compose exec web python manage.py createsuperuser
```

Access:
- App: http://localhost:8001
- Admin: http://localhost:8001/admin
- PostgreSQL: exposed on 5433 (container 5432)

Notes:
- Code changes auto-reload; Tailwind auto-compiles.
- To stop: `docker-compose down` (add `-v` to drop DB volume).

---

## Project Structure

```
clubify/
├── accounts/          # User authentication
├── clubs/             # Club management
├── memberships/       # Membership and roles
├── posts/             # Blog and news posts
├── templates/         # Base templates
├── static/            # CSS (Tailwind)
├── clubify/           # Project settings
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## License

MIT License
