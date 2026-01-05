# Aethor Discord Bot

A Python Discord bot for Minecraft MMORPG server, Aethor.

## Features
- Slash and prefix commands (`/ping`, `!ping`)
- Admin utilities (sync commands, reload cogs)
- Minecraft server status via `mcstatus`
 - Roles management (grant/revoke roles)
 - Whitelist management (add/remove/list Minecraft names)
 - Optional RCON integration to apply changes to the server
 - Onboarding: `/verify` links a Minecraft name, whitelists, and grants a role
 - Moderation: kick/ban/unban, timeout/untimeout, mute/unmute (role), purge, slowmode, lock/unlock, with logging

## Quick Start (Windows)
1. Install Poetry:
   https://python-poetry.org/docs/#installation
2. Install deps:
   ```powershell
   poetry install
   ```
3. Configure environment:
   - Run the bot once to generate `config.yaml`, then fill it out.
4. Smoke-check (no token needed):
   ```powershell
   poetry run python -m src.bot --check
   ```
5. Run bot:
   ```powershell
   poetry run python -m src.bot --sync
   ```

## Notes
- Prefix commands use `!`. Slash commands are under the bot's app commands.
- Use `--sync` on first run to publish slash commands.
 - Economy features are scaffolded as comments in `src/cogs/economy.py` and not active.

## Operations
- Install dependencies and optional voice support:
   ```powershell
   poetry install
   ```
- Validate setup without logging in:
   ```powershell
   poetry run python -m src.bot --check
   ```
- First run and slash sync:
   ```powershell
   poetry run python -m src.bot --sync
   ```
- Windows service (optional): use NSSM to run the bot in the background
   ```powershell
   nssm install AethorBot "C:\\Path\\to\\poetry.exe" "run" "python" "-m" "src.bot" "--sync"
   nssm set AethorBot AppDirectory "D:\\AethorBot"
   nssm start AethorBot
   ```
- Logging: Bot logs to stdout; capture via your service manager or redirect PowerShell output.
- Known warnings: Voice support warning appears if `PyNaCl` is not installed; it's safe to ignore.
   The extension loading has been updated to async to avoid the "load_extension was never awaited" warning.

## Healthcheck
- Enable via config: `healthcheck.enabled: true`.
- Port selection:
   - If `healthcheck.port` is set, the server binds to that port.
   - On Pterodactyl/Revivenode, the panel sets `PORT`; we auto-fallback to it if provided.
- Endpoints: `GET /`, `/health`, `/healthz`, `/ready`, `/live` → returns JSON with `{ ok, uptime_seconds, guilds, latency_ms, ready }`.

## File Logging
- Enable via config: `file_logs.enabled: true`.
- Defaults: writes rotating logs to `logs/aethor.log` (1MB, 5 backups).
- Customize with:
   - `file_logs.path`, `file_logs.max_bytes`, `file_logs.backup_count`.

## Revivenode Deployment
- Create a Discord Bot service (Python) in the Revivenode panel (Pterodactyl).
- Upload files via SFTP: `src/`, `data/`, `requirements.txt`, `.env.example`, `README.md`.
   - Data persistence: everything under `/home/container` persists; the bot uses `data/` for state.
   - Upload your filled `config.yaml` after the first run.
- Startup command (Startup tab):
   - `python -m src.bot --sync` (The first run will generate the `config.yaml` file. Fill it before running the bot again.)
   - After the first sync, you can use `python -m src.bot`.
- Install dependencies (if the egg supports Auto-Install): click Install. Otherwise run in Console:
   ```bash
   poetry install
   ```
- First run: Start the server. Watch the console for "Synced" and "Logged in as".
   - Health: The panel may expose the assigned port for checks; the health endpoint returns 200 JSON when the bot is up.
- RCON tips:
   - Ensure your Minecraft server `server.properties` has RCON enabled and the port open to the bot host.
   - Use the server's public IP for `rcon.host` and the RCON port/password from your config.
- Updates:
   - Upload changed files via SFTP, then restart. Use `/sync` to update slash commands when needed.

## RCON Integration
- Enable RCON in your `server.properties`:
   - `enable-rcon=true`
   - `rcon.port=25575` (default)
   - `rcon.password=your_password`
- Behavior:
   - When `rcon.enabled: true`, `whitelist_add`/`whitelist_remove` will also issue server commands via RCON.
   - Use `/whitelist_list_server` to read the current server whitelist via RCON.
   - Local list is stored in `data/whitelist.json`; treat it as your source of truth for bot features.

## Auto Sync (Nightly)
- Behavior:
   - Runs daily at the configured time and applies local list to server.
   - Respects `auto_sync.remove_extras` for removal.
   - Posts summary to `channels.log_channel_id` when set; reports skipped/error states.

## Backups
- When Backups Run:
   - After `/whitelist_import` completes.
   - After manual `/whitelist_sync` and `!wlsync` complete.
   - After nightly auto-sync completes.

## Diff Preview
- Commands:
   - `!wldiff` / `/whitelist_diff`
- Shows what would be added/removed compared to the server without applying changes.

## Commands
 - Moderation:
    - `/kick member:<@User> reason:<text?>`
    - `/ban member:<@User> delete_message_days:<int=0> reason:<text?>`
    - `/unban user_id:<id> reason:<text?>`
    - `/timeout member:<@User> minutes:<int> reason:<text?>`
    - `/untimeout member:<@User> reason:<text?>`
    - `/mute member:<@User> reason:<text?>` / `/unmute member:<@User> reason:<text?>`
    - `!purge <count>` / `/purge count:<int>`
    - `/slowmode seconds:<int> channel:<#channel?>`
    - `/lock channel:<#channel?>` / `/unlock channel:<#channel?>`
- Roles:
   - `!rolegrant @Role @User` / `/role_grant role:<Role> member:<User?>`
   - `!rolerevoke @Role @User` / `/role_revoke role:<Role> member:<User?>`
- Whitelist:
   - `!wladd <name>` / `/whitelist_add name:<str>`
   - `!wlremove <name>` / `/whitelist_remove name:<str>`
   - `!wllist` / `/whitelist_list`
   - `!wlsync [remove_extras]` / `/whitelist_sync remove_extras:<bool>`
   - When `LOG_CHANNEL_ID` is set, manual sync posts a summary to that channel.
   - Manual sync cooldown per user: `SYNC_COOLDOWN_SECONDS` (default 30s)
   - `/whitelist_import file:<attachment> apply_rcon:<bool>` — upload a CSV or TXT of IGNs (one per line or comma/CSV). Adds to local whitelist; when `apply_rcon=true` and RCON is enabled, also runs `whitelist add` for each name.
   - `/whitelist_export as_csv:<bool>` — download the current whitelist as JSON (default) or newline CSV.
 - Onboarding:
    - `/verify name:<str>` — links your Minecraft IGN (resolves UUID), adds to whitelist (and RCON if enabled), and grants `VERIFIED_ROLE_ID` if configured.
    - `/whois user:<@User?>` — shows a user's linked IGN/UUID.
    - `/unverify` — self-remove verification, role, and whitelist entry; uses RCON if enabled.
    - `/unverify_user user:<@User>` — admin-only: unverify another user, remove role and whitelist; uses RCON if enabled.
    - Safety: unverify commands refuse to run if the player appears online (checked via RCON `list`, or mcstatus query/status as fallback).
 - Status:
    - `!status` / `/status` — shows RCON state, next auto-sync time, local and server whitelist counts.
