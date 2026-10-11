# Deployment with docker compose

The site runs on a Docker VM as one container (nginx with the static page). The image is built by GitHub Actions and pulled from GHCR.

```
Browser -> Cloudflare (TLS, access policy) -> Cloudflare Tunnel
        -> http://<VM address>:8085 (published port of the VM)
        -> container htw-studienplaner (nginx, port 8080 inside)
```

- TLS ends at Cloudflare. The VM has no certificates and no reverse proxy; the nginx container speaks plain HTTP.
- The tunnel route (hostname `studium.jadlab.org` -> `http://<VM address>:8085`) and the access policy are configured in the Cloudflare Zero Trust dashboard, **not** in this repository. No tunnel token or other secret is stored here; `.env` is git-ignored.
- The image is public, so the VM needs no login to pull it.
- Updates are manual for now (see "Update"). An automatic update could be added later.

## Requirements

- Docker with the compose plugin (`docker compose version`)
- `curl` (to download two files; Git is **not** needed on the VM)
- Port 8085 free on the VM (`ss -ltn | grep 8085` prints nothing). Otherwise set another `HOST_PORT` in `.env` and change the tunnel route to match.

## First deploy

The VM only needs two files from the repository: `compose.yaml` and `.env.example` (saved as `.env`). The folder can be chosen freely; `docker compose` only needs both files in the same folder. The example uses `~/htw-studienplaner/deploy`.

```bash
mkdir -p ~/htw-studienplaner/deploy
cd ~/htw-studienplaner/deploy
BASE=https://raw.githubusercontent.com/eljakj/htw-studienplaner/main/deploy
curl -fsSL -o compose.yaml "$BASE/compose.yaml"
curl -fsSL -o .env "$BASE/.env.example"     # adjust if needed, no secrets in it
ls -la                        # .env is a hidden file, plain "ls" does not show it
docker compose pull
docker compose up -d
docker compose ps             # STATUS must become "healthy"
curl -s http://127.0.0.1:8085/healthz     # prints: ok
```

Then open https://studium.jadlab.org (through the VPN or the private network).

## Update

Every merge to `main` publishes a new `latest` image after CI succeeded (see CONTRIBUTING.md, "Container image"). To make it live:

```bash
cd ~/htw-studienplaner/deploy
docker compose pull
docker compose up -d
```

Only if `deploy/compose.yaml` itself changed, download it again first (your `.env` stays untouched):

```bash
curl -fsSL -o compose.yaml https://raw.githubusercontent.com/eljakj/htw-studienplaner/main/deploy/compose.yaml
```

Which commit is live:

```bash
docker inspect -f '{{ index .Config.Labels "org.opencontainers.image.revision" }}' htw-studienplaner
```

## Roll back

Every build has a tag `sha-<7 characters of the commit>` (list: GitHub, Packages, `htw-studienplaner`). Put the old tag into `.env` and restart:

```bash
cd ~/htw-studienplaner/deploy
nano .env                     # IMAGE_TAG=sha-0123456
docker compose pull
docker compose up -d
```

To go back to the newest build set `IMAGE_TAG=latest` again and repeat the two compose commands.

## Logs

```bash
cd ~/htw-studienplaner/deploy
docker compose logs --tail 100
```

nginx writes no access log and only critical errors (no visitor addresses are stored). Docker keeps at most 3 files of 10 MB.

## Troubleshooting

- `docker compose ps` shows `unhealthy`: read the logs, then try `docker compose up -d --force-recreate`.
- "port is already allocated": another service uses port 8085. Change `HOST_PORT` in `.env` and the tunnel route.
- The page does not open but `curl http://127.0.0.1:8085/healthz` works: check the tunnel route and the access policy in Cloudflare.
