# DevDesk Milestone 4: Global Search + UI Polish — Implementation Plan

> **For agentic workers:** Execute task-by-task with strict TDD where a task is testable:
> write the failing test, run it to confirm it fails, implement, run it to confirm it
> passes, then commit. Infrastructure/scaffold steps are verified by smoke checks.

**Goal:** `GET /search?q=` fanning out to Postgres FTS (projects, tasks) and MongoDB text
indexes (snippets, bookmarks), merged into grouped, owner-scoped results; a frontend search
experience (header search box + results page with deep links); light UI polish (head
metadata). Stack shippable via Docker Compose.

**Scope decisions (deviations flagged):**
- Spec §3 shows `{tasks, snippets, bookmarks}` but §2 searches "projects and tasks" — the
  endpoint returns all four groups (`projects` added); supersets the §3 contract.
- Postgres FTS (`websearch_to_tsquery`, english config) with a portable ILIKE fallback for
  non-PG dialects: the fast API-test tier runs on SQLite. Production and integration tests
  always hit the FTS path.
- Mongo text indexes created idempotently at app startup via a shared
  `ensure_mongo_indexes()` helper (also used by test fixtures, since ASGITransport skips
  lifespan).
- "UI polish" scoped to: header search box, results page, app head metadata (title/meta),
  useDebounce util. No redesign.

---

### Task 1: Postgres search — projects + tasks repos

- [ ] Failing integration tests (testcontainers PG): `ProjectRepository.search` matches
  name/description with stemming (e.g. "deploying" → "deploy"), owner-scoped;
  `TaskRepository.search` matches title/description, owner-scoped via project join;
  no-match returns [].
- [ ] Implement `search()` on both repos: `websearch_to_tsquery('english', q)` on PG,
  ILIKE fallback elsewhere (dialect-guarded).
- [ ] Integration suite green. Commit.

### Task 2: Mongo text indexes + search methods

- [ ] Failing integration tests (testcontainers mongo): `SnippetRepository.search` matches
  title/code/notes/tags via `$text`, owner-scoped; `BookmarkRepository.search` matches
  title/description/tags; no-match returns [].
- [ ] Implement `ensure_mongo_indexes(db)` in `app/db/mongo.py` (text indexes on both
  collections), call from app lifespan; `search()` on both repos.
- [ ] Integration suite green. Commit.

### Task 3: SearchService (unit-tested with fakes)

- [ ] Failing unit tests: fans out to all four repos with owner_id/q/limit, returns
  grouped dict; per-group limit respected.
- [ ] Implement `app/services/search_service.py`.
- [ ] Unit suite green. Commit.

### Task 4: /search endpoint + API tests

- [ ] Failing API tests: grouped shape with hits in all four groups, owner isolation
  (other users' content invisible), requires auth, `q` required (422 when missing/empty),
  per-group `limit` param.
- [ ] Implement `app/schemas/search.py`, `app/routers/search.py`, DI provider; mount;
  test fixture ensures mongo text indexes.
- [ ] Full backend suite green; ruff clean. Commit.

### Task 5: Frontend — search UX + head polish

- [ ] TDD `useDebounce`/`debouncedRef` util — failing test first. TDD `SearchResultsGroup`
  component (heading with count, slot items, empty state hidden).
- [ ] Header search box (submits to `/app/search?q=`); search page with debounced
  re-query, grouped results deep-linking: project → board, task → its project board,
  snippet → snippets page, bookmark → external URL.
- [ ] App head metadata (title template, description) in `nuxt.config.ts`.
- [ ] Vitest green; build green. Commit.

### Task 6: Compose smoke E2E

- [ ] `docker compose up -d --build`; seed project/task/snippet/bookmark through the
  proxy; `GET /api/v1/search?q=` finds all four groups owner-scoped; second user sees
  nothing; `/app/search` page serves; teardown.
- [ ] Commit any fixes; plan checked off.
