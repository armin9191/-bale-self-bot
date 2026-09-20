# ⚔️ POSSIBLY

A PostgreSQL-backed Group Management + Fun + Games bot for Bale, restricted to `@possibly`.

## Verified library

This project targets `python-bale-bot==2.5.0`. The official documentation confirms `Bot.run()` is the synchronous entry point, message/callback events, inline keyboards, `ban_chat_member`, `unban_chat_member`, `get_chat_member`, `get_chat_administrators`, `Message.delete`, and document sending. See the official docs/changelog before extending the project.

## Important security note

The configuration file intentionally contains placeholders. Do **not** commit a live Bale token or a private Railway PostgreSQL URL to GitHub. A token previously pasted into chat should be rotated before using this repository.

For Railway, the PostgreSQL address must be reachable from the bot service. A hostname ending in `.railway.internal` is normally private to Railway's internal network and should not be used from a local Windows machine.

## Config

Edit `config.py`:

- `BOT_TOKEN`
- `DATABASE_URL` (use the Railway public/external connection string for local testing)
- `ALLOWED_GROUP_ID`
- `OWNER_ID`
- `POSSIBLY_ADMIN_ID`

No `.env` file is required by this project.

## Run locally

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## Railway

Set the same values in `config.py` if you deliberately want a code-only configuration. For a public GitHub repository, use Railway service variables instead and keep secrets out of Git.

The Worker command is:

```text
python main.py
```

`pg_dump` must be available in the Railway image if the `بکاپ` feature is used. If it is not available, the bot reports that backup creation failed.

## Current implemented features

- Single centralized message dispatcher (avoids competing `on_message` registrations)
- PostgreSQL pool and schema creation
- Allowed-group gate
- Owner / configured admin permission checks
- `/ban`, `/unban`, `/kick` using verified Bale chat methods
- Reply or numeric User ID targeting
- Learning system with 300-item limit
- Daily PostgreSQL statistics
- Echo command with message deletion attempt
- Private menu with inline keyboard
- Callback handling
- Tic-Tac-Toe engine and callback board
- PostgreSQL moderation log table
- PostgreSQL backup command for the configured admin

## API limitations / deliberately not faked

Some requested behavior depends on capabilities not represented by a single verified library method or requires additional privacy semantics. In particular:

- A true temporary kick is implemented as ban followed by immediate unban; there is no claim that this is an atomic timed-kick API. A scheduled five-second unban can be added with a task queue later.
- Whisper receiver-only visibility needs a carefully scoped private interaction. The project does not expose whisper content publicly as a fake implementation.
- Full animated GIF caption rendering is isolated but not enabled in the dispatcher until file-download/upload behavior and Railway resource limits are configured for the target deployment.
- Full persistent Mafia and Truth/Dare orchestration still belongs in the game-service layer; the Tic-Tac-Toe path is the first complete interactive game in this baseline.
- Bale's member-list API exposes administrators and member-count methods; the bot should not pretend it can enumerate every member when the installed API does not provide a general member-list method.

## GitHub

Never commit:

- live bot tokens
- private database passwords
- private Railway connection URLs
- generated backups
