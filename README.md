# Sneaker Checkout — Mesh Take-Home Demo

A tiny full-stack app that satisfies the Mesh take-home requirements:

- Connects to **Coinbase** through Mesh Link (Sandbox)
- Pays for a **$50 pair of shoes** using **USDC** on the **Ethereum** network,
  sent to the test wallet address, via the **Link UI**
- Reads and displays the connected Coinbase **portfolio** using the
  `accessToken`
- Runs entirely against Mesh's **Sandbox** environment

**Stack:** Python (Flask) backend + a single static HTML/JS page using the
Mesh Web SDK (loaded via [esm.sh](https://esm.sh), no `npm install`/build step
needed for the frontend).

---

## 1. Get Mesh Sandbox credentials

1. Log into the **Mesh dashboard** → **Account → API keys → API keys**.
2. Create a new key with **Read & Write** permissions (required for transfers).
   You'll get:
   - **Client ID** — shown next to the key
   - **API key (sandbox)** — starts with `sk_sandbox_...` → this is your
     `MESH_CLIENT_SECRET`
3. **Important:** while you're there, go to **Account → API keys → Access**
   and add the domain you'll run this app on — e.g. `localhost:5001` and
   `127.0.0.1:5001`. **The Mesh SDK refuses to load the Link UI on any
   domain not on this allowlist** — this is what causes the
   `frame-ancestors` CSP error / "refused to connect" screen if you skip it.

## 2. Project setup (in VS Code)

```bash
# from this folder
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# then open .env in VS Code and paste in your real MESH_CLIENT_ID / MESH_CLIENT_SECRET
```

Open the folder in VS Code, and just run:

```bash
python app.py
```

The app serves at **http://localhost:5001**. Open that URL in your browser.

> Tip in VS Code: use the built-in `.env` support with the Python extension,
> or just `pip install python-dotenv` (already in requirements.txt) — `app.py`
> loads `.env` automatically via `load_dotenv()`.

## 3. Demo flow (matches the panel script)

1. Click **"Pay with Coinbase"**. This calls `/api/link-token` on the Flask
   backend (server-side, using your Client Secret — never exposed to the
   browser), which requests a `linkToken` from Mesh pre-loaded with:
   - `integrationId` for Coinbase (jumps straight past the catalog)
   - a `transferOptions` block for **$50 of USDC over Ethereum** to the test
     wallet address from the spec
2. The Mesh **Link UI** opens in an overlay. Pick Coinbase (if the catalog
   shows) and log in with Mesh's pre-configured sandbox test account:

   | Exchange | Username | Password | OTP    |
   |----------|----------|----------|--------|
   | Coinbase | `Mesh`   | `Pass123`| `123456` |

3. If prompted again for a One-Time Passcode / MFA code (e.g. to confirm the
   transfer), use **`123456`** again, per the take-home spec.
4. Confirm the $50 USDC transfer in the Link UI.
5. `onIntegrationConnected` fires in the frontend → the app calls
   `/api/holdings` with the `accessToken` it just received, which the Flask
   backend uses server-side to call Mesh's `/api/v1/holdings/get` and
   `/api/v1/holdings/value` — the resulting Coinbase portfolio renders in
   the "Coinbase portfolio" card.
6. `onTransferFinished` fires once the transfer completes → the app shows a
   success state and the raw transfer payload (handy to point at during the
   demo to show it really is an end-to-end Sandbox transaction).

## 4. Where each requirement is implemented

| Requirement | Where |
|---|---|
| Sign up for Mesh dashboard | Manual step, done before coding |
| Build an app using Mesh | This whole repo |
| Fully functional end-to-end, Sandbox | `MESH_BASE_URL` in `app.py` points at `sandbox-integration-api.meshconnect.com` |
| Launch Link, connect Coinbase | `POST /api/link-token` + `static/index.html`'s `createLink()`/`openLink()` |
| Payment flow: $50 USDC → wallet, Ethereum, Link UI | `transferOptions` in `create_link_token()` in `app.py` |
| Read/display Coinbase portfolio via accessToken | `POST /api/holdings` in `app.py`, rendered in `index.html` |

## 5. Notes / things worth mentioning to the panel

- The Client Secret **never touches the browser** — both Mesh calls that
  need it (`/linktoken`, `/holdings/get`, `/holdings/value`) are proxied
  through the Flask backend. The frontend only ever sees the short-lived
  `linkToken` and the Coinbase `accessToken` it gets back from Link.
- `integrationId` is set to Coinbase's Mesh catalog ID so the demo jumps
  straight to Coinbase login instead of the full catalog — remove it from
  `.env` (or the payload in `app.py`) if you'd rather show the catalog.
- Bonus/creativity ideas if you want to extend it further: show a live
  webhook listener for transfer status instead of polling `onTransferFinished`,
  add multiple "products" at different price points, or support additional
  Sandbox institutions (Binance, Robinhood) as alternate payment methods.
# Project-Software
