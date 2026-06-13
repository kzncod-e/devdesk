# DevDesk — CLAUDE.md

Developer productivity app: projects, tasks (kanban), code snippets, and bookmarks.

---

## Stack at a Glance

| Layer | Technology |
|---|---|
| Frontend | Nuxt 4, Vue 3, Tailwind v4, TanStack Vue Query |
| Backend | FastAPI, async SQLAlchemy, Motor/PyMongo |
| Databases | PostgreSQL (structured data), MongoDB (snippets, bookmarks) |
| Auth | JWT — access token in memory, refresh token in httpOnly cookie |
| Image storage | Cloudinary (SDK: `cloudinary` Python package) |
| Container | Docker Compose (`postgres`, `mongo`, `api`, `nuxt`) |

---

## Repo Layout

```
devdesk/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI factory + lifespan (DB init, Cloudinary config, migrations)
│   │   ├── api/deps.py          # FastAPI dependencies (DB sessions, services, auth guards)
│   │   ├── core/
│   │   │   ├── config.py        # pydantic-settings: Settings class, get_settings()
│   │   │   ├── errors.py        # AppError hierarchy (NotFoundError, ForbiddenError, etc.)
│   │   │   └── security.py      # bcrypt + JWT helpers
│   │   ├── db/
│   │   │   ├── postgres.py      # AsyncEngine, Base, get_session()
│   │   │   └── mongo.py         # Motor client, get_mongo_db(), ensure_mongo_indexes()
│   │   ├── models/              # SQLAlchemy ORM (Postgres): user.py, project.py, task.py
│   │   ├── schemas/             # Pydantic I/O: auth.py, project.py, task.py, snippet.py, bookmark.py, search.py
│   │   ├── repositories/        # DB access layer: user, project, task, snippet, bookmark
│   │   ├── services/            # Business logic: auth, project, task, snippet, bookmark, search, user
│   │   └── routers/             # FastAPI routers: auth, admin, projects, tasks, snippets, bookmarks, search
│   └── pyproject.toml
├── frontend/
│   ├── app/
│   │   ├── assets/css/main.css  # Tailwind v4 theme: design tokens + utilities
│   │   ├── layouts/app.vue      # Authenticated shell: sidebar, topbar, mobile nav, splash
│   │   ├── pages/
│   │   │   ├── index.vue        # Landing (prerendered)
│   │   │   ├── login.vue
│   │   │   ├── register.vue
│   │   │   └── app/
│   │   │       ├── index.vue          # Projects list
│   │   │       ├── projects/[id].vue  # Kanban board
│   │   │       ├── snippets.vue
│   │   │       ├── bookmarks.vue
│   │   │       └── settings.vue       # Profile + admin user management
│   │   ├── components/
│   │   │   ├── Ui*/             # Design-system primitives (see Design System below)
│   │   │   ├── ProjectCard/Form, TaskCard/Form, SnippetCard/Form, BookmarkCard/Form
│   │   │   ├── CommandPalette.vue
│   │   │   └── AppSplash.vue    # First-visit onboarding overlay
│   │   ├── composables/
│   │   │   ├── useAuth.ts       # login, register, logout, api() (authenticated $fetch wrapper)
│   │   │   ├── useConfirm.ts    # global confirm dialog (useConfirm().confirm({...}))
│   │   │   ├── useToast.ts      # useToast().success/error/info
│   │   │   ├── useTheme.ts      # light/dark toggle
│   │   │   ├── useCommandPalette.ts
│   │   │   └── useAppReady.ts   # splash-screen state + localStorage onboarding flag
│   │   ├── middleware/auth.ts   # Nuxt route middleware: redirects to /login if no token
│   │   ├── plugins/
│   │   │   ├── vue-query.ts     # TanStack Vue Query client
│   │   │   └── theme.client.ts  # Applies saved dark/light class on <html> before first paint
│   │   ├── types/api.ts         # TypeScript interfaces: User, Project, Task, Snippet, Bookmark
│   │   └── utils/position.ts    # Kanban task position helpers
│   └── nuxt.config.ts
├── docker-compose.yml
├── .env                         # Cloudinary credentials (not committed)
└── CLAUDE.md
```

---

## Backend

### Conventions

- **All routes are async.** Use `async def` everywhere.
- **Layer separation is strict:** routers call services, services call repositories, repositories touch the DB.
- **Dependency injection** via `api/deps.py`: `get_current_user`, `get_admin_user`, `get_project_service`, etc. Compose with `Annotated[T, Depends(...)]`.
- **Error handling:** raise from `app.core.errors` (`NotFoundError`, `ForbiddenError`, `UnprocessableError`, `ConflictError`). The global handler in `main.py` converts them to JSON `{ detail, code }`.
- **Schema naming:** `*In` = request body, `*Out` = response, `*Patch` = partial update.

### Databases

| Data | Store | Notes |
|---|---|---|
| Users, Projects, Tasks | PostgreSQL | SQLAlchemy async ORM, `Base` from `db/postgres.py` |
| Snippets, Bookmarks | MongoDB | Motor async via `db/mongo.py`; text indexes created on startup |

Schema migrations are done with inline `ALTER TABLE … ADD COLUMN IF NOT EXISTS` in `main.py`'s `_MIGRATIONS` list (runs idempotently on every startup). There is no Alembic.

### Auth

- `POST /api/v1/auth/register` → hashes password, creates user with `role="member"`
- `POST /api/v1/auth/login` → returns `access_token` (15 min JWT) + sets `refresh_token` httpOnly cookie
- `POST /api/v1/auth/refresh` → exchanges cookie for new access token
- `GET /api/v1/auth/me` → current user
- `PATCH /api/v1/auth/me` → update own profile (name)

### RBAC

Roles: `admin`, `manager`, `member` (default). Enforced by deps:

- `get_current_user` — any authenticated user
- `get_admin_user` — raises `ForbiddenError` if `user.role != "admin"`
- `get_manager_or_admin_user` — raises if neither admin nor manager

Admin routes live at `/api/v1/admin/*` (router: `routers/admin.py`).

### Image Upload (Cloudinary)

`POST /api/v1/projects/{id}/image` accepts `multipart/form-data` with field `file`.  
Upload runs in a thread-pool executor (`asyncio.get_running_loop().run_in_executor`) because the `cloudinary` SDK is synchronous.  
`public_id=project_{id}` with `overwrite=True` + `invalidate=True` — each project has exactly one Cloudinary slot; re-uploading replaces in-place.  
Returns full `ProjectOut` with updated `image_url` (Cloudinary CDN URL).

Required env vars: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`

### API Routes Summary

```
/api/v1/auth/        register, login, logout, refresh, me, PATCH me
/api/v1/projects/    CRUD + GET summary + POST image
/api/v1/projects/{id}/tasks/   CRUD + PATCH position
/api/v1/snippets/    CRUD (MongoDB)
/api/v1/bookmarks/   CRUD + auto-fetch meta (MongoDB)
/api/v1/search/      GET ?q= → grouped results (projects, tasks, snippets, bookmarks)
/api/v1/admin/users  GET list, PATCH role
```

---

## Frontend

### Routing

- `/`, `/login`, `/register` — **prerendered** (static HTML, no SSR overhead)
- `/app/**` — **CSR only** (`ssr: false` in `routeRules`). No server-side JWT juggling.
- All authenticated pages set `definePageMeta({ middleware: 'auth', layout: 'app' })`.

### Data Fetching

Uses **TanStack Vue Query** (`@tanstack/vue-query`).

```ts
const { api } = useAuth()                        // authenticated $fetch wrapper
const { data } = useQuery({ queryKey: ['projects'], queryFn: () => api<Project[]>('/api/v1/projects') })
const mut = useMutation({ mutationFn: ..., onSuccess: () => queryClient.invalidateQueries(...) })
```

`api()` in `useAuth.ts` is an authenticated `$fetch` wrapper — adds `Authorization: Bearer <token>` and transparently retries once after a 401 (refresh flow). Pass `FormData` as `body` for file uploads; ofetch detects it and does NOT set `Content-Type` (browser sets multipart boundary automatically).

### Design System

Tailwind v4 with `@theme inline` CSS custom properties. **Never use raw hex or `dark:` utility variants** — always use semantic token utilities.

**Token map (`app/assets/css/main.css`):**

| Token | Utility | Purpose |
|---|---|---|
| `--canvas` | `bg-canvas` | Page background |
| `--surface` | `bg-surface` | Card / panel background |
| `--surface-2` | `bg-surface-2` | Slightly elevated surface |
| `--surface-3` | `bg-surface-3` | Input fills, hover states |
| `--line` | `border-line` | Default border |
| `--line-strong` | `border-line-strong` | Hover / focus border |
| `--ink` | `text-ink` | Primary text |
| `--ink-muted` | `text-ink-muted` | Secondary text |
| `--ink-subtle` | `text-ink-subtle` | Placeholder / disabled |
| `--accent` | `text-accent`, `bg-accent` | Brand / interactive color (indigo) |
| `--accent-soft` | `bg-accent-soft` | Tinted accent background |
| `--accent-fg` | `text-accent-fg` | Text on accent fill |

Dark mode is a `.dark` class on `<html>` — the CSS vars flip automatically. No `dark:` variants needed.

**Tailwind v4 note:** use `bg-linear-to-b` not `bg-gradient-to-b`.

### UI Primitives

All components are in `app/components/`. Use these instead of raw HTML elements:

| Component | Usage |
|---|---|
| `UiButton` | `variant="primary\|ghost\|danger"`, `icon="..."`, `:loading` |
| `UiModal` | Centered dialog. Props: `open`, `title`, `subtitle`, `width`. Emits `close`. Use for all CRUD forms. |
| `UiDrawer` | Right-side slide-in. Exists but **not used for forms** — UiModal is preferred. |
| `UiConfirm` | Global singleton. Use `useConfirm().confirm({ title, message, confirmLabel, danger })` → returns `Promise<boolean>`. |
| `UiMenu` / `UiMenuItem` | Dropdown menu. Slot `#trigger` for the button. |
| `UiToaster` | Global singleton. Use `useToast().success/error/info(msg)`. |
| `UiIcon` | Inline SVG icon set. Prop `name` (see component for full list). `size` in px. |
| `UiIconButton` | Icon-only button. Props: `icon`, `label` (for a11y), `size`. |
| `UiBadge` | Pill badge. Prop `tone="green\|red\|gray\|indigo\|yellow"`, `dot`. |
| `UiSkeleton` | Loading placeholder. Apply `class` for size. |
| `UiEmptyState` | Empty state. Props: `icon`, `title`, `description`. Default slot for CTA button. |

### Form Pattern

All CRUD forms (`ProjectForm`, `TaskForm`, `SnippetForm`, `BookmarkForm`) follow the same pattern:
- `defineProps<{ item?: T | null; busy?: boolean }>`
- `defineEmits<{ submit: [data: FormPayload]; cancel: [] }>`
- `<form @submit.prevent="emit('submit', { ...fields })">`
- Button row: `<div class="flex justify-end gap-2 pt-4">` (NOT `mt-auto`, forms are NOT full-height)
- Mounted inside `UiModal` in the parent page; parent owns the mutation.

### Key Composables

```ts
const { user, api, login, register, logout } = useAuth()
// user is Ref<User | null>, User has: id, email, name, role

const { confirm } = useConfirm()
const ok = await confirm({ title: 'Delete?', message: '...', confirmLabel: 'Delete', danger: true })

const { success, error } = useToast()

const { mode, toggle } = useTheme()   // 'light' | 'dark'
```

### Onboarding / Splash

`AppSplash` in `layouts/app.vue` shows on first visit (checks `localStorage` key `devdesk:onboarded`). Managed by `useAppReady`. The splash dismisses after ≥1.2 s + user data is loaded, with a 4 s absolute fallback.

---

## Docker / Infrastructure

```yaml
services:
  postgres:   port 5432, volume pgdata
  mongo:      port 27017, volume mongodata
  api:        port 8000, built from ./backend
  nuxt:       port 3000, built from ./frontend
```

**Proxy:** The Nuxt Nitro server proxies `/api/**` → `http://api:8000/api/**` (set via build arg `API_PROXY_TARGET=http://api:8000` in the frontend Dockerfile). Images are served directly from Cloudinary CDN — no `/static/**` proxy needed.

**Dev proxy** (`nuxt dev` on host): `nitro.devProxy` forwards `/api` → `http://localhost:8000/api`.

**Rebuilding rules:**
- Backend code changes → `docker compose up -d api` (watch sync handles live reload via `develop.watch`)
- Frontend code changes (nuxt.config, new deps) → `docker compose up --build -d nuxt`
- New Python dependencies → `docker compose up --build -d api`
- All services after network issues → `docker compose up -d`

**Env vars** (set in `.env` at project root, picked up by docker-compose):

```
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
```

---

## Common Gotchas

1. **SQLAlchemy `server_default`**: string defaults must be SQL literals — `server_default="'member'"` not `server_default="member"`. The latter generates `DEFAULT member` (bare identifier, invalid SQL).

2. **Schema migrations**: `Base.metadata.create_all` only creates missing tables, never alters existing ones. Add new columns to `_MIGRATIONS` in `main.py` using `ALTER TABLE … ADD COLUMN IF NOT EXISTS`.

3. **Cloudinary upload is sync**: the `cloudinary` SDK has no async API. Always wrap with `asyncio.get_running_loop().run_in_executor(None, lambda: cloudinary.uploader.upload(...))`.

4. **Vitest component tests** (`frontend/tests/`): Nuxt auto-imports are not available. Explicitly import `ref`, `computed` from `'vue'`. Use native `<button aria-label="...">` — child components like `UiIconButton` don't resolve in unit tests.

5. **TanStack Query `enabled` guard**: pass a `computed(() => bool)` or `MaybeRef<boolean>`, not a raw expression. E.g. `enabled: isAdmin` where `isAdmin` is a computed ref.

6. **`FormData` uploads through `api()`**: `ofetch` detects `FormData` body and does NOT set `Content-Type` — the browser sets the multipart boundary. Do not manually set `Content-Type` for uploads.
