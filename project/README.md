# NoteVault secure build project

This local project includes a hardened Flask notes app, an intentionally vulnerable reference for authorized demonstrations, a threat/vulnerability report, CycloneDX SBOM, and GitHub Actions scans/signing workflow.

- Secure app and run instructions: [`starter-app/README.md`](starter-app/README.md)
- Report and submission fields: [`REPORT-TEMPLATE.md`](REPORT-TEMPLATE.md) and [`NoteVault-Secure-Build-Report.pdf`](NoteVault-Secure-Build-Report.pdf)
- Vulnerable demo: start only on an isolated local machine with `docker compose up --build` inside `vulnerable-baseline`; it binds to port 8081. Never expose it publicly.
- Supply-chain workflow: `../.github/workflows/security.yml`. CI regenerates SBOM and signs release artifacts using GitHub OIDC.

Replace `[TEAM_ID]`, repository/video URLs, member names, and private contribution statements before submission. The local SBOM lists direct runtime dependencies; CI generates a dependency-resolved SBOM.
