<table>
  <tr>
    <td>
      <img src="screenshots/clubify_logo.png" alt="ClubiFy logo" height="64">
    </td>
    <td>
      <h1>ClubiFy</h1>
    </td>
    <td align="right">
      <a href="https://radibbk.pythonanywhere.com/">
        <img src="https://img.shields.io/badge/Live_Demo-1E40AF?style=for-the-badge&logo=globe&logoColor=white" alt="Live Demo">
      </a>
    </td>
  </tr>
</table>

## A Django-powered club management platform for discovering clubs, managing role-based memberships, and publishing news/blog posts.


## Highlights
- Authentication with Google OAuth (signup, login, logout)
- Create and browse clubs
- Role-based memberships (Admin, Moderator, Member)
- Membership requests with approve / reject workflow
- Publish blog posts (members) and news posts (mods / admins)
- Bookmark important posts
- Delete posts (mods/admins) and remove members (admins)
- **Like, Comment & Share** on posts
- AI post summarizer
- User profiles with memberships and pending requests
- Responsive UI with Tailwind CSS

---

## Tech Stack

| Backend | Frontend | Infra/Tooling |
| --- | --- | --- |
| ![Django](https://img.shields.io/badge/Django-092E20?logo=django&logoColor=white) ![Python](https://img.shields.io/badge/Python_3.10+-3776AB?logo=python&logoColor=white) ![Hugging Face](https://img.shields.io/badge/Hugging_Face-FFD21E?logo=huggingface&logoColor=black) | ![Tailwind](https://img.shields.io/badge/Tailwind_CSS-06B6D4?logo=tailwindcss&logoColor=white) | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white) ![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white) ![Gunicorn](https://img.shields.io/badge/Gunicorn-499848?logo=gunicorn&logoColor=white) ![WhiteNoise](https://img.shields.io/badge/WhiteNoise-555?logo=python&logoColor=white) |

---

## Quick Links
- [🌐 Live Demo](https://radibbk.pythonanywhere.com/)
- [Screenshots](#screenshots-user-flow)
- [Setup (Local)](#option-1-local-development-setup)
- [Setup (Docker)](#option-2-docker-setup-recommended)
- [Project Structure](#project-structure)

---

## Screenshots

### Getting Started

| Browse Clubs |
|:------------:|
| ![Club List](screenshots/club-list.png) |
| Discover and explore available clubs |

| Register | Create Club |
|:--------:|:-----------:|
| ![Registration](screenshots/registration.png) | ![Create Club](screenshots/create-club.png) |
| Create your account to join clubs | Start your own community |

### Club Management

| Club Details |
|:------------:|
| ![Club Details](screenshots/club-details.png) |
| View club info, news & blogs |

| Member Management |
|:-----------------:|
| ![Club Members](screenshots/club-members.png) |
| Manage members and roles |

### Content & Interaction

| Create Post | Browse Posts |
|:-----------:|:------------:|
| ![Create Post](screenshots/create-post.png) | ![All Posts](screenshots/all-posts.png) |
| Write blog posts or news updates | View all posts in a club |

| Post Details |
|:------------:|
| ![Post Details](screenshots/post-details.png) |
| Read full post content |

| Comments | Share |
|:--------:|:-----:|
| ![Comments](screenshots/comment-section.png) | ![Share Modal](screenshots/share-modal.png) |
| Engage with the community | Share to social media |

### Features

| AI Summarizer |
|:-------------:|
| ![AI Summarize](screenshots/ai-summarize.png) |
| Get AI-powered post summaries |

| User Profile |
|:------------:|
| ![Profile](screenshots/profile.png) |
| View your memberships & activity |



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
git clone https://github.com/Radib-BK/ClubiFy.git
cd ClubiFy
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
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
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

#### Prerequisites
- Docker & Docker Compose installed

#### Setup

1. **Create `.env` file** (optional, but recommended):
   ```bash
   # Copy the existing .env or create one with these values:
   SECRET_KEY=your-secret-key
   DEBUG=True
   DB_NAME=
   DB_USER=
   DB_PASSWORD=
   GOOGLE_CLIENT_ID=your-id
   GOOGLE_CLIENT_SECRET=your-secret
   HF_SUMMARIZATION_MODEL=sshleifer/distilbart-cnn-12-6
   ```
   
   **Note:** `.env` is **optional** - if not provided, defaults are used.

2. **Build and start containers**:
   ```bash
   docker-compose build web  # First time (downloads Hugging Face model ~5 min)
   docker-compose up -d       # Start all services
   ```

3. **Create admin user**:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

#### Access
- App: http://localhost:8001
- Admin: http://localhost:8001/admin
- PostgreSQL: localhost:5433

#### Common Commands
```bash
# View logs
docker-compose logs -f web

# Stop containers
docker-compose down

# Rebuild after code changes
docker-compose build web && docker-compose up -d

# Run Django commands
docker-compose exec web python manage.py <command>
```

#### About the AI Summarizer
- The Hugging Face model is **pre-downloaded during the first build** (takes ~5 minutes)
- Model is **cached in Docker volume** for fast subsequent starts
- To change model, edit `.env`:
  ```env
  HF_SUMMARIZATION_MODEL=facebook/bart-large-cnn
  ```
  Then rebuild: `docker-compose build web`

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
