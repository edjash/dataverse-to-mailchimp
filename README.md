# Dataverse‑to‑Mailchimp

> **Boring‑robust contact sync from Microsoft Dataverse (Dynamics 365) to a Mailchimp audience.**

&#x20;&#x20;

---

## Overview

Dataverse‑to‑Mailchimp keeps your Microsoft Dataverse (Dynamics 365) contacts and your Mailchimp audience perfectly in step. Use it for quick back-fills, scheduled incremental syncs, or ad‑hoc dry‑runs. No heavyweight middleware or vendor lock‑in.

- **OAuth 2.0** against Azure AD / Entra ID for the Dataverse Web API.
- **API‑key auth** + regional detection for Mailchimp.
- **Service‑protection back‑off** (Dataverse 429/503) *and* **token bucket** (Mailchimp 10 req/s).
- **Dry‑run**, **limit**, and **full‑sync** switches for safe smoke‑tests.
- Halts on first **403 Forbidden** unless you pass `--allow-partial`.
- Single‑file packaging (`pyproject.toml`), zero lock‑in, **Python 3.11+**.
- One focused **pytest** suite proving the 403 logic ➜ >95 % coverage.
- JSON logs to `stdout`, perfect for Azure Automation or GitHub Actions.

---

## Install

```bash
# Clone + create an isolated env (you can use pyenv, direnv, etc.)
git clone https://github.com/edjash/dataverse‑to‑mailchimp.git
cd dataverse‑to‑mailchimp
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1

# Editable install with tooling extras
pip install -e .[dev]
```
---

## Configuration

The app reads credentials from *real* environment variables **or** a local `.env` file (loaded via [`python‑dotenv`](https://pypi.org/project/python-dotenv/)).

```ini
# Dataverse / Dynamics 365
DATAVERSE_TENANT_ID=aaaaaaaa‑bbbb‑cccc‑dddd‑eeeeeeeeeeee
DATAVERSE_CLIENT_ID=ffffffff‑1111‑2222‑3333‑444444444444
DATAVERSE_CLIENT_SECRET=SuperSecretFromEntra
DATAVERSE_RESOURCE=https://YOURORG.crm.dynamics.com

# Mailchimp
MAILCHIMP_API_KEY=abc123‑us5
MAILCHIMP_AUDIENCE_ID=0123456789
```
---

## Quick start

Initial import of all contacts using --full-sync

```bash
python -m dataverse_to_mailchimp --full-sync
```

Import contacts modified in the past 24 hours

```bash
python -m dataverse_to_mailchimp 
```

Import contacts modified since ISO8601 timestamp:

```bash
python -m dataverse_to_mailchimp --since 2025-07-10T12:00:00Z
```



### CLI reference

```text
usage: dataverse-to-mailchimp [options]

Sync Dataverse contacts to a Mailchimp audience.

Optional arguments:
  --help                show this help message and exit
  --since ISO8601       sync contacts modified after this UTC timestamp (default: 1 hour ago)
  --full-sync           ignore --since and fetch *all* contacts
  --limit N             stop after N contacts (for smoke-tests)
  --dry-run             no writes—log what *would* happen
  --allow-partial       continue after first 403/401 instead of aborting
```

---

## Development

```bash
# run unit tests + coverage
pytest -q --cov src/dataverse_to_mailchimp

# format + lint
ruff check .
ruff format .
```

CI passes on **Linux, macOS, and Windows** runners using Python 3.11.

---

## Roadmap

- Persistent “last successful sync” checkpoint (file, blob, or key‑value store).
- Delta links instead of modified‑since filter once Dataverse Change Tracking settles.
- Optional **one‑way** Mailchimp → Dataverse update for GDPR consent states.

PRs and issues welcome—please keep the ethos *“small, boring, robust.”*

---

## License

[MIT](LICENSE) © 2025 Edward Shortt

