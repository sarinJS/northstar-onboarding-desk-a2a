"""Check public Agent Card plus authenticated A2A 0.3 RPC on a deployed Render app.

Requires Python 3.10+. Uses standard library; no dependencies required.
"""
import json
import os
import sys
import urllib.request
import urllib.error
import uuid

base = os.environ.get("A2A_BASE_URL", "").rstrip("/")
token = os.environ.get("A2A_BEARER_TOKEN", "")
if not base.startswith("https://") or not token:
    sys.exit("Set A2A_BASE_URL=https://... and A2A_BEARER_TOKEN before running this test")

try:
    with urllib.request.urlopen(base + "/health", timeout=90) as reply:
        print("HEALTH:", json.load(reply))
    with urllib.request.urlopen(base + "/.well-known/agent-card.json", timeout=90) as reply:
        card = json.load(reply)
    print("AGENT:", card.get("name"))
    print("PROTOCOL:", card.get("protocolVersion"))
    assert card.get("protocolVersion") == "0.3.0"
    rpc_url = card["url"]
    assert rpc_url.startswith("https://")
    payload = {"jsonrpc": "2.0", "id": "verify-1", "method": "message/send", "params": {"message": {"kind": "message", "messageId": str(uuid.uuid4()), "role": "user", "parts": [{"kind": "text", "text": "Prepare an onboarding checklist for two proposed Java developers joining Project Orion. List six controls and what was actually executed."}]}}}
    request = urllib.request.Request(rpc_url, data=json.dumps(payload).encode(), headers={"Content-Type":"application/json", "Authorization":"Bearer "+token}, method="POST")
    with urllib.request.urlopen(request, timeout=90) as reply:
        result = json.load(reply)
    if "error" in result:
        sys.exit("A2A ERROR: " + str(result["error"]))
    task = result["result"]
    assert task.get("status", {}).get("state") == "completed", task
    answer = task["artifacts"][0]["parts"][0]["text"]
    for required in ("Hiring authorization", "Right-to-work verification", "Security training", "Access governance", "Device provisioning", "Manager sign-off", "No offer, hire"):
        assert required in answer, f"Missing {required}"
    print("ANSWER:\n" + answer)
    print("\nPASS: discovered and authenticated a real A2A 0.3 message/send interaction")
except (urllib.error.URLError, urllib.error.HTTPError, AssertionError, KeyError) as exc:
    sys.exit("FAIL: " + str(exc))
