[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/new/template/kirocrew?utm_medium=integration&utm_source=button&utm_campaign=kirocrew)

# KiroCrew on Railway

One-click Railway template for [KiroCrew](https://github.com/kirodotdev/KiroCrew) **v0.13.1** (Apache-2.0), the
persistent workspace from the Kiro team: a web dashboard and chat channels (Slack, Discord, Telegram) in front of
long-running Kiro coding-agent sessions, with crons, webhooks, memory and an app store.

It runs the official image `ghcr.io/kirodotdev/kirocrew:0.13.1`, pinned by digest
`sha256:080c81417fd67d03ca28fdd983cb309efbcea8ee618adaeeb75a2ed96bcf58d1`, plus a small wrapper:

- **Caddy** on Railway's `PORT` in front of the gateway, which itself listens on `127.0.0.1:5476` only.
  KiroCrew pins each dashboard token to the client IP; with the gateway behind the same-container proxy,
  every request arrives from one address and sign-in links work through Railway's edge.
- **`/login`**: protected by HTTP basic auth (user `admin`, password = the generated `KIROCREW_LOGIN_PASSWORD`).
  It mints a short-lived KiroCrew dashboard link with `kirocrew token` and redirects you into the dashboard.
  No token ever appears in the logs.
- **`/api/health`**: the health check Railway uses.
- **One volume** at `/home/kirocrew`: config, sessions, memory, the Kiro CLI login and agent workspaces.
- A start script that refuses to start without a strong login password, sizes KiroCrew's memory thresholds to
  the container, skips the 400+ MB browser-harness and embedding-model downloads, and exits non-zero if any
  process dies so Railway restarts the service.

## Variables

| Variable | Default | Notes |
|---|---|---|
| `KIROCREW_LOGIN_PASSWORD` | `${{secret(32)}}` | Password for `/login` (user `admin`). Generated; read it in the service's Variables tab. |
| `KIROCREW_LOGIN_USER` | `admin` | Basic-auth user name for `/login`. |
| `PORT` | `8080` | Port Caddy listens on; leave as is. |
| `KIROCREW_LOGIN_TTL` | `15m` (not set) | How long a minted dashboard link stays valid. |
| `KIRO_API_KEY` | not set | Optional: add it yourself to use a Kiro API key (Kiro Pro and higher) instead of signing in with `kiro-login` (Free plan works). |
| `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `DISCORD_BOT_TOKEN`, `TELEGRAM_BOT_TOKEN`, `KIROCREW_OWNER_ID` | not set | Optional chat channels: add them as service variables and redeploy. The upstream entrypoint moves them into `~/.kiro/crew/.env` (mode 600). |

## After deploying

1. Open `https://YOUR-DOMAIN/login`, sign in as `admin` with `KIROCREW_LOGIN_PASSWORD`; you land in the dashboard.
   Open `/login` again whenever you need a fresh link.
2. Sign the agent in to Kiro once: `railway ssh` into the service and run `kiro-login`
   (device flow: open the printed URL, enter the code). A free Kiro account works. The login is kept on the volume.
   Or set `KIRO_API_KEY` (Kiro Pro) and redeploy.
3. Optional: add chat-channel tokens as variables and redeploy. The dashboard shows settings read-only when you
   reach it through a proxy (KiroCrew's design), so change settings with `railway ssh` and `crew config set ...`.

`crew <command>` runs any `kirocrew` CLI command as the app user, e.g. `crew token --ttl 2h` or `crew doctor`.

## Resources

KiroCrew's gateway idles at about 350–420 MB and is OOM-killed under 0.5 GB, so it needs **Railway Hobby or
higher, with about 1 GB of RAM** (measured on Railway: about 385 MB anonymous memory at idle, killed for lack of memory
about 30 s after boot at 0.5 GB; the start script logs a warning below about 900 MB) (more for many parallel agent sessions; each Kiro agent session adds a few hundred MB).
The inner agent sandbox needs Linux user namespaces, which Railway doesn't offer, so agent commands run
unsandboxed inside the container (KiroCrew's documented `KIROCREW_ALLOW_UNSANDBOXED=1` mode).

## Updates

Deployers get Railway's "update available" notice when this repo's `main` changes. Each update bumps the pinned
image in `Dockerfile` and adds an entry to [`CHANGELOG.md`](CHANGELOG.md) (breaking changes first). Your data
stays on the volume.
