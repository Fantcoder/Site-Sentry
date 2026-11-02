# SiteSentry Scan Report

| Field | Value |
|---|---|
| Target | `http://127.0.0.1:59205` |
| Scan ID | `3749f629-796f-4db4-8d2f-f0a29208fcba` |
| Started | 2026-11-02 13:10:10 UTC |
| Completed | 2026-11-02 13:10:11 UTC |
| Pages Crawled | 5 |
| **Grade** | **F** |
| **Score** | **30/100** |

## Score Breakdown

| Check | Findings | Deduction |
|---|---|---|
| hdr-csp | 1 | -7 |
| hdr-hsts | 0 | -0 |
| hdr-xfo | 1 | -3 |
| hdr-xcto | 1 | -3 |
| hdr-referrer | 1 | -0 |
| hdr-permissions | 1 | -0 |
| cookie-flags | 1 | -7 |
| tls-cert | 0 | -0 |
| tls-protocol | 0 | -0 |
| redirect-https | 1 | -7 |
| cors-misconfig | 0 | -0 |
| exposed-files | 5 | -30 |
| tech-disclosure | 2 | -6 |
| mixed-content | 0 | -0 |
| sri-missing | 0 | -0 |
| dir-listing | 1 | -7 |

## Findings

### 🔴 High (3)

#### [exposed-files] .git/HEAD exposed

- **URL:** `http://127.0.0.1:59205/.git/HEAD`
- **Evidence:** `HTTP 200, size=21 bytes, body starts with 'ref: refs/heads/main\n'`
- **Explanation:** Git repository HEAD file is publicly accessible
- **Fix:** Remove or restrict access to /.git/HEAD. Ensure your web server does not serve sensitive files. Add these paths to your .gitignore and review deployment scripts.

#### [exposed-files] .env file exposed

- **URL:** `http://127.0.0.1:59205/.env`
- **Evidence:** `HTTP 200, size=37 bytes`
- **Explanation:** .env environment file is publicly accessible
- **Fix:** Remove or restrict access to /.env. Ensure your web server does not serve sensitive files. Add these paths to your .gitignore and review deployment scripts.

#### [exposed-files] backup.zip exposed

- **URL:** `http://127.0.0.1:59205/backup.zip`
- **Evidence:** `HTTP 200, size=75 bytes`
- **Explanation:** Backup archive is publicly accessible
- **Fix:** Remove or restrict access to /backup.zip. Ensure your web server does not serve sensitive files. Add these paths to your .gitignore and review deployment scripts.

### 🟠 Medium (5)

#### [hdr-csp] Content-Security-Policy header missing

- **URL:** `http://127.0.0.1:59205/`
- **Evidence:** `Header not present`
- **Explanation:** Without a CSP, browsers cannot restrict which scripts, styles, or resources the page may load, making XSS attacks more impactful.
- **Fix:** Add a Content-Security-Policy header. Start with Content-Security-Policy: default-src 'self' and progressively tighten it.

#### [cookie-flags] Cookie 'session_id' missing HttpOnly flag

- **URL:** `http://127.0.0.1:59205/`
- **Evidence:** `Set-Cookie: session_id=... (HttpOnly absent)`
- **Explanation:** The cookie 'session_id' is accessible to JavaScript. If the site has an XSS vulnerability, an attacker can steal this cookie.
- **Fix:** Add the HttpOnly flag: Set-Cookie: name=value; HttpOnly; ...

#### [redirect-https] Site is served over plain HTTP

- **URL:** `http://127.0.0.1:59205`
- **Evidence:** `Target URL uses scheme: http`
- **Explanation:** The site is not using HTTPS. All traffic including credentials and session tokens is transmitted in plaintext and can be intercepted by anyone on the network path.
- **Fix:** Obtain a TLS certificate and configure the server to serve all content over HTTPS. Redirect all HTTP traffic to HTTPS.

#### [exposed-files] .DS_Store file exposed

- **URL:** `http://127.0.0.1:59205/.DS_Store`
- **Evidence:** `HTTP 200, size=8 bytes`
- **Explanation:** macOS .DS_Store file reveals directory structure
- **Fix:** Remove or restrict access to /.DS_Store. Ensure your web server does not serve sensitive files. Add these paths to your .gitignore and review deployment scripts.

#### [dir-listing] Directory listing is enabled

- **URL:** `http://127.0.0.1:59205/secret-dir/`
- **Evidence:** `Page body matches directory listing pattern: '<title>\\s*Index of\\s*/'`
- **Explanation:** The web server is configured to display a list of files in a directory when no index file is present. This can expose sensitive files, source code, backups, and internal structure to attackers.
- **Fix:** Disable directory listing in your web server configuration. Apache: Options -Indexes. nginx: autoindex off. IIS: Disable Directory Browsing in site settings.

### 🟡 Low (4)

#### [hdr-xfo] X-Frame-Options or CSP frame-ancestors missing

- **URL:** `http://127.0.0.1:59205/`
- **Evidence:** `X-Frame-Options: absent; CSP frame-ancestors: absent`
- **Explanation:** Without framing protection, this page can be embedded in an attacker-controlled iframe, enabling clickjacking attacks.
- **Fix:** Add X-Frame-Options: DENY (or SAMEORIGIN), or add frame-ancestors 'self' to your Content-Security-Policy.

#### [hdr-xcto] X-Content-Type-Options: nosniff missing

- **URL:** `http://127.0.0.1:59205/`
- **Evidence:** `Header not present`
- **Explanation:** Without nosniff, some browsers may MIME-sniff responses and execute content as a different type than declared (e.g., execute a JSONP endpoint as a script).
- **Fix:** Add: X-Content-Type-Options: nosniff

#### [tech-disclosure] Server header reveals version

- **URL:** `http://127.0.0.1:59205/`
- **Evidence:** `server: uvicorn, Apache/2.4.49`
- **Explanation:** The 'server' header reveals the software product and version (Apache/2.4.49). This helps attackers identify unpatched software and target known CVEs.
- **Fix:** Remove or redact the 'server' header. In Apache: ServerTokens Prod. In nginx: server_tokens off. In PHP: expose_php = Off.

#### [tech-disclosure] X-Powered-By header reveals version

- **URL:** `http://127.0.0.1:59205/`
- **Evidence:** `x-powered-by: PHP/7.4.3`
- **Explanation:** The 'x-powered-by' header reveals the software product and version (PHP/7.4.3). This helps attackers identify unpatched software and target known CVEs.
- **Fix:** Remove or redact the 'x-powered-by' header. In Apache: ServerTokens Prod. In nginx: server_tokens off. In PHP: expose_php = Off.

### ℹ️ Info (3)

#### [hdr-referrer] Referrer-Policy header missing

- **URL:** `http://127.0.0.1:59205/`
- **Evidence:** `Header not present`
- **Explanation:** Without Referrer-Policy, the browser's default behaviour may leak full URLs (including query parameters with sensitive data) to third-party sites via the Referer header.
- **Fix:** Add: Referrer-Policy: strict-origin-when-cross-origin

#### [hdr-permissions] Permissions-Policy header missing

- **URL:** `http://127.0.0.1:59205/`
- **Evidence:** `Header not present`
- **Explanation:** Without Permissions-Policy (formerly Feature-Policy), powerful browser features (camera, microphone, geolocation) may be accessible to embedded third-party iframes.
- **Fix:** Add a Permissions-Policy header to restrict which browser features this page and its embedded content may use.

#### [exposed-files] robots.txt hints

- **URL:** `http://127.0.0.1:59205/robots.txt`
- **Evidence:** `HTTP 200, size=32 bytes, body starts with 'User-agent: *\nDisallow: /admin/\n'`
- **Explanation:** robots.txt is present; review Disallow rules for sensitive paths
- **Fix:** Remove or restrict access to /robots.txt. Ensure your web server does not serve sensitive files. Add these paths to your .gitignore and review deployment scripts.

---
*Generated by SiteSentry 0.1.0*