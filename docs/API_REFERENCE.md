# CH360 Backend API Reference

Base URL prefixes
- Auth: `/api/auth/`
- Accounts: `/api/accounts/`
- Students: `/api/v1/students/`
- Faculty: `/api/v1/faculty/`
- Academics: `/api/v1/academics/`
- Departments: `/api/v1/departments/`
- Attendance: `/api/v1/attendance/`
- Placements: `/api/v1/placements/`
- Grads: `/api/v1/grads/`
- RnD: `/api/v1/rnd/`
- Facilities: `/api/v1/facilities/`
- Exams: `/api/v1/exams/`
- Fees: `/api/v1/fees/`
- Transport: `/api/v1/transport/`
- Mentoring: `/api/v1/mentoring/`
- Feedback: `/api/v1/feedback/`
- Open Requests: `/api/v1/open-requests/`
- Assignments: `/api/v1/assignments/`

Auth
- POST `/api/auth/token/` obtain JWT
- POST `/api/auth/token/refresh/` refresh JWT

Accounts
- POST `/api/accounts/register/` register user
- GET `/api/accounts/me/` current user
- POST `/api/accounts/logout/` logout
- GET `/api/accounts/me/roles-permissions/` effective roles & permissions

Students (selected)
- CRUD `/api/v1/students/` students
- Custom fields `/api/v1/students/custom-fields/`
- Documents `/api/v1/students/documents/`

Faculty
- CRUD `/api/v1/faculty/`

Academics
- Courses `/api/v1/academics/api/courses/`
- Syllabi `/api/v1/academics/api/syllabi/`
- Timetables `/api/v1/academics/api/timetables/`
- Enrollments `/api/v1/academics/api/enrollments/`
- Academic calendar `/api/v1/academics/api/academic-calendar/`

Departments
- CRUD `/api/v1/departments/`
- Resources `/api/v1/departments/resources/`
- Announcements `/api/v1/departments/announcements/`
- Events `/api/v1/departments/events/`
- Documents `/api/v1/departments/documents/`
- Stats `/api/v1/departments/stats/`
- Search `/api/v1/departments/search/`

Attendance, Placements, Grads, RnD, Facilities, Exams, Fees, Transport, Mentoring, Feedback, Open Requests, Assignments
- Each app exposes RESTful endpoints under its base prefix; list with `GET` on the collection to discover schemas.

Implementation guide
- Auth
  - Include HTTP header: `Authorization: Bearer <access_token>` after login.
  - Refresh token periodically using the refresh endpoint.
- Pagination
  - List endpoints default to page size 20. Use query `?page=` and `?page_size=`.
- Filtering & search
  - Many list endpoints accept filters via query params (e.g., `?status=ACTIVE`).
  - Some support search: `?search=term` and ordering: `?ordering=field`.
- Idempotency & retries
  - For create operations that may be retried, include a client-generated idempotency key header and handle 409 conflicts.
- Error handling
  - Standard DRF error format: HTTP 4xx/5xx with `{detail: ...}`.
- Rate limits
  - Token endpoints are rate-limited; backoff on 429.

Common curl examples
- Login
  curl -X POST $BASE/api/auth/token/ -H "Content-Type: application/json" -d '{"email":"user@example.com","password":"secret"}'
- List departments
  curl -H "Authorization: Bearer $TOKEN" $BASE/api/v1/departments/
- Create announcement
  curl -X POST $BASE/api/v1/departments/announcements/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"department":"<uuid>","title":"Welcome","content":"Hi","announcement_type":"GENERAL"}'

Notes
- UUIDs are used for primary keys in most resources.
- Case-insensitive unique constraints on emails/identifiers prevent duplicates.
- For high throughput, prefer bulk endpoints where available and minimize N+1 calls.

Health & Metrics
- GET `/health/`, `/health/detailed/`, `/health/ready/`, `/health/alive/`
- GET `/metrics/app` – application RPS and request/DB latency percentiles