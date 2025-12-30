# ClubiFy — Workflow & Architecture

> See `Requirements.md` for detailed feature specs and user stories.

---

## Architecture Decisions

### Why These App Names?

| App | Purpose | Why This Name? |
|-----|---------|----------------|
| `accounts` | Auth UX (signup/login/logout) | We use Django's built-in User — `accounts` signals "auth actions", not "user model ownership" |
| `clubs` | Club CRUD | Self-explanatory |
| `memberships` | User↔Club relationships, roles, requests | Separate from `clubs` for SRP — complex domain (roles, requests, permissions) |
| `posts` | Blog/News content | Self-explanatory |

### Key Design Choices

| Decision | Choice | Why |
|----------|--------|-----|
| Custom User model? | **No** | MVP scope; Django's User is sufficient |
| Multiple club membership? | **Yes** | Realistic; `Membership` M2M-through handles it |
| Database | **PostgreSQL** | Production-ready, Docker-friendly |

### Model Ownership

| Model | App | Fields |
|-------|-----|--------|
| `Club` | clubs | name, description, created_by (FK→User), created_at, slug |
| `Membership` | memberships | user (FK→User), club (FK→Club), role (ADMIN/MODERATOR/MEMBER), joined_at |
| `MembershipRequest` | memberships | user (FK→User), club (FK→Club), status (PENDING/APPROVED/REJECTED), requested_at, reviewed_by (FK→User, nullable) |
| `Post` | posts | title, body, post_type (BLOG/NEWS), club (FK→Club), author (FK→User), created_at, is_published |

### Import Rules (No Circular Imports)

```
clubs      → imports nothing from project apps
memberships → imports Club from clubs
posts      → imports Club from clubs, helpers from memberships
accounts   → imports nothing from project apps
```

---

## Implementation Checklist

### DAY 0 — Setup

| # | Checkpoint | Branch | Status |
|---|------------|--------|--------|
| 0.1 | Architecture design documented | — | ✅ |
| 0.2 | Git init + .gitignore | `main` | ✅ |

**0.2 Commits:**
- `chore: initialize repository with project documentation`

---

### DAY 1 — Foundation

| # | Checkpoint | Branch | Status |
|---|------------|--------|--------|
| 1.1 | Django project + `accounts` app (signup/login/logout) | `feature/auth` | ✅ |
| 1.2 | `Club` model + admin registration | `feature/clubs` | ✅ |
| 1.3 | Club create view + form | `feature/clubs` | 🔄 |
| 1.4 | Club list page | `feature/clubs` | ⬜ |
| 1.5 | Club detail page | `feature/clubs` | ⬜ |

**1.1 Commits:**
- `feat(accounts): add signup view and template`
- `feat(accounts): add login/logout functionality`

**1.2–1.5 Commits:**
- `feat(clubs): add Club model and admin`
- `feat(clubs): add create view and form`
- `feat(clubs): add list and detail views`

---

### DAY 2 — Membership & Roles

| # | Checkpoint | Branch | Status |
|---|------------|--------|--------|
| 2.1 | `Membership` + `MembershipRequest` models | `feature/memberships` | ⬜ |
| 2.2 | Request membership flow | `feature/memberships` | ⬜ |
| 2.3 | Admin approve/reject UI | `feature/memberships` | ⬜ |
| 2.4 | Role helpers + decorators | `feature/memberships` | ⬜ |
| 2.5 | Member list page | `feature/memberships` | ⬜ |

**Commits:**
- `feat(memberships): add Membership and MembershipRequest models`
- `feat(memberships): add request membership view`
- `feat(memberships): add approve/reject views`
- `feat(memberships): add role helpers and decorators`
- `feat(memberships): add member list view`

---

### DAY 3 — Posts & Docker

| # | Checkpoint | Branch | Status |
|---|------------|--------|--------|
| 3.1 | `Post` model (BLOG/NEWS) | `feature/posts` | ⬜ |
| 3.2 | Post creation with role-based permissions | `feature/posts` | ⬜ |
| 3.3 | Post listing on club detail | `feature/posts` | ⬜ |
| 3.4 | Dockerfile | `feature/docker` | ⬜ |
| 3.5 | docker-compose.yml + .env.example | `feature/docker` | ⬜ |

**Commits:**
- `feat(posts): add Post model with type choices`
- `feat(posts): add post creation view with permissions`
- `feat(posts): add post listing to club detail`
- `feat(docker): add Dockerfile`
- `feat(docker): add docker-compose.yml`

---

### DAY 4 — Testing & Docs

| # | Checkpoint | Branch | Status |
|---|------------|--------|--------|
| 4.1 | Role permission tests | `feature/tests` | ⬜ |
| 4.2 | Happy-path integration test | `feature/tests` | ⬜ |
| 4.3 | README.md completion | `chore/docs` | ⬜ |

**Commits:**
- `test(memberships): add role permission tests`
- `test(posts): add post creation permission tests`
- `test: add happy-path integration test`
- `docs: complete README with setup instructions`

---

## Quick Reference

### URL Routes

| Route | App | Access |
|-------|-----|--------|
| `/accounts/signup/`, `/accounts/login/`, `/accounts/logout/` | accounts | Public |
| `/clubs/`, `/clubs/<id>/` | clubs | Public |
| `/clubs/new/` | clubs | Auth |
| `/clubs/<id>/join/` | memberships | Auth |
| `/clubs/<id>/members/` | memberships | Members |
| `/clubs/<id>/requests/` | memberships | Admin |
| `/clubs/<id>/posts/new/` | posts | Members |

### Role Permissions

| Action | Member | Moderator | Admin |
|--------|--------|-----------|-------|
| View member list | ✅ | ✅ | ✅ |
| Create BLOG | ✅ | ✅ | ✅ |
| Create NEWS | ❌ | ✅ | ✅ |
| Approve requests | ❌ | ❌ | ✅ |

---

*End of Document*
