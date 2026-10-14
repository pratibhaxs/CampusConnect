# Campus Placement Experience Hub

A full-stack platform for college students to browse real placement/interview
experiences shared by seniors and alumni, searchable by company, college,
role, year, branch, and difficulty — with a question repository, frequency
analysis, and a star-rated recommendation feature.

**Stack:** React (Vite) + **FastAPI** (REST API) + MySQL, JWT auth,
role-based access control (student / alumni / admin).

> **Note on this version:** the backend was originally built in Flask
> (10 phases, fully featured) and has since been **converted to FastAPI**.
> The API paths, request/response JSON shapes, and all business logic are
> identical — the conversion was done to preserve exact contract parity, so
> the React frontend required **zero changes**. The original Flask backend
> is kept at `backend-flask-archive/` alongside this one for reference.

---

## Quick start

### Backend (FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: set DB_PASSWORD to your local MySQL password

# in MySQL: CREATE DATABASE campus_placement_hub;

# create tables (no migration tooling — same as before)
python3 -c "from app.database import Base, engine; from app import models; Base.metadata.create_all(bind=engine)"

python run.py
# or equivalently: uvicorn app.main:app --reload
```

Visit `http://localhost:5000/api/health/db` — should return
`{"status": "ok", "message": "MySQL connection successful"}`.

**New with FastAPI:** interactive API docs are auto-generated — visit
`http://localhost:5000/docs` (Swagger UI) or `/redoc` for a browsable,
try-it-yourself reference of every endpoint. This didn't exist under Flask
and is worth showing off in your viva.

### Add a college, then create your first admin

Same as before — no public admin signup, promote manually in MySQL:

```sql
INSERT INTO colleges (name, city, state) VALUES ('ABC University', 'Meerut', 'UP');
-- after registering a normal account:
UPDATE users SET role = 'admin' WHERE email = 'you@example.com';
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` — works exactly as before; it has no idea the
backend changed frameworks.

### Run the tests

```bash
cd backend
pip install pytest httpx   # httpx powers FastAPI's TestClient
pytest tests/ -v
```

**99 tests, all passing** — the entire test suite was ported 1:1 from the
Flask version (same scenarios, same assertions) using `fastapi.testclient`
instead of Flask's test client, and an in-memory SQLite override via
`app.dependency_overrides` instead of Flask's `TestingConfig`.

---

## What changed under the hood (Flask → FastAPI)

| Concern | Flask (before) | FastAPI (now) |
|---|---|---|
| Routing | Blueprints | `APIRouter` per resource |
| Request validation | Marshmallow schemas | Pydantic models (native to FastAPI) |
| ORM | Flask-SQLAlchemy (`db.Model`, `Model.query`) | Plain SQLAlchemy 2.0 (`Base`, `db.query(Model)`), injected via `Depends(get_db)` |
| Auth | Flask-JWT-Extended + Flask-Bcrypt | `pyjwt` + `bcrypt` directly, with `get_current_user`/`role_required()` as FastAPI dependencies |
| App creation | `create_app(config_name)` factory | `create_app(testing=True)` factory — same pattern, same spirit |
| Error responses | `jsonify({"error": ...})` | Custom exception handlers reshape FastAPI's default `{"detail": ...}` back into `{"error": ...}` / `{"error": "Validation failed", "details": {...}}` — **this is what keeps the frontend working unmodified** |
| Dev server | Flask's built-in server | `uvicorn` (ASGI) |
| API docs | None | Auto-generated at `/docs` and `/redoc` |

**Why the custom exception handlers matter:** FastAPI's default validation
error format is a flat list of `{"loc": [...], "msg": ..., "type": ...}`
objects with a 422 status code. That's different from what the old
Marshmallow-based Flask app returned (`400` with `{"error": "Validation
failed", "details": {field: [messages]}}`), which the React frontend already
parses in a few places (see `Register.jsx`'s `err.response.data.details`
handling). Rather than rewrite the frontend, `app/main.py` registers handlers
that reshape FastAPI's errors back into the old shape. This is the single
most important piece of the conversion — everything else is a fairly direct
line-by-line translation.

**A note on async:** this backend stays fully synchronous (`def`, not `async
def`, in every route) using classic SQLAlchemy with the `PyMySQL` driver —
FastAPI runs sync path functions in a thread pool automatically, so this
works correctly without any extra configuration. Converting to `async def`
with an async driver (`asyncmy` or `aiomysql`) would be the natural next
step for higher concurrency, but wasn't necessary here and would have been
a much larger, riskier change for a project this size.

---

## Feature checklist (against the original spec)

| Area | Status | Notes |
|---|---|---|
| Student register/login, select college, profile | ✅ | JWT + bcrypt |
| Alumni register/login, select college, profile | ✅ | |
| Admin login | ✅ | No public signup — promoted manually in MySQL |
| Role-based access control | ✅ | Enforced server-side via FastAPI dependencies |
| College management | ✅ | Admin CRUD; every experience tied to a college |
| Company pages (roles, experience count, common rounds, topics) | ✅ | `/companies/:id` |
| Structured experience submission (not one big text box) | ✅ | 3-step wizard |
| Recruitment rounds + per-round questions | ✅ | Nested, dynamic add/remove |
| Search & filter (company, college, role, year, branch, difficulty, round type, topic) | ✅ | `/search`, all combine with AND |
| Question repository | ✅ | `/questions`, filterable |
| Frequently Asked Topics | ✅ | Plain `GROUP BY`/`COUNT`, no ML |
| Placement Intelligence Dashboard | ✅ | Per-company: avg rounds, first-round mode, topic %, avg difficulty, bar chart |
| Recommendation feature (star ratings) | ✅ | Per company, optionally per role |
| Bookmarks (experiences, questions, companies) | ✅ | Student-only, per spec |
| Helpful votes | ✅ | One per student per experience, toggleable |
| Report feature | ✅ | fake / inappropriate / spam / incorrect |
| Admin: manage users | ⚠️ Partial | Promotion is manual (MySQL); no admin "manage users" UI page |
| Admin: manage colleges/companies | ✅ | Companies fully in UI; colleges via API only |
| Admin: approve/reject experiences | ✅ | `/admin/experiences`, real UI |
| Admin: manage reports | ✅ | `/admin/reports` |
| Admin: platform statistics | ✅ | `/admin/statistics`, with charts |
| Responsive design | ✅ | Navbar collapses, tables scroll, forms stack on mobile |

---

## Viva walkthrough (suggested demo order)

1. **Register a student**, then an **alumni** account.
2. **Promote a third account to admin** via MySQL.
3. Show `/docs` (Swagger UI) — a good moment to mention the Flask→FastAPI
   conversion and that this is auto-generated for free.
4. As **admin**: `/admin/companies` → add a company + role.
5. As **alumni**: `/alumni/submit-experience` → fill the 3-step form → submit.
6. As **admin**: `/admin/experiences` → Approve it.
7. As **student**: `/companies/:id` → see the Placement Intelligence
   Dashboard and Recommendation panel populate.
8. `/search`, `/questions`, bookmark something → `/student/saved`.
9. On the experience detail page: **Mark as helpful**, **Report** it.
10. As **admin**: `/admin/reports` → resolve it. `/admin/statistics` → charts.
11. Resize the browser narrow → navbar collapses (mobile responsiveness).

---

## Known limitations

- **No DB migration tooling.** Tables are created with a one-off
  `Base.metadata.create_all()` script. Alembic (the SQLAlchemy-native
  migration tool, works the same way under both Flask and FastAPI) would be
  the natural addition for a system with real production data.
- **Topic matching is exact (case-insensitive) string matching**, not fuzzy —
  a deliberate "simple queries, not ML" choice from the spec.
- **Admin user management is manual (MySQL), not a UI page** — a scope cut
  for a medium-level project; a rare operation versus the daily-use features
  that got the UI investment.
- **No email verification, password reset, or OAuth.**
- **Stats/recommendations are computed live on every request**, not cached.
- **Synchronous DB access**, not async — see "A note on async" above.

---

## Project structure

```
backend/
  app/
    models/       SQLAlchemy models (one file per table)
    schemas/       Pydantic request/response models
    routers/       FastAPI APIRouters (one file per resource)
    database.py    engine, SessionLocal, Base, get_db dependency
    security.py     password hashing, JWT, auth dependencies
    config.py       Settings (pydantic-settings, reads .env)
    main.py         create_app() factory, CORS, exception handlers
  tests/          99 pytest tests across 12 files, using TestClient
  run.py, requirements.txt

backend-flask-archive/   the original Flask implementation, kept for reference

frontend/                unchanged by the backend conversion
  src/
    api/, components/, context/, pages/, routes/
```

See `campus-placement-hub-architecture.md` (delivered separately, at the
start of this build) for the full original architecture plan and roadmap
this project followed phase-by-phase — note it describes the Flask version;
the FastAPI conversion came after all 10 phases were complete.
