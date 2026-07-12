# Sneaker Checkout — Mesh Take-Home Demo

A checkout app that connects to **Coinbase** via Mesh Link (Sandbox), lets a
user pay **$50 in USDC on Ethereum**, and displays their portfolio.

**Stack:** Python (Flask) backend + a static HTML/JS frontend using the Mesh
Web SDK (loaded via [esm.sh](https://esm.sh), no build step needed).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then paste in your MESH_CLIENT_ID / MESH_CLIENT_SECRET
python app.py
```
Open **http://localhost:5001**.

**One-time dashboard step:** add `localhost:5001` and `127.0.0.1:5001` under
**Mesh Dashboard → Account → API keys → Access**, or Link will refuse to load.

## Demo flow

1. **Click "Connect Coinbase"** → log in with the sandbox test account:

   | Username | Password | OTP |
   |---|---|---|
   | `Mesh` | `Pass123` | `123456` |

   → Coinbase's portfolio loads on the page.

2. **Click "Proceed to Pay $50"** → skips straight past login (reusing the
   account just connected) and opens the transfer confirmation screen →
   confirm the $50 USDC transfer.

3. Portfolio refreshes automatically once the payment completes.

## How it works

- **Backend (`app.py`)** — the only place your Mesh Client Secret is used.
  Makes 3 server-side calls to Mesh: `/linktoken` (start a session),
  `/holdings/get` + `/holdings/value` (read the portfolio).
- **Frontend (`static/index.html`)** — loads the Mesh SDK, opens the Link
  overlay, and reacts to its callbacks (`onIntegrationConnected`,
  `onTransferFinished`, `onExit`).
- **Connect → Pay is two separate Link sessions**, not one: the first
  connects only (no transfer attached), so the portfolio is visible before
  checkout; the second reuses that connection's token to skip login and go
  straight to the transfer. This mirrors how Mesh's "return user" experience
  works, just triggered immediately instead of on a later visit.

## Addtional Notes

- Client Secret never reaches the browser — the frontend only ever sees a
  short-lived `linkToken` and the Coinbase `accessToken`/`tokenId`.
- Chose `renderType: "overlay"` for simplicity; Mesh recommends `embedded`
  for production web apps.
- `onTransferFinished`/`onEvent` are used for UI display only — Mesh's docs
  say webhooks are the authoritative source for backend business logic.
- Next steps to productionize: persist tokens in a real database (currently
  an in-memory dict that resets on server restart), add a webhook listener,
  replace the hardcoded demo user with real auth.

## Other files

- `static/sdk-playground.html` — minimal page for watching raw SDK events,
  useful for debugging.
- `test-paylink.sh` — terminal script to test Mesh credentials without
  running the app at all.
