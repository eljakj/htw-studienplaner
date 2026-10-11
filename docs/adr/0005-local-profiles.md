# ADR-0005: Several local profiles in one storage key

- Status: Accepted
- Date: 2026-10-11

## Context

Two people can share one browser profile, and one person may want to try a second plan (for example "what if I take another elective"). ADR-0002 rules out accounts, so the separation has to happen in the browser.

## Decision

- All plans of a browser live in the one key `studienverlauf-ai-v2`: `{v: 2, active, profiles: {p1: {...}, p2: {...}}}`. Only deviations from the catalog are stored.
- A bar above the plan switches between plans, adds one (at most 20), renames and deletes. Every change is saved at once, so switching never loses data.
- Each browser tab has its own active plan. `active` in the storage is only what a new tab opens.
- **Deleting** needs a confirmation inside the page (no `window.confirm`, which can be suppressed and cannot be tested well). The deleted record is kept in memory and can be restored with "Rückgängig" until the page is closed.
- Extra fields are written only when set: `subtitle` (own heading), `created` and `lastExport` (backup reminder after 30 days, see PRD A10).
- The old key `studienverlauf-ai-v1` is migrated once and never changed. An existing v2 key, even an unusable or empty one, blocks the migration, so deleting all plans cannot bring back an old plan.

## Consequences

Easier:

- No account and no server, yet two people (or two scenarios) do not mix.
- Export and import work per plan; the import can add a plan instead of replacing one.

Harder:

- All plans share the fate of the browser data: clearing it removes every plan. That is why the backup reminder exists, per plan.
- Several tabs writing the same key can overwrite each other; the last change wins and other tabs reload through the `storage` event.
- The storage limit of the browser applies to all plans together (small, since only deviations are stored).

## Alternatives considered

- **One key per profile:** needs an index key anyway and makes "all or nothing" writes impossible.
- **Undo for an import:** would need a second copy of the plan in memory for every import; the preview and the export before importing cover the risk.
