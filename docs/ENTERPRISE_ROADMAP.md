# DevDesk — Enterprise Roadmap (Phases 1 → 4)

> The phased plan to take DevDesk from a single-user tool to an enterprise-grade
> developer workspace (Linear / Notion / Vercel tier). Each item states **why**,
> the **DB / backend / API / UI** changes, and a rough **effort**.
>
> Effort key: **S** = ≤1 day · **M** = 2–4 days · **L** = ~1 week · **XL** = multi-week.

---

## Status snapshot

| Capability | State |
|---|---|
| Workspaces, memberships, invites | ✅ shipped (Phase 1) |
| Workspace-scoped RBAC (owner/admin/editor/member/viewer) | ✅ shipped |
| Auto-provision personal workspace on signup | ✅ shipped |
| `X-Workspace-Id` scoping + default fallback | ✅ shipped |
| Frontend workspace switcher + members/invite UI | ✅ shipped |
| Projects / tasks / snippets / bookmarks scoped to workspace | ✅ shipped |
| Snippets & bookmarks consolidated into Postgres | ✅ shipped (2.1) |
| Alembic migrations (outbox + worker backbone) | ✅ shipped (2.0, 2.2) |
| Activity feed, audit log, notifications | ✅ shipped (2.3, 2.4) |
| Global search (Postgres FTS) + ⌘K actions | ✅ shipped (2.5) |
| Templates + public gallery | ✅ shipped (2.6) |
| Collections, tag registry, saved filters | ✅ shipped (2.7) |
| Comments + @mentions | ✅ shipped (3.1) |
| Task side-panel, workflows, teams, webhooks, sharing | ❌ not started (Phase 3) |
| SSO/SCIM, billing, public API, audit export | ❌ not started (Phase 4) |

---

## Architecture guardrails (apply to every phase)

These are deliberate constraints. Violating them is how the codebase rots.

1. **Modular monolith, not microservices.** One deployable, organised by domain
   module. Revisit only when a module has independent scaling needs *and* an
   owning team.
2. **Transactional outbox, not Kafka / event-sourcing.** Domain events are written
   to an `outbox` table in the same DB transaction as the state change; one async
   worker fans them out. Same decoupling, a fraction of the ops cost.
3. **Postgres FTS before a search engine.** `tsvector` + `pg_trgm` covers
   Linear-quality search to ~1M rows/workspace. Adopt Typesense/Meilisearch only
   when measured limits demand it — and only behind the existing search interface.
4. **Permissions in code, assignments in the DB.** The role→permission matrix
   lives in `app/core/policy.py`; the database only stores `memberships.role`.
5. **Every tenant row carries `workspace_id`, indexed first.** Enables cheap
   isolation and future partitioning. Soft-delete via `deleted_at`.
6. **One database.** Finish the Mongo→Postgres consolidation early (Phase 2) so
   FKs, transactions, and a single search index are available to everything after.

---

## Phase 1 — Foundation ✅ (shipped)

The load-bearing wall: multi-tenancy + scoped RBAC. Everything else depends on it.

- **Shipped:** `workspaces`, `memberships`, `invites` tables; `Role`/`Perm` policy
  with the 5-role matrix; `require(perm)` (header-scoped) and `require_member(perm)`
  (path-scoped) guards; all content routers scoped to `workspace_id`; personal
  workspace auto-created on signup; idempotent migration + backfill; Mongo
  `workspace_id` backfill; frontend switcher, create-workspace, and members/invite
  management UI.
- **Verified:** 77 backend tests (unit + API + integration), 22 frontend tests.

**Carry-over hardening (do early in Phase 2):**
- Promote `projects.workspace_id` / `tasks.workspace_id` from nullable → `NOT NULL`
  once backfill is confirmed on all environments. **(S)**
- Postgres **Row-Level Security** as defense-in-depth: `SET app.workspace_id` per
  transaction + `CREATE POLICY` on every tenant table, so a missing app-layer check
  can't leak across tenants. **(M)**

---

## Phase 2 — Growth

Goal: make the product feel alive, fast, and sticky. Almost everything here falls
out of two pieces of infrastructure — **the single database** and **the outbox
event backbone** — so build those first.

### 2.0 Adopt Alembic  ·  **M**  ·  *prerequisite*
- **Why:** inline `ALTER TABLE … IF NOT EXISTS` in `main.py` has no version history,
  no down-migrations, and no review trail — unacceptable once tenants hold real data.
- **Backend:** add Alembic, autogenerate an initial revision that baselines the
  current schema, move `_MIGRATIONS` into versioned revisions, run on deploy (not
  in the request/app lifespan).
- **DB/API/UI:** none (tooling change).

### 2.1 Consolidate MongoDB → Postgres  ·  **L**  ·  *prerequisite*
- **Why:** snippets/bookmarks in Mongo block FKs to workspaces, cross-store
  transactions (e.g. "create project from template"), and a unified search index.
  One datastore removes an entire ops surface.
- **DB:** new `snippets` and `bookmarks` Postgres tables with `workspace_id`,
  `owner_id` (creator), `project_id` FK, `collection_id` FK, `tags` (via the
  normalized tag join), `visibility`, `deleted_at`, and a generated `tsvector`
  column. Flexible/scraped fields (`fetched_meta`) live in `JSONB`.
- **Backend:** rewrite `snippet_repo` / `bookmark_repo` against SQLAlchemy; one-time
  migration script copies Mongo docs → Postgres (keyed by the `workspace_id`
  already backfilled); delete Mongo client + `db/mongo.py`.
- **API:** unchanged response shapes (IDs become integers — coordinate a frontend
  type change `string → number`).
- **UI:** update `Snippet.id` / `Bookmark.id` types.

### 2.2 Outbox event backbone + worker  ·  **L**  ·  *prerequisite*
- **Why:** one `emit()` call powers activity, audit, notifications, search
  indexing, and webhooks — without slowing the request or losing events on crash.
- **DB:** `outbox(id, topic, payload jsonb, created_at, processed_at)`.
- **Backend:** `core/events.py` writes outbox rows inside the request transaction;
  an `arq` worker (async, Redis-backed) polls and dispatches to handlers. Add Redis
  to compose. Introduce `platform/jobs`, `platform/outbox`.
- **API/UI:** none directly (enables the features below).

### 2.3 Activity feed + Audit log  ·  **M**
- **Why:** "feels alive" (activity) + the compliance checkbox enterprise buyers
  require (audit). One emit, two ledgers with different retention/immutability.
- **DB:** `activities(workspace_id, actor_id, verb, entity_type, entity_id,
  metadata, created_at)` (user-facing, prunable); `audit_logs(workspace_id,
  actor_id, action, target_type, target_id, before, after, ip, user_agent,
  created_at)` (append-only; `REVOKE UPDATE/DELETE` from the app role).
- **Backend:** outbox handlers write both from domain events
  (`project.created`, `member.role_changed`, `auth.login`, …).
- **API:** `GET /workspaces/{ws}/activity?cursor=` (keyset), `GET /{entity}/{id}/activity`,
  `GET /workspaces/{ws}/audit?action=&actor=&from=&to=` (admin-only).
- **UI:** activity feed on the dashboard + per-entity timeline tab; audit table in
  workspace settings.

### 2.4 Notifications  ·  **M**
- **Why:** retention loop; "you were assigned / mentioned / invited".
- **DB:** `notifications(user_id, workspace_id, type, payload jsonb, read_at, created_at)`.
- **Backend:** outbox handler fans out to in-app rows + email (arq job); daily
  digest via an arq cron.
- **API:** `GET /notifications?cursor=`, `POST /notifications/read`, unread count.
- **UI:** wire the existing bell icon to a real unread badge + dropdown panel.

### 2.5 Global search + ⌘K actions  ·  **M**  ·  ✅ shipped
- **Why:** the most-used surface in Linear/Raycast; defines "fast tool".
- **DB:** ✅ generated `tsvector` columns + GIN indexes on projects/tasks
  (migration `f3a4b5c6d7e8`). Snippets/bookmarks keep their MongoDB text indexes.
- **Backend:** ✅ `app/platform/search.py` query builder — index-backed match +
  `ts_rank` ordering, all `workspace_id`-scoped, with prefix matching (`term:*`)
  so partial words match mid-type; ILIKE fallback on the SQLite test tier.
- **API:** ✅ `GET /search?q=&types=&limit=` returns grouped results; `types`
  (comma-sep subset) drives palette scoping.
- **UI:** ✅ command palette is now **actionable** (new project/snippet/bookmark
  via a cross-page `useQuickCreate` intent, switch workspace, invite, toggle
  theme, settings, log out); `/p /t /s /b` scoping; recents on empty query
  (localStorage).
- **Deferred:** `pg_trgm` fuzzy/typo-tolerance (prefix matching covers the common
  case); per-user recents in Redis (localStorage chosen — per-device, no
  round-trip); `tags=` filter; templates not yet indexed (ship in 2.6).

### 2.6 Templates + public gallery  ·  **M**  ·  ✅ shipped
- **Why:** time-to-value; a public gallery is a growth/SEO channel (GitHub-template style).
- **DB:** ✅ `templates(workspace_id NULL=global, kind, name, description, payload
  jsonb, visibility, created_by, use_count)` (migration `a4b5c6d7e8f9`).
- **Backend:** ✅ `app/services/template_service.py` — "capture" serializes a
  project (+ its tasks & snippets) or a snippet → `payload`; "use" instantiates
  into the current workspace in a single transaction, increments `use_count`,
  emits `template.created` / `template.used` (wired into the activity feed).
- **API:** ✅ `POST /templates/capture`, `POST /templates` (from payload),
  `GET /templates?kind=&visibility=`, `GET /templates/{id}`,
  `POST /templates/{id}/use`, `DELETE /templates/{id}`, and the unauthenticated
  `GET /templates/gallery`.
- **UI:** ✅ "Save as template" on project/snippet cards (global `SaveTemplateModal`
  via a `useSaveTemplate` singleton); `/app/templates` browse-and-use page; ⌘K
  "Browse templates"; SSR public `/gallery`.
- **Permissions:** ✅ create = `CONTENT_WRITE`; delete = `CONTENT_DELETE`;
  publish public = `WORKSPACE_MANAGE`. Usable templates = own workspace ∪ global
  (NULL) ∪ any public.
- **Deferred:** templates aren't FTS-indexed yet (2.5 follow-up); gallery "Use"
  links into the app rather than instantiating anonymously; capture is bounded to
  200 tasks/snippets.

### 2.7 Collections, tag registry, saved filters  ·  **S–M**  ·  ✅ shipped
- **DB:** ✅ `collections(workspace_id, name, kind, parent_id)` (self-ref tree);
  `tags(workspace_id, name, color)` registry; `saved_filters(user_id, workspace_id,
  name, kind, query jsonb)`; nullable `collection_id` on snippets/bookmarks
  (migration `b5c6d7e8f9a0`).
- **Decision — no polymorphic `taggables`:** kept the working GIN-indexable
  `text[]` tag arrays as the source of truth and added a `tags` *registry* (name→
  color) that self-populates on snippet/bookmark writes. Avoids the polymorphic-FK
  anti-pattern and a risky rewrite of every tag path; delivers colored chips +
  autocomplete + recolor. Rename-tag-everywhere deferred (the one cross-cutting op).
- **API:** ✅ CRUD `/collections`, `/tags` (list + recolor + delete),
  `/saved-filters`; `collection_id` filter + field on snippets/bookmarks.
- **UI:** ✅ snippets page — collections folder rail (create/select/delete +
  filter), colored tag chips (registry), tag-aware autocomplete in the form,
  collection selector, and saved "views" (save/apply/delete current filters).
- **Deferred:** bookmarks page reuse of the same rail/chips (snippets shipped as
  the flagship); strict cross-workspace `collection_id` validation on assignment
  (reads stay workspace-isolated); rename-everywhere.

---

## Phase 3 — Team Collaboration

Goal: turn shared workspaces into real collaboration. Depends on Phase 2's outbox
(for mentions → notifications) and single DB.

### 3.1 Comments + @mentions  ·  **M**  ·  ✅ shipped
- **DB:** ✅ `comments(workspace_id, entity_type, entity_id, author_id, body, parent_id,
  created_at, edited_at, deleted_at)` (migration `c6d7e8f9a0b1`); soft-delete; eager
  `author` relationship for the response.
- **Backend:** ✅ `comment_service` pins every comment to an entity in the caller's
  workspace; `@mention` ids (from the composer) are validated against active members;
  `emit("comment.created")` → outbox handler writes an activity ("commented") + audit
  row and notifies @mentioned users (email) + the task's assignees (quiet). Threads via
  `parent_id`.
- **API:** ✅ `GET /comments?entity_type=&entity_id=`, `POST /comments`,
  `PATCH /comments/{id}` (author-only), `DELETE /comments/{id}` (author or
  `CONTENT_DELETE`). Header-scoped via `require(CONTENT_READ|COMMENT_WRITE)`.
- **UI:** ✅ `TaskComments` on the task detail page — list, composer with `@`-mention
  autocomplete, highlighted mention chips, inline edit, delete.
- **Tests:** ✅ `tests/api/test_comments_api.py` (CRUD + threading, workspace isolation,
  invalid-mention drop, auth/validation).
- **Deferred:** entity side-panel (3.2) still surfaces comments via the page, not a
  drawer; mention parsing is composer-driven (explicit ids), not free-text NLP;
  `comment_count` not yet denormalised onto `TaskOut` for card chips; comments only on
  tasks so far (schema is generic).

### 3.2 Entity side-panel (Linear-style)  ·  **M**
- **Why:** detail-on-the-side beats modal hops; the `UiDrawer` already exists, unused.
- **UI:** slide-in panel for task/snippet detail with inline edit + Comments /
  Activity tabs. No schema change.

### 3.3 Custom workflow states + sub-tasks  ·  **M–L**
- **Why:** hardcoded `todo|in_progress|done` doesn't survive real teams.
- **DB:** `workflow_states(project_id, name, category, position)`; `tasks.status` →
  FK to a state; `tasks.parent_task_id` for sub-tasks; `tasks.number` (per-project
  sequence → `DEV-42`).
- **API:** state CRUD; task create/patch accept `state_id`, `parent_task_id`.
- **UI:** board columns driven by states; state editor; sub-task lists.

### 3.4 Teams (sub-groups within a workspace)  ·  **M**
- **DB:** `teams(workspace_id, name, key)`, `team_members(team_id, user_id, role)`;
  optional `projects.team_id`.
- **API:** team CRUD + membership; project assignment to a team.
- **UI:** teams in the sidebar; team-scoped project lists.

### 3.5 Version history  ·  **M**
- **Why:** developers expect diffable history (snippets first).
- **DB:** append-only `snippet_revisions(snippet_id, body, author_id, created_at)`
  written on update; extend to tasks/docs later.
- **API:** `GET /snippets/{id}/revisions`, `POST /snippets/{id}/revert/{rev}`.
- **UI:** history dropdown + side-by-side diff.

### 3.6 Webhooks  ·  **M**
- **DB:** `webhooks(workspace_id, url, secret, events[], active)`,
  `webhook_deliveries(...)` for retry/inspection.
- **Backend:** outbox handler signs (HMAC) and delivers with retry/backoff (arq).
- **API:** webhook CRUD + delivery log; `WORKSPACE_MANAGE` only.
- **UI:** webhook settings + delivery history.

### 3.7 Granular (per-resource) sharing  ·  **M**
- **DB:** `project_members(project_id, user_id, role)` overriding workspace role
  for private projects; `projects.visibility` (`workspace|private`).
- **Backend:** permission resolution checks per-resource grant before workspace role.
- **API:** project member CRUD; `visibility` on project patch.
- **UI:** "Share" dialog per project.

---

## Phase 4 — Enterprise

Goal: clear the enterprise procurement bar (security, provisioning, billing, scale).

### 4.1 SSO (SAML / OIDC) + SCIM provisioning  ·  **XL**
- **Why:** non-negotiable for enterprise deals; IT provisions/deprovisions via IdP.
- **DB:** `sso_connections(workspace_id, provider, metadata jsonb)`;
  `users.sso_subject`; `scim_tokens`.
- **Backend:** SAML (e.g. `python3-saml`) / OIDC login; SCIM 2.0 `/Users` `/Groups`
  endpoints mapping to memberships; JIT provisioning.
- **API:** `/sso/{ws}/login`, `/sso/{ws}/callback`, `/scim/v2/*`.
- **UI:** SSO config + enforcement toggle in workspace security settings.

### 4.2 API keys + public REST API  ·  **L**
- **DB:** `api_keys(workspace_id, name, hashed_key, scopes[], last_used_at, created_by)`.
- **Backend:** key auth scheme alongside JWT; per-key scopes mapped to `Perm`;
  rate limiting via Redis.
- **API:** key CRUD; publish a versioned, documented public API (the OpenAPI already exists).
- **UI:** developer settings — create/revoke keys, view usage.

### 4.3 Billing + seats  ·  **L**
- **DB:** `subscriptions(workspace_id, plan, status, seats, stripe_*)`; seat counting
  from active memberships.
- **Backend:** Stripe integration; webhook → subscription state; plan-gating via a
  `requires_plan()` guard.
- **API:** checkout session, billing portal link, subscription status.
- **UI:** billing page; upgrade prompts; seat-limit enforcement on invite.

### 4.4 Advanced audit: export + retention  ·  **M**
- **Backend:** async export job (CSV/JSON) of `audit_logs`; configurable retention;
  optional log streaming to S3/SIEM.
- **API:** `GET /workspaces/{ws}/audit/export` (job), retention settings.
- **UI:** export button + retention controls (owner only).

### 4.5 Usage analytics / admin dashboards  ·  **M**
- **Backend:** aggregate queries (members, activity volume, seat usage, storage) —
  good candidates for the materialized-endpoint pattern.
- **API:** `GET /workspaces/{ws}/analytics`.
- **UI:** admin console with usage charts; drives upsell.

### 4.6 Scale hardening  ·  **L** (do when metrics demand)
- **DB:** partition large tables (`activities`, `audit_logs`, `tasks`) by
  `workspace_id` or time; connection pooling (PgBouncer); read replicas for
  analytics.
- **Search:** migrate the `platform/search` indexer to Typesense/Meilisearch if
  Postgres FTS is measurably outgrown — drop-in behind the existing interface.

---

## Cross-cutting schema reference

Canonical DDL for the entities introduced across phases lives alongside this doc in
the original audit. Conventions applied everywhere:

- `BIGINT` identity PKs; `workspace_id` FK indexed first on every tenant table.
- Soft delete via `deleted_at TIMESTAMPTZ`.
- Flexible/variable shape (settings, template payloads, scraped metadata) in `JSONB`.
- Polymorphic joins (`taggables`, `comments.entity_type/entity_id`) instead of a
  column per entity.
- Append-only tables (`audit_logs`) have `UPDATE`/`DELETE` revoked from the app role.

---

## Sequencing & dependencies

```
Phase 1 ✅ ──► 2.0 Alembic ──► 2.1 Mongo→PG ──► 2.2 Outbox+worker ──┐
                                                                     ├─► 2.3 Activity/Audit
                                                                     ├─► 2.4 Notifications ──► 3.1 Comments/@mentions
                                                                     ├─► 2.5 Search + ⌘K
                                                                     └─► 2.6 Templates (needs 2.1 for atomic instantiate)
Phase 3 collaboration ──► Phase 4 enterprise (SSO, billing, public API, scale)
```

**Build order rule:** ship `2.0 → 2.1 → 2.2` first — they're prerequisites that make
every later feature cheaper. Then pick Phase 2 features by value/effort
(Search and Activity/Audit are the highest-leverage). Don't start Phase 4 infra
(SSO, billing, partitioning) until a real customer or measured limit requires it.

## Highest value-for-effort, next 3 items
1. **2.0 Alembic** (M) — unblocks safe schema evolution for everything else.
2. **2.1 Mongo→Postgres** (L) — removes a datastore; unlocks atomic templates + unified search.
3. **2.3 Activity + Audit** (M, after 2.2) — the "alive" feeling *and* the enterprise compliance checkbox from one event backbone.
