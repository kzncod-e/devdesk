# DevDesk — Unified Developer Workspace: Design Spec

**Date:** 2026-06-12
**Status:** Approved by owner (design review complete)
**Purpose:** A self-hosted web app the owner will use daily while developing other apps. It unifies project/task tracking, reusable code snippets, and bookmarked references in one tool. Secondary goal: demonstrate the full skill set in the VENTURO Fullstack Web Programmer job listing (Python backend, REST APIs, Vue frontend, SQL + NoSQL, security, Git, Docker, CI/CD, VPS deployment, Clean Architecture, TanStack Query).

---

## 1. Overview & Architecture

Everything orbits a **Project**. Each project holds tasks (moved across a board), code snippets (syntax-highlighted, taggable), and bookmarks (docs/API links with auto-fetched metadata). Global search spans all three. Single-user initially, but with real auth so multi-user is trivial later.

**Architecture style:** Clean Architecture monolith.

Backend layering (strict, one-directional dependencies):

```
routers (HTTP)  →  services (business logic)  →  repositories (data access)  →  models/schemas
```

- Routers know nothing about databases.
- Services know nothing about HTTP.
- Repositories are the only layer that touches a database driver.

**Stack:**

| Layer      | Choice |
|------------|--------|
| Backend    | FastAPI, Python 3.12 |
| Relational DB | PostgreSQL (users, projects, tasks) |
| Document DB   | MongoDB (snippets, bookmarks) |
| Frontend   | Nuxt (latest, TypeScript), Tailwind CSS, TanStack Query (Vue adapter), hybrid rendering |
| Auth       | JWT access + refresh tokens, bcrypt password hashing |
| Infra      | Docker Compose; nginx reverse proxy; GitHub Actions CI/CD; single VPS |

**Nuxt rendering strategy (hybrid via route rules in `nuxt.config.ts`):**

- SSR / prerendered: public pages — landing, login, register (fast first paint, SEO-safe, no user data).
- CSR (`ssr: false`): all authenticated routes under `/app/**` (dashboard, boards, snippets, bookmarks) — private, interactive, avoids SSR JWT juggling.
- Production frontend runs the Nitro Node server (not static files).

**Containers (Docker Compose):** `nginx` (reverse proxy, TLS) → `nuxt` (Nitro) + `api` (FastAPI), plus `postgres` and `mongo` with persistent volumes.

**Repository layout:** single monorepo — `backend/`, `frontend/`, `docker-compose.yml`, `.github/workflows/`.

---

## 2. Data Model

### PostgreSQL (strict shape, relational)

- **users** — `id`, `email` (unique), `password_hash`, `name`, `created_at`
- **projects** — `id`, `owner_id → users`, `name`, `description`, `status` (`active` | `archived`), `color`, `created_at`, `updated_at`
- **tasks** — `id`, `project_id → projects`, `title`, `description`, `status` (`todo` | `in_progress` | `done`), `priority`, `position` (board ordering), `due_date`, `created_at`, `updated_at`

### MongoDB (document-shaped, flexible)

- **snippets** — `{ _id, owner_id, project_id?, title, language, code, tags: [], notes, created_at, updated_at }`
- **bookmarks** — `{ _id, owner_id, project_id?, url, title, description, tags: [], favicon, fetched_meta: {…}, created_at }`

Notes:

- `project_id` is **optional** on snippets and bookmarks — general-purpose items are allowed.
- Cross-database references (Mongo docs pointing at Postgres project ids) are resolved and validated in the **service layer**. On project deletion, the service layer either detaches or deletes associated Mongo docs (decision: **detach** — set `project_id` to null — so general-purpose value isn't lost).
- `fetched_meta` is an irregular blob of scraped page metadata — the genuine justification for a document store.

### Search

- Postgres full-text search over projects and tasks.
- MongoDB text indexes over snippets and bookmarks.
- One `/search` endpoint fans out to both and merges grouped results.

---

## 3. API Design

All endpoints under `/api/v1`. OpenAPI docs auto-generated at `/docs`.

**Auth**

- `POST /auth/register`
- `POST /auth/login` → access + refresh JWTs
- `POST /auth/refresh`
- `GET /auth/me`

**Projects**

- CRUD: `GET/POST /projects`, `GET/PATCH/DELETE /projects/{id}`
- `GET /projects/{id}/summary` → counts of tasks/snippets/bookmarks (dashboard)

**Tasks**

- `GET/POST /projects/{id}/tasks` (create/list nested under project)
- `PATCH /tasks/{id}` (edits + status moves; `position` field persists drag-and-drop ordering)
- `DELETE /tasks/{id}`

**Snippets & Bookmarks**

- Flat CRUD at `/snippets` and `/bookmarks`
- Filters: `?project_id=`, `?tag=`, `?language=` (snippets)
- Bookmark creation triggers a background metadata fetch (FastAPI `BackgroundTasks`): scrape page title/description/favicon, update the document asynchronously.

**Search**

- `GET /search?q=` → `{ tasks: [], snippets: [], bookmarks: [] }`

**Conventions**

- Pagination on every list endpoint: `?limit=&offset=`
- Owner scoping enforced in the service layer on every query — no cross-user access even with guessed ids.
- Consistent error envelope: `{ "detail": …, "code": … }`; global exception handlers; correct status codes (401/403/404/422); structured logging.

---

## 4. Security

- Access JWT ~15 min, held in memory client-side; refresh JWT ~7 days in an httpOnly cookie (mitigates XSS token theft).
- bcrypt password hashing.
- Pydantic validation on all inputs; SQLAlchemy parameterized queries (SQL injection defense).
- Strict CORS allow-list.
- Rate limiting on auth endpoints (slowapi).
- Security headers + TLS (Let's Encrypt) at nginx.

---

## 5. Testing

**Backend (pytest):**

1. Unit tests — services with mocked repositories (fast).
2. Integration tests — repositories against real Postgres/Mongo via testcontainers.
3. API tests — FastAPI TestClient: auth flows, ownership checks, validation errors.
- Coverage target: ~70%+ on the service layer.

**Frontend:**

- Vitest + Vue Testing Library for components/composables.
- Playwright smoke tests for the critical path: login → create project → add task.

---

## 6. CI/CD & Operations

**GitHub Actions:**

- Every push/PR: lint (ruff, eslint), type-check (mypy, vue-tsc), run both test suites. Red pipelines block merge.
- Merge to `main`: build Docker images → push to GitHub Container Registry → SSH to VPS → `docker compose pull && docker compose up -d`.

**VPS production:**

- nginx: TLS, security headers, reverse proxy to Nitro and FastAPI.
- Postgres/Mongo on Docker volumes.
- Nightly backups: `pg_dump` + `mongodump` via cron.

---

## 7. Build Roadmap (each milestone shippable)

1. Backend skeleton + auth + projects CRUD, Dockerized, tests green.
2. Tasks + board ordering; Nuxt app with auth flow and project dashboard.
3. Snippets + bookmarks (Mongo) with tagging and background metadata fetch.
4. Global search + UI polish.
5. CI/CD pipeline + VPS deploy — begin daily real-world use.

## 8. Out of Scope (MVP)

- Multi-user collaboration / sharing.
- Microservices (possible later extraction: link-metadata fetcher service).
- Mobile apps, notifications, integrations (GitHub, Slack).
- Rich-text task descriptions beyond Markdown.
