# Development Task List: personal_blog

> Project: Personal Blog (FastAPI + React 18 + Vite + Tailwind + TipTap)
> Date: 2026-08-15
> Owner: Charlie (PM)

---

## Phase 1: Backend Foundation (P0)

| ID | Task | Description | Acceptance Criteria | Dep | Effort | Layer |
|----|------|-------------|-------------------|-----|--------|-------|
| T01 | Set up FastAPI project skeleton | Create project directory, `pyproject.toml`, `app/` package, `main.py` entry point, Alembic init | `python -m app.main` starts a live server on `:8000`; health endpoint returns 200 | None | 1h | Backend |
| T02 | Configure settings with Pydantic Settings | Extract DB URL, JWT secret, CORS origins, upload path, jieba dict path into `Settings`; load from `.env` | Settings loads from env file; missing required keys raise `ValidationError`; all keys accessible via `get_settings()` singleton | T01 | 1h | Backend |
| T03 | Define SQLAlchemy models for all 7 tables | `User`, `Post`, `Category`, `Tag`, `PostTag` (association), `Comment`, `Setting`; define proper column types, indexes, foreign keys, cascade rules | All 7 models pass `Base.metadata.create_all()` without errors; Alembic `autogenerate` produces a non-empty revision diff | T01 | 2h | Backend |
| T04 | Wire up Alembic migrations | Create initial migration from models; add `alembic upgrade head` script; verify migration creates all 7 tables | `alembic upgrade head` on a fresh DB creates all tables; `alembic downgrade -1` removes them; migration files checked into VCS | T03 | 1h | Backend |
| T05 | Implement auth middleware & dependency helpers | JWT decode middleware (`get_current_user`), role-check decorator (`require_role`), CORS middleware registration | JWT token in `Authorization` header resolves to a `User` object; expired/invalid tokens return 401; CORS preflight passes for configured origins | T02, T03 | 1.5h | Backend |
| T06 | Write unit tests for models & settings | `pytest` tests for Settings loading, model constraints (unique slug, nullable fields), Alembic migration dry-run | All tests pass with `pytest tests/`; coverage on `models/` ≥ 80% | T03, T04 | 1.5h | Backend |

---

## Phase 2: Backend APIs — Auth (P0)

| ID | Task | Description | Acceptance Criteria | Dep | Effort | Layer |
|----|------|-------------|-------------------|-----|--------|-------|
| T07 | User registration endpoint | `POST /api/auth/register` — validate input, hash password (bcrypt), create user, return JWT pair | Register with valid payload → 201 + `{access_token, refresh_token, user}`; duplicate email → 409; invalid email format → 422 | T05 | 2h | Backend |
| T08 | Login & refresh endpoints | `POST /api/auth/login` (returns JWT), `POST /api/auth/refresh` (refresh token rotation) | Correct credentials → 200 + tokens; wrong password → 401 (same message as wrong user); expired refresh → 401 | T07 | 2h | Backend |
| T09 | Me / profile endpoints | `GET /api/auth/me` (current user info), `PATCH /api/auth/me` (update username/avatar) | `me` returns full user excluding password hash; `PATCH` requires JWT; invalid fields return 422 | T07 | 1h | Backend |
| T10 | Auth API integration tests | `pytest` with `TestClient`: register → login → refresh → me, plus negative cases (bad password, missing token, expired token) | All scenarios pass; test DB is isolated (transaction rollback per test) | T07, T08, T09 | 1.5h | Backend |

---

## Phase 3: Backend APIs — Posts CRUD + Slug + Preview (P0)

| ID | Task | Description | Acceptance Criteria | Dep | Effort | Layer |
|----|------|-------------|-------------------|-----|--------|-------|
| T11 | Post CRUD endpoints | `GET/POST/PATCH/DELETE /api/posts` + `GET/PATCH/DELETE /api/posts/{id}`; PATCH supports partial update; DELETE is soft-delete | All 5 endpoints pass integration tests; soft-deleted posts excluded from list by default; only author/admin can PATCH/DELETE | T07, T09 | 2h | Backend |
| T12 | Slug generation & unique constraint | Auto-generate URL-safe slug from title on create; allow override; enforce uniqueness via DB index + application-level retry | Two posts with identical slug → second rejected 409; slug change on PATCH updates index; non-ASCII title produces ASCII slug | T11 | 1h | Backend |
| T13 | Markdown preview & TOC extraction | `POST /api/posts/preview` — accept raw Markdown, return rendered HTML + auto-generated TOC JSON | Preview renders headings/tables/code fences; TOC extracts H2/H3 headings with anchor IDs; no XSS (HTML sanitized) | T11 | 2h | Backend |
| T14 | Post list pagination & filtering | `GET /api/posts` supports `page`, `page_size`, `category_id`, `tag_id`, `status` (draft/published) query params | Correct page boundaries; empty pages return `[]` not error; filter by category/tag/status works correctly | T11 | 1h | Backend |
| T15 | Post CRUD integration tests | Test happy path + edge cases (empty title, draft visibility, slug collision, pagination bounds) | All tests green; ≥ 90% branch coverage on `posts/` | T11–T14 | 2h | Backend |

---

## Phase 4: Backend APIs — Media Upload (P0)

| ID | Task | Description | Acceptance Criteria | Dep | Effort | Layer |
|----|------|-------------|-------------------|-----|--------|-------|
| T16 | Image upload endpoint | `POST /api/media/upload` (multipart) — validate MIME/size, generate thumbnail, save to filesystem, return CDN URL | JPEG/PNG/WebP accepted up to 10 MB; invalid MIME rejected 400; thumbnail (max 400×400) generated and stored alongside | T02, T05 | 2h | Backend |
| T17 | Video upload endpoint | `POST /api/media/upload-video` — validate MP4/WebM up to 200 MB, generate 1s screenshot thumbnail, store metadata | File saved with unique hash filename; thumbnail PNG generated; upload progress not required but metadata (duration, size, mime) returned | T16 | 2h | Backend |
| T18 | Media management endpoints | `GET /api/media` (list user's files), `DELETE /api/media/{id}` (soft-delete with cascade); expose via `GET /api/media/{id}/thumbnail` | List paginated; delete removes file + all references; thumbnail route serves stored thumbnail at correct content-type | T16 | 1.5h | Backend |
| T19 | Media upload tests | Upload valid/invalid files; verify thumbnail generation; verify storage cleanup on delete | All file types tested (valid image, invalid MIME, oversized file, video); temp files cleaned after test run | T16, T17, T18 | 1.5h | Backend |

---

## Phase 5: Backend APIs — Categories, Tags, Comments, Search, Settings (P0/P1)

| ID | Task | Description | Acceptance Criteria | Dep | Effort | Layer |
|----|------|-------------|-------------------|-----|--------|-------|
| T20 | Categories CRUD | Full CRUD on `/api/categories`; enforce unique name; cascading delete removes post references | Create/list/update/delete all work; deleting a category with posts fails 409 (unless `force=true`); ≤ 50 categories hard limit | T07 | 1.5h | Backend |
| T21 | Tags CRUD + post tagging | Full CRUD on `/api/tags`; `PATCH /api/posts/{id}/tags` — set tag list (N:M via `PostTag`); tag cloud endpoint | Tag creation idempotent on name; tag association works for multiple tags; tag cloud returns `{name, count}` sorted desc | T11, T20 | 2h | Backend |
| T22 | Comments CRUD + nested | `GET/POST /api/posts/{id}/comments` (paginated, thread-safe); `PATCH/DELETE /api/comments/{id}`; support `reply_to` for nesting up to 3 levels | List sorted by created_at desc; reply_to creates correct tree; author + admin can delete; soft-delete hides content but keeps thread structure | T11 | 2h | Backend |
| T23 | Search with jieba | `GET /api/search?q=<keyword>` — use jieba for Chinese word segmentation + English split; full-text search across title, content, tags; return top 20 results | Chinese query returns relevant posts; English query works; empty query returns 422; results include snippet with keyword highlighted | T11, T13 | 2h | Backend |
| T24 | Settings CRUD | Singleton-style `GET/POST/PATCH /api/settings/{key}` — admin only; keys like `site_title`, `site_description`, `seo_keywords`, `footer_text` | Non-admin returns 403; key is a unique slug; `GET /api/settings` returns all; `POST` creates if missing | T07, T09 | 1h | Backend |
| T25 | Phase 5 integration tests | End-to-end tests for categories, tags, comments, search, settings | All endpoints covered; jieba tokenizer behavior verified with known words; settings isolation per user role | T20–T24 | 2h | Backend |

---

## Phase 6: Frontend Setup — Vite + Tailwind + Router + Zustand (P0)

| ID | Task | Description | Acceptance Criteria | Dep | Effort | Layer |
|----|------|-------------|-------------------|-----|--------|-------|
| T26 | Vite + React 18 + TS scaffold | `npm create vite@latest` with React TS template; remove boilerplate; add ESLint + Prettier + Husky | `npm run dev` serves on `:5173`; TypeScript strict mode on; no lint errors on empty app | None | 1h | Frontend |
| T27 | Tailwind CSS setup | Install Tailwind + PostCSS; configure `tailwind.config.js` with custom theme (colors, fonts); set up dark mode (`class` strategy) | Tailwind classes apply; dark mode toggle switches `html class`; custom colors/font tokens available via `@theme` | T26 | 1h | Frontend |
| T28 | React Router + layout shell | Configure React Router v6 with lazy-loaded routes; create `Layout` component (header/nav + footer + `<Outlet>`) | Root layout renders header + footer on all pages; at least 3 test routes (home, about, 404); code-split bundles | T26 | 1.5h | Frontend |
| T29 | Zustand store + API client | Create Zustand store (`authStore`, `postStore`) with `immer` middleware; wrap Axios with base URL, JWT interceptor, and error mapping | Store exposes typed actions; Axios auto-attaches JWT from localStorage; 401 triggers store cleanup + redirect to login | T26, T28 | 2h | Frontend |
| T30 | Component library scaffolding | Create shared components: `Button`, `Input`, `Card`, `Modal`, `Toast` (using Tailwind + `sonner` or `react-hot-toast`); Storybook optional | All shared components importable from `@components/*`; Toast notifications work globally; basic accessibility (aria labels) | T27 | 1.5h | Frontend |

---

## Phase 7: Frontend Auth Pages + Protected Routes (P0)

| ID | Task | Description | Acceptance Criteria | Dep | Effort | Layer |
|----|------|-------------|-------------------|-----|--------|-------|
| T31 | Login & Register pages | Build login form (email + password) and register form (email + username + password + confirm); form validation with `react-hook-form` + `zod` | Both pages reachable; zod schema validates input before submit; success redirects to dashboard; error messages displayed inline | T30 | 2h | Frontend |
| T32 | JWT localStorage + auth flow | On login → store access + refresh tokens; refresh logic when 401 received; logout clears tokens + redirects | Token persists across page reload; expired access token auto-refreshed once; failed refresh logs out user | T29, T31 | 1.5h | Frontend |
| T33 | Protected route wrapper | `ProtectedRoute` component — redirects unauthenticated users to `/login`; shows loading state during auth check | All admin routes (`/admin/*`) behind `ProtectedRoute`; direct URL access to `/admin` without token redirects to login | T32 | 1h | Frontend |
| T34 | Auth page tests | React Testing Library: form validation, submit success/failure, redirect behavior | All scenarios covered; no unhandled promise rejections; mock API responses with `msw` | T31, T32, T33 | 1.5h | Frontend |

---

## Phase 8: Frontend Post List + Detail Pages (P0)

| ID | Task | Description | Acceptance Criteria | Dep | Effort | Layer |
|----|------|-------------|-------------------|-----|--------|-------|
| T35 | Post list page | Fetch posts with pagination; render as responsive card grid; show title, excerpt, date, category, tag chips; infinite scroll or paginated buttons | Page loads with skeleton loaders; pagination controls work; empty state displayed when no posts; click card navigates to detail | T33, T29 | 2h | Frontend |
| T36 | Post detail page | Fetch single post by slug; render title, author, date, rendered Markdown body, tags, related posts sidebar; share buttons | Slug-based URL resolves correctly; 404 shown for unknown slug; related posts shown below (same category, max 3); TOC sidebar on desktop | T35 | 2h | Frontend |
| T37 | Markdown rendering + code highlighting | Use `react-markdown` + `remark-gfm` + `rehype-highlight` for code blocks with Prism.js syntax highlighting | Tables, task lists, code fences render correctly; light/dark code block themes match site theme | T36 | 1.5h | Frontend |
| T38 | Post pages tests | RTL tests: render list items, navigate to detail, verify markdown rendering, test 404 handling | All scenarios green; snapshots for key components | T35, T36, T37 | 1.5h | Frontend |

---

## Phase 9: Frontend Admin Panel + TipTap Editor + Media Upload (P0)

| ID | Task | Description | Acceptance Criteria | Dep | Effort | Layer |
|----|------|-------------|-------------------|-----|--------|-------|
| T39 | Admin dashboard layout | Admin sidebar (Posts, Categories, Tags, Comments, Settings); top bar with user avatar/logout; role-gated access (admin only) | Sidebar navigation works; non-admin users see 403 page; responsive collapse on mobile | T33 | 2h | Frontend |
| T40 | TipTap rich-text editor integration | Install `@tiptap/react` + extensions (heading, paragraph, bullet-list, ordered-list, code-block, image, link, placeholder); custom image upload handler → calls backend media API | Editor renders toolbar correctly; all extensions functional; image upload triggers backend API and inserts URL into content; save to draft works | T29, T39 | 3h | Frontend |
| T41 | Post create / edit form | Full form: title, slug (auto+editable), category select, tag multi-select, TipTap content, status (draft/published), cover image picker; save as draft + publish | All fields persisted; draft/published toggle works; form validation blocks submit with empty content; slug auto-generates but is editable | T40 | 2.5h | Frontend |
| T42 | Media upload widget | File picker → drag-and-drop or click → upload to backend → thumbnail preview → confirm to insert; support image + video; progress bar | Drag-and-drop works for both files; progress bar shows upload %; video files show duration after upload; inserted media renders correctly in editor | T16, T17 | 2h | Frontend |
| T43 | Post management list + edit | Admin post table: sortable columns, status badges, search filter, bulk delete; inline edit for title/category; delete confirmation modal | Sort by date/title/status works; bulk delete confirmed with modal; edit opens inline or navigates to edit form | T35, T41 | 2h | Frontend |
| T44 | Admin editor tests | RTL + happy-dom: editor renders, content save roundtrip, media upload mock, form validation errors | Editor content persists across save/load; validation blocks empty save; mock media upload returns test URL | T41, T42 | 2h | Frontend |

---

## Phase 10: Frontend Comments / Search / Settings / Categories (P1)

| ID | Task | Description | Acceptance Criteria | Dep | Effort | Layer |
|----|------|-------------|-------------------|-----|--------|-------|
| T45 | Comments section on post detail | Nested comment display (up to 3 levels); reply form; submit new comment; "Reply" and "Delete" actions for author/admin | Comments load with skeleton; nested indentation visible; reply form opens below target; delete shows confirmation | T36 | 2h | Frontend |
| T46 | Search page | Search input with live debounce; result cards with highlighted keywords; filter by category; instant results as user types | Debounced requests (≥ 300ms); keyword highlighting in title/snippet; no request on empty input; category filter updates results | T23 | 1.5h | Frontend |
| T47 | Site settings admin page | Form for site title, description, SEO keywords, footer text, logo upload; auto-save or save button; real-time preview | Changes saved and reflected on public-facing pages; logo upload uses media API; preview updates live | T24, T39 | 2h | Frontend |
| T48 | Categories & Tags admin pages | Category CRUD (create/edit/delete with cascade warning); Tag CRUD with tag cloud preview; post-tag assignment via multi-select on post edit | Category delete warns about linked posts; tag cloud shows count; tag assignment syncs immediately | T20, T21 | 1.5h | Frontend |
| T49 | Phase 10 tests | RTL tests for comments (nesting + reply), search debounce, settings save | All scenarios covered; debounced requests verified with fake timers; nested comment tree renders correctly | T45–T48 | 2h | Frontend |

---

## Phase 11: Frontend Responsive Polish + Unit Tests (P1)

| ID | Task | Description | Acceptance Criteria | Dep | Effort | Layer |
|----|------|-------------|-------------------|-----|--------|-------|
| T50 | Mobile-first responsive audit | Test all pages at 320px, 768px, 1024px, 1440px breakpoints; fix overflow, alignment, touch targets; ensure mobile nav (hamburger) works | All pages pass Lighthouse mobile audit ≥ 90; no horizontal scroll on any page; touch targets ≥ 44×44px | T39, T45, T46, T47 | 2h | Frontend |
| T51 | Dark mode & theme polish | Refine dark mode tokens (colors, borders, shadows); ensure all components respect theme; test transitions; persist preference in localStorage | Theme toggle flips all components; no flash of wrong theme on reload; smooth 150ms transition | T27, T35 | 1.5h | Frontend |
| T52 | Accessibility pass (WCAG AA) | Audit with axe-core: alt texts on images, ARIA labels on buttons/forms, keyboard navigation, focus management, color contrast | No critical axe violations; keyboard-only navigation works for all interactive elements; contrast ratio ≥ 4.5:1 | T50, T51 | 2h | Frontend |
| T53 | Comprehensive unit tests | Jest/RTL tests for all shared components, store actions, utility functions, form validation schemas; aim ≥ 70% coverage | All existing tests pass; new tests cover edge cases (empty state, error state, loading state); CI-ready | T34, T38, T44, T49 | 3h | Frontend |

---

## Phase 12: Integration + Docker + README (P0)

| ID | Task | Description | Acceptance Criteria | Dep | Effort | Layer |
|----|------|-------------|-------------------|-----|--------|-------|
| T54 | End-to-end integration test | Playwright/Cypress: register → login → create post with media → publish → view on list → search → add comment → logout | Full happy path passes; tests run in headless mode; screenshots on failure captured | T50, T53 | 3h | Integration |
| T55 | Docker Compose stack | `docker-compose.yml` with services: `backend` (FastAPI + Uvicorn), `frontend` (Nginx serving Vite build), `postgres` (with healthcheck), `redis` (optional, for rate limiting) | `docker compose up` starts all services; backend connects to DB; frontend proxies API requests; `.env.example` committed | T54 | 2h | DevOps |
| T56 | Health check + graceful shutdown | Backend health endpoint (`GET /health`); Docker healthcheck; SIGTERM handler for graceful DB connection close | `curl localhost:8000/health` returns `{"status":"ok"}`; `docker compose down` completes without data loss; DB connections drained | T55 | 1h | Backend |
| T57 | README + architecture docs | `README.md`: project overview, tech stack, quickstart (env setup, docker, npm), API docs link (OpenAPI/Swagger), project structure tree | A developer can clone, configure, and run the project in < 10 min following README; Swagger UI accessible at `/docs` | T54, T55 | 1.5h | Docs |
| T58 | CI/CD pipeline (GitHub Actions) | Workflow: lint + test on PR, build Docker image on merge to main, deploy to staging | PR triggers `pytest` + `npm test` + `npm run build`; main merge builds and pushes image; deploy step placeholder for manual trigger | T54, T55, T56 | 2h | DevOps |

---

## Summary

| Phase | Priority | Tasks | Total Effort | Layer |
|-------|----------|-------|-------------|-------|
| 1. Backend Foundation | P0 | T01–T06 | 8.5h | Backend |
| 2. Auth APIs | P0 | T07–T10 | 6.5h | Backend |
| 3. Posts CRUD + Slug + Preview | P0 | T11–T15 | 8h | Backend |
| 4. Media Upload | P0 | T16–T19 | 7h | Backend |
| 5. Categories/Tags/Comments/Search/Settings | P0/P1 | T20–T25 | 10.5h | Backend |
| 6. Frontend Setup | P0 | T26–T30 | 7h | Frontend |
| 7. Auth Pages + Protected Routes | P0 | T31–T34 | 6h | Frontend |
| 8. Post List + Detail | P0 | T35–T38 | 7h | Frontend |
| 9. Admin + Editor + Media | P0 | T39–T44 | 13.5h | Frontend |
| 10. Comments/Search/Settings/Categories | P1 | T45–T49 | 9.5h | Frontend |
| 11. Responsive + A11y + Unit Tests | P1 | T50–T53 | 8.5h | Frontend |
| 12. Integration + Docker + README | P0 | T54–T58 | 9.5h | Integration/DevOps/Docs |
| **Total** | | **58 tasks** | **101h** | |

### Legend

| Column | Meaning |
|--------|---------|
| **Dep** | Dependency task IDs that must be completed first |
| **Effort** | Estimated wall-clock time per task (single developer) |
| **Layer** | Backend / Frontend / Integration / DevOps / Docs |
| **Priority** | P0 = must ship in MVP; P1 = post-MVP enhancement |

### Milestone Gates

| Milestone | Criteria | Tasks |
|-----------|----------|-------|
| **M1 — Backend ready** | All backend APIs pass integration tests; Swagger docs accessible | T01–T25 |
| **M2 — Frontend MVP** | Register → login → create post → publish → view flow works | T26–T44 |
| **M3 — Feature complete** | Comments, search, settings, categories all functional | T45–T49 |
| **M4 — Ship ready** | Dockerized, tested, documented, CI passing | T50–T58 |