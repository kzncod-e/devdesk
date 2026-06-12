# DevDesk Milestone 3: Snippets + Bookmarks (MongoDB) — Implementation Plan

> **For agentic workers:** Execute task-by-task with strict TDD where a task is testable:
> write the failing test, run it to confirm it fails, implement, run it to confirm it
> passes, then commit. Infrastructure/scaffold steps are verified by smoke checks.

**Goal:** Owner-scoped snippets and bookmarks stored in MongoDB with tagging, flat CRUD at
`/snippets` and `/bookmarks` with `?project_id=/?tag=/?language=` filters, background
metadata fetch on bookmark creation, project-deletion detach semantics, real counts in
`/projects/{id}/summary`, and frontend pages for both with syntax highlighting.

**Scope decisions (deviations flagged):**
- PyMongo native `AsyncMongoClient` instead of Motor (Motor is deprecated for new projects).
- Mongo text indexes deferred to M4 alongside `/search` (spec groups them under Search).
- API-tier tests run against a real Mongo testcontainer (module-scoped) — no good async
  Mongo fake exists for PyMongo Async; Postgres side stays in-memory SQLite.
- HTML metadata parsed with a small stdlib `HTMLParser` util (title, meta description,
  favicon) — no bs4/lxml dependency for three fields.
- The HTML fetcher is a DI seam (`get_html_fetcher`) so API tests exercise the real
  BackgroundTasks flow without network egress.

---

### Task 1: Mongo wiring (settings + client + DI seam)

- [x] Failing unit test: `Settings` reads `MONGO_URL` and `MONGO_DB_NAME` from env with
  sane defaults.
- [x] Implement settings fields, `app/db/mongo.py` (lazy global `AsyncMongoClient`,
  `get_mongo_db` dependency), add `pymongo` to deps; compose `api` service gets
  `MONGO_URL=mongodb://mongo:27017`.
- [x] Unit suite green. Commit.

### Task 2: Snippet + Bookmark repositories (integration-tested vs real Mongo)

- [x] Failing integration tests (testcontainers mongo): snippet create/get/update/delete
  owner-scoped; list with project/tag/language filters + pagination; bookmark create with
  empty `fetched_meta`, `set_metadata`, list with filters; `detach_project` nulls
  `project_id` across owners' docs; `count_for_project`.
- [x] Implement `app/repositories/snippet_repo.py` and `bookmark_repo.py` (docs returned as
  JSON-friendly dicts, `_id` → `id: str`).
- [x] Tests green. Commit.

### Task 3: HTML metadata parser (pure, TDD)

- [x] Failing unit tests: extracts `<title>`, meta description (name= and property=og:),
  favicon link (absolute via base URL), falls back to `/favicon.ico` and empty strings;
  survives malformed HTML.
- [x] Implement `app/core/htmlmeta.py` with stdlib `HTMLParser`.
- [x] Tests green. Commit.

### Task 4: Services — snippets, bookmarks, detach-on-delete, real summary counts

- [x] Failing unit tests (fakes): create validates optional `project_id` against owned
  projects (cross-DB check, NotFound otherwise); get/update/delete owner-scoped;
  `BookmarkService.fetch_and_store_meta` fetches HTML via injected fetcher and stores
  parsed meta (fetch errors swallowed, doc untouched); `ProjectService.delete` detaches
  snippets+bookmarks; `summary` includes real snippet/bookmark counts.
- [x] Implement `SnippetService`, `BookmarkService`; extend `ProjectService`.
- [x] Unit suite green. Commit.

### Task 5: Schemas + routers + API tests (BackgroundTasks fetch)

- [x] Failing API tests (mongo testcontainer + SQLite PG): snippets CRUD + filters +
  owner isolation + 401s + 422s; bookmarks CRUD; bookmark create returns 201 immediately
  and the background task stores metadata from the DI-faked fetcher; project deletion
  detaches; summary returns real counts.
- [x] Implement `app/schemas/snippet.py`, `bookmark.py`, routers, DI providers
  (`get_html_fetcher` seam); mount routers.
- [x] Full backend suite green; ruff clean. Commit.

### Task 6: Frontend — TagInput + snippets page with highlighting

- [x] TDD `TagInput` (chips, Enter adds, × removes, v-model `string[]`) — failing test
  first. TDD `SnippetCard` (title, language badge, tags, emits edit/delete).
- [x] Snippets page `/app/snippets`: vue-query list with language/tag filters, create/edit
  form (code textarea, language, tags, optional project), delete; `CodeBlock` with
  highlight.js (common bundle); nav links in `AppHeader`.
- [x] Vitest green; build green. Commit.

### Task 7: Frontend — bookmarks page

- [x] TDD `BookmarkCard` (favicon, linked title, description, tags, emits edit/delete) —
  failing test first.
- [x] Bookmarks page `/app/bookmarks`: list with tag/project filters, create by URL
  (+tags/project), edit tags/title, delete; metadata appears after background fetch
  (refetch button / query invalidation).
- [x] Vitest green; build green. Commit.

### Task 8: Compose smoke E2E

- [ ] `docker compose up -d --build`; through the Nuxt proxy: register/login, create
  project, create snippet (tagged, project-linked), filter by tag and language, create
  bookmark pointing at `http://api:8000/docs` (no egress needed), verify background
  metadata fetch populated the title, verify summary counts, delete project and verify
  detach left the snippet with `project_id: null`; teardown.
- [ ] Commit any fixes; plan checked off.
