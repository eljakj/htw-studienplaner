# ADR-0002: Export and import instead of accounts or sync

- Status: Accepted
- Date: 2026-10-10

## Context

Each student keeps a personal plan: which modules are passed, planned or repeated, plus short notes. This is personal data. The project goals are: no account, no server-side storage, no tracking, and plans of different people never mix.

Browser storage can be lost (cleared browser data, private windows, a new device). Users therefore need a way to back up a plan and to move it to another device.

## Decision

- There are **no accounts, no server-side storage and no sync between devices**.
- Each browser keeps its own plan in `localStorage`. The server delivers the same neutral page to everyone.
- A plan is backed up and moved by **exporting one profile as a JSON file and importing it** on the other device.
- Import treats the file as untrusted input: it is validated with the same logic as loading, shown as a preview before it is applied, and values are only ever set as text, never as HTML.

This decision was made on 2026-10-10.

## Consequences

Easier:

- The server stores and processes no personal data. There is no backend to build, secure or operate.
- Plans of different people cannot mix, because each browser has its own storage.
- The whole system stays a static page, which keeps hosting and review simple.

Harder:

- There is no automatic sync. The user has to export and import by hand.
- If browser data is deleted without a recent export, the plan is lost. A backup reminder after 30 days without an export (PRD A10) reduces this risk.
- Two people who share one browser profile share one plan. Local profiles with a switcher (PRD A8, ADR-0005) are the answer for that case.
- Import needs careful validation, because the file can come from anywhere.

## Alternatives considered

- **Accounts with server-side storage:** would add login, a database, backups and privacy obligations. It contradicts the goals "no account" and "no server-side storage".
- **Sync through a third-party cloud service:** needs requests to other servers and gives away control of personal data. It contradicts the goal of making no external requests.
- **Read-only share link (PRD A11):** not a replacement for backup. It stays an idea for later and does not change this decision.
