# ADR-0003: Content Security Policy with a script hash, generated at build time

- Status: Accepted
- Date: 2026-10-10

## Context

The app is one HTML file with an inline script and inline styles (ADR-0001). A Content Security Policy (CSP) limits what a page may run and load, so an injected script (for example through a bug in the import of a JSON file) cannot execute or send data away.

The simplest policy for inline code is `'unsafe-inline'`, but for scripts it switches the protection off. Two facts shape the decision:

- The page also runs on GitHub Pages (public demo), where we cannot set HTTP headers.
- The script text changes with every release, so a fixed hash in a config file would go stale.

## Decision

- `build.py` computes the SHA-256 hash of every executable inline `<script>` and writes a `<meta http-equiv="Content-Security-Policy">` tag into the page: `default-src 'none'; script-src 'sha256-...'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'`. Data blocks such as `<script type="application/json">` are not executed and need no hash.
- Scripts are therefore protected without `'unsafe-inline'`: only the exact script shipped in the page runs, and nothing is loaded or sent to other origins.
- Styles keep `'unsafe-inline'`, because the app sets `style` attributes (module colors) while rendering. The risk of injected CSS is much lower than that of injected scripts.
- nginx adds only what a `<meta>` tag cannot do: `Content-Security-Policy: frame-ancestors 'none'; ...`, plus `X-Content-Type-Options`, `Referrer-Policy` and `Permissions-Policy`. Browsers apply both policies together.
- E2E tests fail on any console error, which includes CSP violations, so a script change that breaks the policy is caught in CI.

## Consequences

Easier:

- The protection works the same on nginx, GitHub Pages and a local file.
- No hash to maintain by hand: every build is correct by construction.

Harder:

- No inline event handlers (`onclick="..."`), no `eval`, no `new Function`. Code must stay in the one script block.
- If a later feature needs a request to another origin (`connect-src`) or images (`img-src`), the policy in `build.py` must be widened on purpose and this ADR updated.

## Alternatives considered

- **`'unsafe-inline'` for scripts and styles:** simple, but gives no protection against injected scripts.
- **Nonce per request:** needs server-side generation for every response. Not possible on a static page and on GitHub Pages.
- **Full CSP only as nginx header with a generated hash file:** works only where we control the headers, and adds a second build output to keep in sync.
