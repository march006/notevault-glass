# Attack-to-fix evidence (local only)

All requests targeted loopback services on this machine. The baseline ran at `127.0.0.1:8081`; the secure Docker Compose app ran at `localhost:8080`. The baseline database was a disposable temporary SQLite file containing only synthetic notes (`GLASS-SENTINEL`, `XSS-PROOF`, `PRIVATE-NOTE-PROOF`). No real user data or credentials were used.

## F-01 — SQL injection in search (CWE-89)

Baseline request with a normal no-match query:

```http
GET /search?q=NOTFOUND HTTP/1.1
Host: 127.0.0.1:8081
```

Observed response: HTTP 200 with an empty body.

Baseline injection request:

```http
GET /search?q=zz%27%20OR%201%3D1%20--%20 HTTP/1.1
Host: 127.0.0.1:8081
```

Observed response: HTTP 200, body `GLASS-SENTINEL<br>XSS-PROOF`. The search predicate was altered by the input because the baseline interpolates the query into SQL. The fixed route uses placeholders and binds the authenticated `owner_id`; the same request in the secure app did not expose the baseline sentinel.

## F-02 — Unauthenticated note export / IDOR (CWE-639)

Baseline request with no Cookie header:

```http
GET /export/1 HTTP/1.1
Host: 127.0.0.1:8081
```

Observed response: HTTP 200, body `PRIVATE-NOTE-PROOF`. In the secure app, export requires authentication and adds the current owner to the lookup. A separate normal account requesting the first test account's note received HTTP 404.

## F-03 — Stored XSS (CWE-79)

The synthetic record body was `<b>GLASS-XSS-PROOF</b>`. The baseline response from `GET /note/2` included the raw tags, and the browser rendered the text in bold. The secure authenticated home response contained `&lt;b&gt;GLASS-XSS-PROOF&lt;/b&gt;`; the browser displayed the markup literally as text.

Screenshots: `vulnerable-stored-xss.png` and `remediated-stored-xss.png`. The latter is a local HTML snapshot of the actual authenticated secure response so the captured result contains no session cookie.

## F-05 and authorization checks

- A signed-in test user POSTing to `/notes` without a CSRF token received HTTP 400.
- A normal user requesting `/admin` received HTTP 403.
- A normal user requesting another account's `/export/1` received HTTP 404.

The exact remediation is in commit [`fe38f23`](https://github.com/march006/notevault-glass/commit/fe38f23). The SQLite volume ownership regression found while verifying this flow was fixed in [`295d35d`](https://github.com/march006/notevault-glass/commit/295d35d).
