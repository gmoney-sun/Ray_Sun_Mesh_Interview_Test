import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

# --- Config -----------------------------------------------------------------

MESH_CLIENT_ID = os.environ["MESH_CLIENT_ID"]
MESH_CLIENT_SECRET = os.environ["MESH_CLIENT_SECRET"]

# Sandbox host (per take-home requirement #3: "fully functional End to end
# using Sandbox"). Swap for https://integration-api.meshconnect.com in prod.
MESH_BASE_URL = os.environ.get(
    "MESH_BASE_URL", "https://sandbox-integration-api.meshconnect.com"
)

# Coinbase's catalog integrationId in Mesh. Setting this makes Link skip
# straight to the Coinbase login screen instead of showing the full catalog.
# Leave blank in .env if you'd rather let the user pick from the catalog.
COINBASE_INTEGRATION_ID = os.environ.get(
    "COINBASE_INTEGRATION_ID", "721a5035-029f-4e05-bf3c-009da2fe381b"
)

# Destination wallet + demo payment amount from the take-home spec.
DEST_WALLET_ADDRESS = os.environ.get(
    "DEST_WALLET_ADDRESS", "0x0Ff0000f0A0f0000F0F000000000ffFf00f0F0f0"
)
ETHEREUM_NETWORK_ID = "e3c7fdd8-b1fc-4e51-85ae-bb276e075611"  # Ethereum mainnet
PAYMENT_SYMBOL = "USDC"
PAYMENT_AMOUNT_USD = 50  # "$50 pair of shoes"
SAVED_TOKENS = {}


def mesh_headers():
    return {
        "Content-Type": "application/json",
        "X-Client-Id": MESH_CLIENT_ID,
        "X-Client-Secret": MESH_CLIENT_SECRET,
    }


# --- Routes ------------------------------------------------------------------


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/config")
def config():
    """Non-secret config the frontend needs (clientId is public, unlike the secret)."""
    return jsonify({"clientId": MESH_CLIENT_ID})


@app.post("/api/link-token")

def create_link_token():
    """
    Creates a Mesh linkToken pre-configured for:
      - connecting a Coinbase account
      - a $50 USDC transfer, over Ethereum, to the demo wallet address

    The frontend calls this, then hands the returned linkToken straight to
    the Web SDK's openLink().
    """
    body = request.get_json(silent=True) or {}
    user_id = body.get("userId", "shoe-shopper-demo-user")
    include_transfer = body.get("includeTransfer", True)  

    payload = {
        "userId": user_id,
        "restrictMultipleAccounts": True,
        "integrationId": COINBASE_INTEGRATION_ID,  # jump straight to Coinbase
    }

    if include_transfer:  
        payload["transferOptions"] = {
            "transactionId": f"shoes-{user_id}",
            "transferType": "payment",
            "isInclusiveFeeEnabled": False,
            "amountInFiat": PAYMENT_AMOUNT_USD,
            "toAddresses": [
                {
                    "networkId": ETHEREUM_NETWORK_ID,
                    "symbol": PAYMENT_SYMBOL,
                    "address": DEST_WALLET_ADDRESS,
                }
            ],
        }

    resp = requests.post(
        f"{MESH_BASE_URL}/api/v1/linktoken", headers=mesh_headers(), json=payload
    )

    if not resp.ok:
        return jsonify({"error": "Failed to create link token", "detail": resp.text}), resp.status_code

    return jsonify(resp.json())


@app.post("/api/holdings")
def get_holdings():
    """
    Reads the connected Coinbase portfolio using the accessToken (authToken)
    the frontend received in onIntegrationConnected.

    Body: { "authToken": "...", "type": "coinbase" }
    """
    body = request.get_json(silent=True) or {}
    auth_token = body.get("authToken")
    account_type = body.get("type", "coinbase")

    if not auth_token:
        return jsonify({"error": "authToken is required"}), 400

    payload = {"authToken": auth_token, "type": account_type,"includeMarketValue": True}

    holdings_resp = requests.post(
        f"{MESH_BASE_URL}/api/v1/holdings/get", headers=mesh_headers(), json=payload
    )
    value_resp = requests.post(
        f"{MESH_BASE_URL}/api/v1/holdings/value", headers=mesh_headers(), json=payload
    )

    return jsonify(
        {
            "holdings": holdings_resp.json() if holdings_resp.ok else {"error": holdings_resp.text},
            "value": value_resp.json() if value_resp.ok else {"error": value_resp.text},
        }
    )


@app.post("/api/save-token")
def save_token():
    """Frontend calls this right after onIntegrationConnected, so we can
    remember this user's tokenId for next time."""
    body = request.get_json(silent=True) or {}
    user_id = body.get("userId")
    token_id = body.get("tokenId")
    broker_type = body.get("brokerType")

    if not user_id or not token_id:
        return jsonify({"error": "userId and tokenId are required"}), 400

    SAVED_TOKENS[user_id] = {"tokenId": token_id, "brokerType": broker_type}
    return jsonify({"saved": True})


@app.get("/api/saved-token")
def get_saved_token():
    user_id = request.args.get("userId")
    saved = SAVED_TOKENS.get(user_id)
    return jsonify({"saved": saved})


if __name__ == "__main__":
    app.run(debug=True, port=5001)
