# Club Project (Django) — 4‑Day MVP Requirements

## Goal
Build a small Django web app where people can **create clubs**, others can **browse clubs**, **request to join**, and club members can **post content** with **role-based permissions**. The project should be completable in **~4 days** (3 days build + 1 day testing/feedback) and cover core Django concepts.

---

## Scope Review (4‑day reality check)

### MVP (recommended for 4 days)
- **Auth**: signup, login, logout.
- **Clubs**: create club, list clubs, view club detail.
- **Membership**:
  - Logged-in users can **request membership** from club detail.
  - Club **admin** can **approve/reject** membership requests.
  - Roles inside a club: **admin**, **moderator**, **member** (general user).
- **Posts**:
  - Members can create **Blog** posts.
  - Admin + moderator can also create **News** posts.
  - Everyone can view published posts on club page (including guests).
- **Dockerized run**: app runs via Docker / Docker Compose.

### Clarifications / small adjustments
- A “guest user” (not logged in) can **browse clubs** and **view club pages**.
- “Guest can join a club” should mean: guest clicks **Join**, is prompted to **sign up / log in**, then a **membership request** is created.

---

## User Types & Permissions

### Global (site-level)
- **Guest (not logged in)**:
  - View club list
  - View club detail page (including published posts)
  - Sign up / log in
- **Logged-in user (not yet a member of a club)**:
  - Request membership on a club
  - See their pending requests (optional but small)

### Club-level roles
- **Admin**:
  - Create/edit the club (at least at creation; edit optional)
  - Approve/reject membership requests
  - Assign roles (optional for MVP; can be admin-only)
  - Create Blog + News posts
- **Moderator**:
  - Create Blog + News posts
- **Member (general user)**:
  - Create Blog posts

Notes:
- A user can be a member of multiple clubs (recommended), but you can also restrict to one club for simplicity.

---

## User Stories (Clarification)

### Guest (not logged in)
- As a guest, I can browse the club list and open a club page to understand what it’s about.
- As a guest, when I click **Join**, I’m asked to **sign up / log in** first.

### Logged-in user (not a member yet)
- As a logged-in user, I can request to join a club from the club home page.
- As a logged-in user, I can see that my request is **pending** and I cannot post until approved.

### Member (general club member)
- As a member, I can view the club home page and see the club’s **member list**.
- As a member, I can create a **Blog** post inside the club.
- As a member, I cannot create **News** posts.

### Moderator
- As a moderator, I can do everything a member can.
- As a moderator, I can create **News** posts as well as **Blog** posts.

### Admin
- As an admin, I can create a club and become its admin automatically.
- As an admin, I can review **pending membership requests** and approve/reject them.
- As an admin, I can create **News** and **Blog** posts.
- As an admin, I can optionally promote a member to **Moderator**.

---

## Core Features (Functional Requirements)

### 1) Authentication
- Users can sign up with:
  - username (or email) + password
- Users can log in/out.
- After login, user is redirected back to the page they came from (optional).

### 2) Club Registration (Creation)
- A logged-in user can create a club with:
  - Club name (required, unique recommended)
  - Description/details (required)
- The creator automatically becomes the club’s **Admin**.

### 3) Club Discovery
- Club list page shows clubs as **cards**:
  - Name
  - Short description excerpt
  - Member count (optional)
  - Button/link to club detail
- Club detail (club “home”) page is similar to a Facebook page and includes:
  - Banner/cover image area (can be a placeholder in MVP)
  - Club profile image/avatar area (can be a placeholder in MVP)
  - Club name + short description/about section
  - Join/request button (depending on user state)
  - Tabs or sections for:
    - News
    - Blogs
  - Sidebar or related info (keep simple):
    - Member count (optional)
    - Created date (optional)
    - Admin/moderator list (optional)
    - Member list link/section (members-only)
  - Footer (basic site footer is enough)

### 4) Membership Workflow
- Logged-in users can request membership:
  - One pending request per club per user
  - Duplicate requests are prevented
- Club Admin can:
  - View pending membership requests
  - Approve or reject each request
- On approval:
  - User becomes a **Member** by default
  - (Optional) Admin can promote to Moderator
- Club members (Admin/Moderator/Member) can:
  - View the club’s **member list**

### 5) Posts (Blog + News)
To keep the model simple, implement a single **Post** concept with a `type`:
- `type = BLOG | NEWS`
- Fields:
  - title
  - body/content
  - club reference
  - author reference
  - created_at
  - (optional) is_published boolean

Permissions:
- Member: can create BLOG
- Moderator: can create BLOG and NEWS
- Admin: can create BLOG and NEWS

---

## Pages / Screens (Minimum UI)
- **Home / Club list**: `/clubs/`
- **Club create**: `/clubs/new/`
- **Club detail**: `/clubs/<slug-or-id>/`
- **Club member list** (members-only): `/clubs/<id>/members/`
- **Membership request action**: button on detail page
- **Admin membership requests**: `/clubs/<id>/requests/`
- **Create post**: `/clubs/<id>/posts/new/`
- **Auth**: `/accounts/signup/`, `/accounts/login/`, `/accounts/logout/`

---

## Non-Functional Requirements
- **Security**
  - Only authorized roles can perform role-limited actions
  - CSRF protection enabled
  - Basic validation and error handling (Django forms)
- **Usability**
  - Clear call-to-action buttons: Join / Request Pending / Member
  - Helpful flash messages (Django messages framework)
- **Maintainability**
  - Keep apps separated: e.g., `clubs`, `memberships`, `posts`
  - Everything can be managed from **Django Admin**:
    - All project models must be **registered** in Django admin
    - Admin can create/edit/delete records for clubs, memberships, membership requests, and posts
    - (Optional) Add list/search filters for faster management

---

## What Django Concepts This Covers
- Project/app structure, settings
- Models + migrations + relationships
- Authentication (sessions) + authorization (permissions)
- Forms / ModelForms and server-side validation
- Function-based or class-based views, templates, URL routing
- Admin customization (optional)
- Testing basics (optional but recommended)
- Docker + environment variables

---

## Out of Scope (for the 3‑day build)
- Email invite flow, password reset emails
- Social login
- Real-time chat
- File uploads (club logos, post images)
- Full-text search / Elasticsearch
- Complex moderation and audit logs

---

## Milestone Plan (4 Days)

### Day 1 — Foundation
- Django project setup + apps
- Auth pages (signup/login/logout)
- Club create/list/detail (templates + forms)
- Basic styling (simple CSS or minimal framework)

### Day 2 — Membership & Roles
- Membership request flow
- Admin approval/rejection UI
- Role checks (decorators/helpers) + template conditionals

### Day 3 — Posts + Docker
- Post creation + listing on club page
- Enforce post type permissions by role
- Dockerfile + docker-compose
- Quick smoke test + README run instructions

### Day 4 — Testing + Real User Feedback
- Add a small test suite:
  - Model validation / constraints (where applicable)
  - Permission tests for roles (who can create News vs Blog, who can approve requests)
  - A couple of happy-path integration tests (signup → request membership → approve → create post)
- Ask 1 real user (friend/classmate) to try the app for 15–30 minutes:
  - Observe where they get confused
  - Collect feedback: unclear buttons, missing messages, broken flows, UI friction
- Fix the top issues and update the README with known limitations / next steps

---

## Development Workflow (Git/GitHub)
- Create a **GitHub repository** for this project before starting development.
- Use a **feature-branch workflow**:
  - Create a new branch for each feature (e.g., `feature/auth`, `feature/clubs`, `feature/membership`, `feature/posts`, `feature/docker`)
  - Open a Pull Request (optional if working solo) and merge to `main` after the feature is stable
  - Keep commits small and descriptive
- After completion, update the repository `README.md` to include:
  - A short project description and screenshots (optional)
  - Setup and run instructions (local + Docker)
  - Default admin credentials creation steps (e.g., how to create a superuser)

---

## Docker Requirement (Target)
Deliver the project so it can be run with:
- `docker compose up --build`

Minimum docker setup should include:
- Web service (Django)
- SQLite is fine for MVP; PostgreSQL is optional (adds setup time)

---

## Open Questions (decide early to avoid scope creep)
- Can a user belong to **multiple clubs**? (recommended: yes)
- Is club editing required? (recommended: optional)
- Should posts be editable/deletable? (recommended: optional; create-only is fine)
- Do you want “News” to be highlighted separately on the club page? (recommended: yes, but same Post model)


