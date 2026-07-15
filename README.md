# Mesh Project Complete Guide

## What is this project?

An **online shoe store** where users can pay $50 in cryptocurrency using a Coinbase account.

**In short: Connect Coinbase → See Your Assets → Pay → Assets Update**

---

## Part 1: Overall Flow 

### User's Perspective

```
Open the website
  ↓
Click "Connect Coinbase"
  ↓
A login popup appears
  ↓
Enter Coinbase username/password
  ↓
Popup closes automatically → see your crypto assets (BTC, ETH, USDC, etc.)
  ↓
Click "Proceed to Pay $50"
  ↓
Popup reopens — no login needed this time, straight to payment confirmation
  ↓
Confirm the $50 transfer
  ↓
Assets refresh automatically, showing the new balance
```

**Two clicks, two steps: connect first, then pay.** 

---

## Part 2: What Happens Behind the Scenes

### Architecture Diagram

```
Browser
    ↓
[Mesh Link UI]
    ↓
Our Flask Backend
    ↓
Mesh Company's Servers 
    ↓
Coinbase 
```

**Why do we need a backend?**
- Mesh needs a secret key to verify who we are
- This key can't be in the browser (too unsafe)
- Flask backend protects the key, keeps it on the server

**Important distinction:**
- Anything starting with `/api/...` (like `/api/holdings`) is **our own** Flask route
- Anything starting with `sandbox-integration-api.meshconnect.com` is **Mesh's real server**
- Our backend sits in between — the browser only ever talks to flask, and only flask talk to Mesh directly

---

## Part 3: Four Core Features

### Feature 1: Generate Login Ticket (Link Token)

### Feature 2: User Login (Step 1 — Connect)

### Feature 3: Payment (Step 2 — Pay)

### Feature 4: Display Your Assets

**Happens twice: right after connecting, and again right after paying**

**Note**: Each dollar amount comes directly from Mesh's User Account Endpoints
---

## Part 4: Mesh's APIs

### API 1: Get Login Ticket 
```
Calls Mesh's API — POST https://sandbox-integration-api.meshconnect.com/api/v1/linktoken — using the secret in the headers. Gets back a linkToken, hands it to the browser. Called twice per full checkout: once with no transferOptions (connect step), once with transferOptions attached (pay step).

Headers:
  Content-Type: application/json
  X-Client-Id: MESH_CLIENT_ID
  X-Client-Secret: MESH_CLIENT_SECRET

Body (connect step):
  {
    "userId": user_id,
    "restrictMultipleAccounts": true,
    "integrationId": COINBASE_INTEGRATION_ID
  }

Body (pay step — adds transferOptions):
  {
    "userId": user_id,
    "restrictMultipleAccounts": true,
    "integrationId": COINBASE_INTEGRATION_ID,
    "transferOptions": {
      "transactionId": f"shoes-{user_id}",
      "transferType": "payment",
      "isInclusiveFeeEnabled": false,
      "amountInFiat": PAYMENT_AMOUNT_USD,
      "toAddresses": [
        {
          "networkId": ETHEREUM_NETWORK_ID,
          "symbol": PAYMENT_SYMBOL,
          "address": DEST_WALLET_ADDRESS
        }
      ]
    }
  }
```
### API 2: Get Holdings 
```
Calls Mesh's API — POST https://sandbox-integration-api.meshconnect.com/api/v1/holdings/get — using the secret in the headers, plus the user's authToken. Gets back the list of crypto assets (cryptocurrencyPositions), including marketValue per asset since includeMarketValue: true is sent. Called three times: after connecting, after reusing the connection to pay, and after the transfer completes.

Headers:
  Content-Type: application/json
  X-Client-Id: MESH_CLIENT_ID
  X-Client-Secret: MESH_CLIENT_SECRET

Body:
  {
    "authToken": auth_token,
    "type": sandboxCoinbase,
    "includeMarketValue": true
  }
```
### API 3: Get Holdings Value
```
Calls Mesh's API — POST https://sandbox-integration-api.meshconnect.com/api/v1/holdings/value — same auth pattern as API 2. Gets back a pre-computed total crpto portfolio value using "cryptocurrenciesValue" field
Headers:
  Content-Type: application/json
  X-Client-Id: MESH_CLIENT_ID
  X-Client-Secret: MESH_CLIENT_SECRET

Body:
  {
    "authToken": auth_token,
    "type": account_type
  }
```
### 5 Backend Endpoints (local, not Mesh's)
```
GET  /api/config        → Give the browser our public clientId
POST /api/link-token     → Ask Mesh for a login ticket (connect OR pay)
POST /api/holdings       → Ask Mesh for assets + value
POST /api/save-token     → Remember this user's connection (our own storage)
GET  /api/saved-token    → Look up a remembered connection
```

## Part 5: Four Key Events (SDK Callbacks)

### Event 1: User Connected (`onIntegrationConnected`)
```
onIntegrationConnected: (payload) => {
  setStatus("Connected...")               // update status message
  loadPortfolio(accessToken, brokerType)  // fetch + render the portfolio table
  saveToken(payload)                      // remember connection for next click
  if (mode === "connect") closeLink()     // no payment this round, close it ourselves
}

variables captured:
payload.accessToken.brokerType
payload.accessToken.accountTokens?.[0]?.tokenId       // for returning user, skip re-verify next time
payload.accessToken.accountTokens?.[0]?.accessToken   // for checking user account balance
```
**Fires twice per full checkout** — once after connecting, once again after the pay step reuses the connection.

### Event 2: Payment Complete (`onTransferFinished`)
```
onTransferFinished: (transferData) => {
  showDebugJson(transferData)             // dump raw payload for demo/debugging
  if (transferData.status === "success") {
    setStatus("✅ Payment sent!")          // show success message
    loadPortfolio(...)                    // refresh portfolio with new balance
  } else {
    setStatus("Transfer ended: " + transferData.status)  // show failure message
  }
}

variables captured:
transferData.status
```
**Fires once**, only during the pay step.

### Event 3: Popup Closed (`onExit`)
```
onExit: (error) => {
  setButtonsDisabled(false)                        // re-enable Connect / Pay buttons
  if (error) {
    setStatus("Closed: " + error)                  // show error message, if any
  } else if (!sessionCompleted) {
    setStatus(reminder)                            // remind user to finish connecting or paying
  }
}
```
**Fires twice** — once after connecting, once after paying.

### Event 4: Event Log (`onEvent`)
```
onEvent: (ev) => {
  console.log("[Mesh event]", ev)         // log every internal screen change (debug only)
}

variables captured:
ev
```

### Frontend Key Code

```
javascript
meshLink.openLink(linkToken)              // Open the link session

onIntegrationConnected: (payload) => {
  loadPortfolio()                         // Connected, load assets
  saveToken(payload)                      // Remember for next click
  if (mode === "connect") closeLink()     // No payment this round, close it automatically
}

onTransferFinished: (data) => {
  if (data.status === "success") {
    loadPortfolio()                       // Paid, refresh assets
  }
}
```

## Part 6: Creativity & Bonus Features 

Beyond the core requirements (connect, pay, view portfolio), a few extra touches were added:

### 1. use Mesh's Supercharge return-users experience to allow customers connect first, see their porfolio and then make the payment without re-login again 

Mesh's "return user" token mechanism is normally described for a customer coming back *days later*. This app reuses the same mechanism **immediately**, inside one checkout

### 2. Real Market Values, Not Static Data

Asset values shown aren't hardcoded or manually calculated — `includeMarketValue: true`
is sent to Mesh's `/holdings/get` API, so each row shows Mesh's own live-computed
`marketValue` per asset, and the portfolio total comes from Mesh's own
`cryptocurrenciesValue`

### 3. "Continue Your Journey" Exit Reminders

If a user closes the popup before finishing — whether during login or before confirming
payment — the app shows a context-aware reminder instead of going silent:

- Exited before connecting → *"You'll need to connect your Coinbase account to continue…"*
- Exited before paying → *"Your $50 payment wasn't completed — click 'Proceed to Pay $50'…"*

This is tracked with a simple flag, set only when Mesh's own dedicated success signals
fire (`onIntegrationConnected` completing, or `transferData.status === "success"`) —
not guessed from generic UI events.

### 4. SDK Playground — a Debugging & Learning Tool

A separate page (`/sdk-playground.html`) exists purely to observe the raw SDK event
stream — every callback logs its **full, unfiltered payload**. Handy for debugging,
and for demonstrating a real understanding of what Mesh is sending under the hood.

### 5. Terminal-Only Credential Test Script

`test-paylink.sh` lets you verify Mesh API credentials and fetch a hosted PayLink
directly from the terminal — no Flask server, no browser required. Useful for quickly
sanity-checking sandbox credentials before touching any app code.

### Ideas not yet built, but natural next steps

- Swap `SAVED_TOKENS` (in-memory dict) for a real database, so return-user
  tokens survive a server restart
- Add a webhook listener as the authoritative source for transfer confirmation,
  per Mesh's own guidance — current callbacks are UI-only, by design
