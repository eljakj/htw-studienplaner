# ADR-0001: One static HTML file, vanilla JS, catalog maintained in Python

- Status: Accepted
- Date: 2026-10-10

## Context

The app plans the Bachelor programme "Angewandte Informatik (B)" at HTW Berlin. It has one view (34 course slots in six semesters), no user accounts and no server-side data. The plan of each user stays in the browser (see ADR-0002).

The module catalog (slots, elective modules, AWE and language courses) has to be checked against the LSF every semester. It needs validation, because an inconsistent catalog silently breaks the plan, for example credit points that no longer add up to 180.

The page should be easy to host, easy to read for reviewers, and must not make requests to other servers.

## Decision

- The app is delivered as **one self-contained file**, `dist/index.html`, produced by `build.py`.
- The UI is written in **vanilla JavaScript** with plain HTML and CSS. There is no framework, no bundler, no npm and no CDN.
- The catalog is the single source of truth in **`src/catalog.py`**. `validate()` checks it (unique IDs, 180 LP in total, 30 LP per semester, valid references). At build time `to_json()` embeds it into the page.
- Python 3 is used for the build and for tests. Browser behaviour is covered by Playwright E2E tests.

## Consequences

Easier:

- Hosting is a static file behind nginx; nothing else has to run.
- No frontend toolchain and no runtime dependencies; the build is deterministic.
- Catalog errors are caught by Python tests before they reach the page.
- No external requests, which keeps the privacy promise easy to verify.

Harder:

- DOM updates and state handling are written by hand.
- One file grows with the app and needs discipline to stay readable.
- Browser logic is tested through E2E tests, which are slower than unit tests.

## Alternatives considered

- **Framework (React, Vue, Svelte):** needs a bundler, npm dependencies and regular updates for one small view. The benefit does not justify the cost here.
- **Several static files (separate JS, CSS, JSON):** more files to deploy and cache, and a catalog file that nothing validates at build time.
- **Catalog as JSON or JavaScript only:** loses the validation in Python tests.
