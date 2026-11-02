# SiteSentry Check Catalog

This catalog documents all 16 passive checks implemented in SiteSentry, detailing their purpose, security rationale, detection criteria, and false positive mitigations.

---

## 1. Security Header Checks

### `hdr-csp` — Content-Security-Policy
- **What it checks:** Validates whether a `Content-Security-Policy` header is present on crawled HTML responses and inspects for permissive directives (`'unsafe-inline'`, `'unsafe-eval'`, wildcard `*` sources).
- **Why it matters:** CSP provides strong mitigation against Cross-Site Scripting (XSS), clickjacking, and unauthorized resource injection.
- **Severity:** Medium (missing header); Low (weak or wildcard directives).
- **Detection:** Inspects `content-security-policy` in response headers for status codes `< 400`.
- **False Positives:** Single-page applications delivering CSP via HTML `<meta http-equiv="...">` tags are noted; server header delivery is recommended.

### `hdr-hsts` — HTTP Strict Transport Security
- **What it checks:** Confirms the presence of `Strict-Transport-Security` on HTTPS pages, verifying that `max-age` is at least 6 months (15,768,000 seconds) and includes the `includeSubDomains` directive.
- **Why it matters:** Protects users against SSL-stripping and man-in-the-middle attacks by ensuring browsers only connect over TLS.
- **Severity:** Medium (missing on HTTPS); Low (short max-age or missing `includeSubDomains`).
- **Detection:** Checked only on HTTPS responses.

### `hdr-xfo` — X-Frame-Options
- **What it checks:** Checks for `X-Frame-Options` (`DENY` or `SAMEORIGIN`) or an equivalent CSP directive with `frame-ancestors`.
- **Why it matters:** Protects users from clickjacking and UI redressing attacks.
- **Severity:** Low.
- **Detection:** Triggers only if neither `X-Frame-Options` nor `frame-ancestors` exists.

### `hdr-xcto` — X-Content-Type-Options
- **What it checks:** Verifies that `X-Content-Type-Options: nosniff` is present.
- **Why it matters:** Prevents browsers from MIME-sniffing response payloads away from the declared content type.
- **Severity:** Low.
- **Detection:** Checks that header value equals `nosniff`.

### `hdr-referrer` — Referrer-Policy
- **What it checks:** Ensures a `Referrer-Policy` header is specified.
- **Why it matters:** Prevents sensitive path parameters and user session tokens from leaking to external referrers.
- **Severity:** Info.
- **Detection:** Flags when `referrer-policy` is omitted.

### `hdr-permissions` — Permissions-Policy
- **What it checks:** Ensures a `Permissions-Policy` header is declared.
- **Why it matters:** Restricts embedded iframes and third-party scripts from accessing powerful browser APIs (geolocation, microphone, camera).
- **Severity:** Info.
- **Detection:** Flags when `permissions-policy` is omitted.

---

## 2. Cookie Security Checks

### `cookie-flags` — Cookie Security Attributes
- **What it checks:** Examines all `Set-Cookie` directives for missing `Secure`, `HttpOnly`, and `SameSite` flags.
- **Why it matters:** Missing `Secure` allows interception over plaintext HTTP; missing `HttpOnly` exposes session tokens to XSS theft; missing `SameSite` exposes state-changing endpoints to CSRF.
- **Severity:** Medium for session-like cookie names (`session`, `sid`, `token`, `auth`, `jwt`, `csrf`); Low for general cookies.
- **Detection:** Evaluates parsed key-value pairs from `Set-Cookie`.

---

## 3. Cryptography & Transport Checks

### `tls-cert` — TLS Certificate Health
- **What it checks:** Connects to the host using `ssl.create_default_context()` and checks certificate validity, expiration, self-signed issuers, and approaching expiration windows (< 14 days, < 30 days).
- **Why it matters:** Expired or untrusted certificates compromise user trust and trigger browser security blocks.
- **Severity:** High (expired, untrusted, or self-signed); Medium (< 14 days to expiration); Low (< 30 days).
- **Detection:** Runs stdlib socket/ssl queries in a worker thread (`asyncio.to_thread`).

### `tls-protocol` — Deprecated TLS Protocols
- **What it checks:** Tests whether the target server still negotiates legacy TLS 1.0 or TLS 1.1 handshakes.
- **Why it matters:** TLS 1.0 and 1.1 have known cryptographic vulnerabilities (e.g., BEAST, POODLE) and are deprecated across major browsers.
- **Severity:** Medium.
- **Detection:** Attempts dedicated handshakes restricted to TLS 1.0 and 1.1.

### `redirect-https` — HTTP to HTTPS Redirection
- **What it checks:** When scanning an HTTPS target, queries the HTTP counterpart to verify it issues an immediate 3xx redirect to `https://`.
- **Why it matters:** Plaintext HTTP access exposes users to eavesdropping if redirects are missing.
- **Severity:** Medium.
- **Detection:** Dispatches a non-following GET to `http://<netloc>/` and verifies the `Location` header begins with `https://`.

---

## 4. Origin & Resource Integrity Checks

### `cors-misconfig` — Cross-Origin Resource Sharing
- **What it checks:** Sends a benign test probe with header `Origin: https://sitesentry.invalid` and checks whether the server reflects it or allows wildcard origins with credentials.
- **Why it matters:** Permissive reflection allows arbitrary third-party websites to read private user responses or perform authenticated actions.
- **Severity:** High (`Access-Control-Allow-Origin: *` with `Allow-Credentials: true`, or reflection with credentials); Medium (arbitrary reflection without credentials).
- **Detection:** Checks response headers against probe origin.

### `mixed-content` — Mixed HTTP Content on HTTPS Pages
- **What it checks:** Scans HTTPS HTML responses for embedded subresources (`<script>`, `<link>`, `<img>`, `<iframe>`, `<object>`, `<embed>`) loaded over `http://`.
- **Why it matters:** Network attackers can intercept unencrypted HTTP subresources and manipulate the page context.
- **Severity:** Medium.
- **Detection:** Beautiful Soup HTML tag parsing on HTTPS pages.

### `sri-missing` — Missing Subresource Integrity
- **What it checks:** Checks external `<script src="...">` and `<link rel="stylesheet">` elements for missing `integrity` attributes.
- **Why it matters:** If a third-party CDN is compromised, attackers can inject malicious scripts into visiting browsers.
- **Severity:** Low.
- **Detection:** Scans tags pointing to external origins without an `integrity` attribute.

---

## 5. Exposure & Information Disclosure Checks

### `exposed-files` — Sensitive File Exposure
- **What it checks:** Probes a fixed set of standard paths: `/.git/HEAD`, `/.env`, `/.DS_Store`, `/backup.zip`, `/phpinfo.php`, `/server-status`, `/.well-known/security.txt`.
- **Why it matters:** Exposed source control files, environment configurations, and database backups lead directly to credential compromise.
- **Severity:** High (`.git/HEAD`, `.env`, `/backup.zip`); Medium (`.DS_Store`, `phpinfo.php`, `server-status`); Info (absence of `security.txt`).
- **Detection & Safety:**
  - **No Secrets in Output:** The scanner never prints or records the contents of discovered sensitive files; only the status code and size are reported.
  - **Soft-404 Mitigation:** Compares responses against the baseline soft-404 probe before reporting, and verifies expected content markers (such as `ref:` for `.git/HEAD`).

### `tech-disclosure` — Software Version Disclosure
- **What it checks:** Scans `Server`, `X-Powered-By`, and `<meta name="generator">` tags for product names and versions (e.g., `Apache/2.4.49`, `PHP/7.4.3`).
- **Why it matters:** Granular version disclosure assists attackers in mapping known CVEs to target hosts.
- **Severity:** Low (reveals specific version); Info (discloses product name only).
- **Detection:** Regular expression parsing across headers and HTML meta tags.

### `dir-listing` — Directory Listing Enabled
- **What it checks:** Identifies default server file directory listings (e.g., `Index of /`, `[To Parent Directory]`).
- **Why it matters:** Exposes unlinked files, temporary backups, and internal file architectures.
- **Severity:** Medium.
- **Detection:** Keyword and pattern matching on crawled HTML responses.
