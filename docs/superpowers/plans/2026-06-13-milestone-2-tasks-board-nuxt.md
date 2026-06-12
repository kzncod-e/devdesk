# DevDesk Milestone 2: Tasks + Board Ordering + Nuxt App — Implementation Plan

> **For agentic workers:** Execute task-by-task with strict TDD where a task is testable:
> write the failing test, run it to confirm it fails, implement, run it to confirm it
> passes, then commit. Infrastructure/scaffold steps are verified by smoke checks.

**Goal:** Tasks CRUD with board `position` ordering and `GET /projects/{id}/summary` on the
backend; a Nuxt (TypeScript, Tailwind, TanStack Query) frontend with auth flow (login /
register / refresh), project dashboard, and a drag-and-drop task board. Stack shippable via
Docker Compose.

**Scope decisions (deviations flagged):**
- Refresh JWT moves to an httpOnly cookie (spec §4) — backend sets/reads it; body field kept
  for API clients and tests.
- Alembic deferred again: M2 only adds the `tasks` table; `create_all` handles new tables and
  there is no production data until M5. Revisit when an existing table must be altered.
- Playwright smoke deferred to M5 (lands with CI). Frontend tested with Vitest.
- `position` is a float; clients order by midpoint insertion (`(prev+next)/2`), append =
  `max + 1024`. No reindexing needed at MVP scale.
- Frontend calls the API same-origin via `/api/**` (Nitro dev proxy locally, proxy route rule
  in the container build) so the httpOnly cookie works without cross-site SameSite issues.

---

### Task 1: Refresh-token httpOnly cookie (backend)

- [x] Failing API tests: login sets an httpOnly `refresh_token` cookie; `/auth/refresh` works
  with the cookie alone (no body); cookie is rotated on refresh.
- [x] Implement: `auth` router sets the cookie on login/refresh (httponly, samesite=lax,
  max_age from settings, path=/api/v1/auth); refresh falls back to cookie when body omitted.
- [x] Full backend suite green. Commit.

### Task 2: Task ORM model + TaskRepository (integration-tested)

- [x] Failing integration tests (testcontainers): create with defaults (`todo`, position),
  list for project ordered by position, `get_with_owner` joins projects for owner scoping,
  `max_position`, `count_by_status`, update, delete.
- [x] Implement `app/models/task.py` (id, project_id FK, title, description, status,
  priority, position float, due_date date|null, created_at, updated_at) and
  `app/repositories/task_repo.py`.
- [x] Tests green. Commit.

### Task 3: TaskService + ProjectService.summary (unit-tested with fakes)

- [x] Failing unit tests: create appends position (`max+1024`), create/list raise NotFound
  for non-owned project; update/delete owner-scoped via task→project join; summary returns
  task counts by status plus zeroed snippets/bookmarks.
- [x] Implement `app/services/task_service.py`; extend `ProjectService` with `summary()`
  (task_repo injected).
- [x] Tests green. Commit.

### Task 4: Task schemas + routers + summary endpoint (API-tested)

- [x] Failing API tests: nested `GET/POST /projects/{id}/tasks`, `PATCH /tasks/{id}` (status
  + position moves), `DELETE /tasks/{id}`, 404 on other users' projects/tasks, 401 without
  auth, validation 422s, `GET /projects/{id}/summary` counts.
- [x] Implement `app/schemas/task.py`, `app/routers/tasks.py`, summary route in projects
  router, DI providers; mount router.
- [x] Full suite green; ruff clean. Commit.

### Task 5: Nuxt scaffold + Tailwind + vue-query + Vitest (infra)

- [x] Scaffold `frontend/` (Nuxt 4, TS): package.json, nuxt.config.ts with hybrid route rules
  (`/`, `/login`, `/register` prerendered; `/app/**` ssr:false; `/api` dev-proxied to
  :8000), Tailwind v4 via vite plugin, vue-query plugin, base layout.
- [x] Vitest configured (happy-dom); a trivial component test proves the harness runs.
- [x] `npm run build` succeeds. Commit.

### Task 6: Position util + auth composables + auth pages

- [ ] TDD `app/utils/position.ts` (`computePosition(prev, next)`): empty column, top,
  bottom, between; failing tests first.
- [ ] Implement `useAuth` (access token in memory via `useState`, login/register/refresh/
  logout/me, $fetch wrapper with 401→refresh→retry) and `auth` route middleware.
- [ ] Login/register pages wired to the API; landing page links.
- [ ] Vitest green; `npm run build` green. Commit.

### Task 7: Dashboard — projects CRUD (TanStack Query)

- [ ] TDD `ProjectCard` component (renders name/description/status, emits open/archive/
  delete) — failing test first.
- [ ] Dashboard page: list projects (useQuery), create/edit form, archive + delete with
  invalidation (useMutation).
- [ ] Vitest green; build green. Commit.

### Task 8: Task board — columns + drag-and-drop ordering

- [ ] TDD `TaskCard` (title, priority badge, due date) — failing test first.
- [ ] Board page `/app/projects/[id]`: three status columns, task create/edit/delete,
  vuedraggable cross/in-column moves persisting `{status, position}` via PATCH and
  computePosition; summary chips from `/summary`.
- [ ] Vitest green; build green. Commit.

### Task 9: Dockerize frontend + compose integration + E2E smoke

- [ ] `frontend/Dockerfile` (node:22-alpine, build with API_PROXY_TARGET=http://api:8000,
  run Nitro server), `.dockerignore`; `nuxt` service in docker-compose.yml.
- [ ] Smoke: `docker compose up -d --build`; `/` and `/login` return 200 from :3000;
  `/api/v1/health` proxied through Nuxt returns ok; register→login→create project→create
  task→reorder via the proxy; teardown.
- [ ] Commit.
