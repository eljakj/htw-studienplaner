# ADR-0004: One neutral build for everyone, the own plan lives in the browser

- Status: Accepted
- Date: 2026-10-11

## Context

The first version could be built with a personal profile (`--profile file.json`): the start values of one student were baked into the page, and the result was deployed. That works for one person only. Every other visitor would see someone else's plan, and personal study data would end up in a build artifact, an image or a repository by accident.

Since ADR-0002 each browser keeps its own plan and moves it with an export file. The build therefore no longer needs any personal input.

## Decision

- `build.py` has **no option for personal data**. `--demo` and `--profile` were removed.
- The page always contains the catalog (every module "planned") and the fictional example plan (`demo/profile.demo.json`, shown as a sandbox that is never saved).
- The same file is used everywhere: the Docker image (production), GitHub Pages (public demo) and a local `dist/index.html`.
- CI compares the file inside the image byte for byte with a fresh build and fails if files like `profile.json` or `studienverlauf-*.json` are tracked.

## Consequences

Easier:

- There is nothing to configure per person, so there is nothing to leak. The privacy promise is checked by tests instead of by care.
- Production and demo cannot drift apart.

Harder:

- A new person starts with an empty plan and has to enter the study start or import an export file once.
- Anyone who wants preset values for a group (for example a course) cannot do it with the build; they hand out an export file instead.

## Alternatives considered

- **Keep `--profile` for the demo only:** a second way to build keeps a path alive through which personal values could reach a deployed page. The example plan covers the demo.
- **Separate demo page on GitHub Pages with other values:** two different pages need two checks; one page is simpler to trust.
