#!/usr/bin/env bash
#
# test-paylink.sh
#
# Standalone test: calls Mesh's /linktoken endpoint with generatePayLink=true,
# then opens the resulting hosted URL in your default browser.
#
# Why this works right now, even while your Allowed Link URLs are still
# propagating: a PayLink is a normal top-level page (not embedded in an
# iframe on your app), so the `frame-ancestors` CSP check never applies.
# This lets you demo the real Link + Coinbase + transfer flow immediately.
#
# Usage:
#   1. Fill in CLIENT_ID and CLIENT_SECRET below (or export them as env vars
#      before running).
#   2. chmod +x test-paylink.sh
#   3. ./test-paylink.sh
#

set -euo pipefail

CLIENT_ID="${MESH_CLIENT_ID:-YOUR_CLIENT_ID}"
CLIENT_SECRET="${MESH_CLIENT_SECRET:-YOUR_SANDBOX_API_KEY}"

if [[ "$CLIENT_ID" == "YOUR_CLIENT_ID" ]]; then
  echo "Edit this script (or export MESH_CLIENT_ID / MESH_CLIENT_SECRET) with your real Sandbox credentials first."
  exit 1
fi

echo "Requesting a Mesh PayLink (sandbox)..."

RESPONSE=$(curl -s --request POST \
  --url https://sandbox-integration-api.meshconnect.com/api/v1/linktoken \
  --header 'Content-Type: application/json' \
  --header "X-Client-Id: ${CLIENT_ID}" \
  --header "X-Client-Secret: ${CLIENT_SECRET}" \
  --data '{
    "userId": "terminal-test-user",
    "restrictMultipleAccounts": true,
    "integrationId": "47624467-e52e-4938-a41a-7926b6c27acf",
    "transferOptions": {
      "transferType": "deposit",
      "amountInFiat": 50,
      "generatePayLink": true,
      "toAddresses": [
        {
          "networkId": "e3c7fdd8-b1fc-4e51-85ae-bb276e075611",
          "symbol": "USDC",
          "address": "0x0Ff0000f0A0f0000F0F000000000ffFf00f0F0f0"
        }
      ]
    }
  }')

echo "Raw response:"
echo "$RESPONSE" | python3 -m json.tool

# Pull out the pay link URL (key name can vary — payLinkUrl / linkUrl — this
# tries a couple of common ones)
PAYLINK_URL=$(echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
content = data.get('content', data)
url = content.get('payLinkUrl') or content.get('linkUrl') or content.get('payUrl')
print(url or '')
")

if [[ -z "$PAYLINK_URL" ]]; then
  echo ""
  echo "Couldn't find a pay link URL field automatically — check the raw"
  echo "response above for the correct field name and open it manually."
  exit 1
fi

echo ""
echo "Opening: $PAYLINK_URL"
open "$PAYLINK_URL"   # macOS-specific; use xdg-open on Linux
