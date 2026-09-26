<p align="center">
  <a href="README.fa.md">
    <img alt="فارسی" src="https://img.shields.io/badge/مستندات-فارسی-red?style=for-the-badge&labelColor=1f2937">
  </a>
  &nbsp;
  <a href="README.md">
    <img alt="English" src="https://img.shields.io/badge/Docs-English-blue?style=for-the-badge&labelColor=1f2937">
  </a>
</p>

# AVAL BOT — Telegram VPN Commerce Bot

A Persian-language Telegram bot for selling VPN subscriptions, with a
web admin panel included. Runs entirely on [Railway](https://railway.app)
— no server, no systemd, no Linux knowledge required.

**One process, one port** — the Telegram bot and the web panel share a
single event loop, so it fits inside Railway's free trial limits.

---

## What it does

- 💬 **Telegram bot** — users browse products, buy subscriptions, pay,
  and receive their VPN subscription link + QR code
- 🌐 **Web admin panel** — manage products, orders, users, and settings
  from a browser (`https://<your-domain>/admin`)
- 🔄 **Automatic backups** — database backup sent to your Telegram at a
  configurable interval (default every 12 hours)
- 💳 **Manual payment flow** — users send a receipt, admin approves, the
  subscription is delivered automatically
- 🗄️ **Panel-aware product linking** — products are attached to a
  preconfigured inbound in your 3x-ui panel; deletion/editing of a
  product never corrupts already-delivered orders (order snapshots)

---

## Requirements

| Item | How to get it |
|---|---|
| A [3x-ui panel](https://github.com/MHSanaei/3x-ui) running somewhere | with an inbound already configured |
| A Telegram bot token | talk to [@BotFather](https://t.me/BotFather) → `/newbot` |
| Your Telegram numeric ID | talk to [@userinfobot](https://t.me/userinfobot) |
| A Railway account | free at [railway.app](https://railway.app) |

> **Note:** This Railway edition talks to your 3x-ui panel over its API.
> The panel itself must be reachable from the public internet (a VPS or
> any host). Railway only hosts *this bot*, not the VPN panel.

---

## Deploy (5 steps)

### 1) Deploy this repository

In the Railway dashboard: **New Project → Deploy from GitHub repo** →
search for `AVAL_Bot_Railway` (this repo is public, you can also fork it
first). Railway detects the `Dockerfile` and builds automatically.

Or with the Railway CLI:

```bash
railway up
```

### 2) Set environment variables

In the service's **Variables** tab (or `railway variables set ...`):

| Variable | Required | Meaning |
|---|---|---|
| `BOT_TOKEN` | ✅ | token from @BotFather |
| `ADMIN_IDS` | ✅ | your Telegram numeric ID (comma-separated for multiple) |
| `WEB_ADMIN_PASSWORD` | ✅ | password to log into the web panel |
| `CARD_NUMBER` | ✅ | card number shown to buyers for manual payment |
| `CARD_OWNER` | ✅ | card holder name |
| `BACKUP_INTERVAL_HOURS` | ⬜ | default `12` |

Everything else has a sensible default. See [`.env.example`](.env.example)
for the full list.

> **VPN panels are configured from the bot's admin panel**, not from
> variables — log into `/admin` after the first deploy and add your
> 3x-ui panel(s) there (base URL, username, password). You then attach
> each product to a panel inbound.

### 3) Create a persistent volume

**Settings → Volumes → Add Volume** → mount path: `/app/data`

Without this, every redeploy wipes your database (users, orders, settings).

### 4) Get a public domain

**Settings → Networking → Generate Domain**

Your panel will be at `https://<your-domain>/admin`.

### 5) Verify

The bot sends a "successfully installed" message to your `ADMIN_IDS`
with the panel address. Send `/start` to the bot to confirm it responds.

---

## Admin features

- **Products** — name, duration (days), volume (GB), price. Attach to a
  panel inbound; stock is never shown to buyers (unlimited by design).
- **Orders** — snapshot of duration/volume at purchase time, so editing
  a product later never affects already-delivered subscriptions.
- **Users** — wallet balance, free-test tracking, block/unblock.
- **Backups** — a database backup is zipped and sent to admin Telegram
  every `BACKUP_INTERVAL_HOURS` (only the last 48 are kept). The
  **Backups** tab in the web panel lists every backup on disk with
  **Download** and **Restore** buttons, plus an **Upload** box to restore
  a `.db` file you saved earlier — see below.
- **Runtime controls** — on Railway, start/stop/restart are handled by
  Railway itself. Saving a new token/password stores it; **redeploy**
  applies it.

## Backup and restore

Backups happen automatically and land in **two** places:

1. **Telegram** — a `.db` file is sent to `ADMIN_IDS` every
   `BACKUP_INTERVAL_HOURS` (default 12). You can also request one
   instantly from the bot's admin menu: **💾 بک‌آپ دیتابیس**.
2. **Persistent volume** — the same file is written to
   `/app/data/backups/` on the Railway volume, so it survives redeploy.

To restore after a problem:

- Open the web panel → **💾 بک‌آپ دیتابیس** tab
- Pick a backup and press **↩ بازیابی** (Restore), or
- Use **⬆ آپلود و بازیابی** (Upload) to restore a `.db` file you
  downloaded from Telegram earlier

Every restore first takes a safety copy of the current database
(`pre_restore_*.db`), so a bad restore can be undone. On Railway, apply
the restored database with a **redeploy**.

---

## Cost on the free trial

With the recommended settings the trial credit lasts **4–6 months**:

- **Settings → Resources**: `0.25 vCPU`, `256 MB` RAM
- `BACKUP_INTERVAL_HOURS=12`

Default (unreduced) resources cost roughly $10–15/month and exhaust the
$24 trial in under two months.

---

## Platform differences vs. the VPS edition

| Feature | VPS edition (systemd) | This Railway edition |
|---|---|---|
| Start/Stop/Restart from panel | ✅ | ❌ — Railway manages the process |
| Delete bot from panel | ✅ | ❌ |
| Apply token/password change | instant (restart) | requires redeploy |
| Telegram backups | ✅ | ✅ |
| Web admin panel | ✅ | ✅ |
| Persistent database | ✅ | ✅ (with the volume) |

The panel's "Bot & settings" section detects Railway and shows a clear
message instead of an error when an action is unsupported.

---

## Troubleshooting

**Bot doesn't reply but the panel loads:** the `BOT_TOKEN` is invalid or
revoked. Get a fresh one from @BotFather, set it in **Variables**, and
redeploy.

**Panel doesn't load but the bot replies:** Railway didn't detect the
port. The `Dockerfile` maps Railway's `PORT` to `WEB_PORT` automatically;
if you're prompted, enter `8090`.

**Database is empty after redeploy:** the volume is missing or not
mounted at `/app/data`. Repeat step 3.

**Build fails:** check **Deployments → View Logs**. The most common
cause is a typo in a variable, not the code.

---

## ⚠️ Security

- Never paste `BOT_TOKEN`, `XUI_PASSWORD`, or `WEB_ADMIN_PASSWORD` into
  chat, issues, or commit messages.
- If a credential leaks, **revoke it immediately** — @BotFather `/revoke`
  for the token, change the 3x-ui password, and set a new panel password.
- Use a long, random `WEB_ADMIN_PASSWORD`.

---

## Development

```bash
pip install -r requirements.txt
python -m pytest -q
```

The repository mirrors the VPS edition; container-specific behavior is
gated behind `IS_CONTAINER_PLATFORM` so the same `bot.py` works both
ways.

---

## License

Provided as-is for personal/commercial use. No warranty.

---

[مستندات فارسی](README.fa.md)
