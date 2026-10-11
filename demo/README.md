# Demo data

`profile.demo.json` holds the **fictional** example of the sandbox ("Beispiel ansehen"). It describes no real person; the file says so itself in its `note` field.

- It uses the format of `apply_profile()` in `src/catalog.py`. `meta.currentSem` says in which semester the example person is "now"; the page derives the study start from it, relative to today's date, so the example never looks outdated.
- `build.py` validates the file and embeds it into every build, including the neutral one served in production. Unit tests check that all slots, statuses and modules exist in the catalog.

Never put real study data here. The build has no option for personal data (ADR-0004); this file is the only plan that is ever embedded. Personal files such as `profile.json` and `studienverlauf-*.json` are git-ignored and must never be committed.
