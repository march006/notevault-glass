# NoteVault secure build

Local Flask notes app for the Week 14 secure-build project. It includes login, registration, owner-scoped notes, search, admin view, and PDF export.

## Run
PowerShell (from `project/starter-app`):
```powershell
$env:TEAM_ID="your-team-name" # choose once; keep stable
$env:SECRET_KEY="replace-with-a-long-random-value"
$env:ADMIN_PASSWORD="replace-with-a-long-random-password"
docker compose up --build
```
Open http://localhost:8080 and register a user. The initial `admin` account password comes from `ADMIN_PASSWORD`; use a distinct secret for this local demo. Set `COOKIE_SECURE=1` only when serving behind HTTPS. Data persists in the named volume.

## Security materials
See `../REPORT-TEMPLATE.md`, `.github/workflows/security.yml`, and `../vulnerable-baseline/` for the intentionally vulnerable isolated baseline. Run the baseline locally only, with dummy data.
