import os
import requests

WEBHOOK_URL = os.environ.get("CHAT_WEBHOOK_URL")

# Clean Cloudflare relay URL
HARDCODED_PROXY = "https://summer-bush-6b1d.helpmeblizzard.workers.dev"

env_proxy = os.environ.get("PROXY_URL", "").strip()

# Guard against broken GitHub secrets containing markdown or brackets
if not env_proxy or "[" in env_proxy or "]" in env_proxy or "(" in env_proxy:
    PROXY_URL = HARDCODED_PROXY
else:
    PROXY_URL = env_proxy

def parse_status(raw_val):
    s = str(raw_val).upper()
    if "AVAIL" in s:
        return "Available 🟢"
    elif any(k in s for k in ["USE", "OCCUPIED", "CHARGING", "BUSY", "PLUGGED"]):
        return "In Use 🔵"
    elif any(k in s for k in ["OUT", "OFFLINE", "DOWN", "FAULT", "UNAVAIL"]):
        return "Offline 🔴"
    return "In Use 🔵"

def fetch_and_notify():
    status_list = []
    
    try:
        print(f"Querying proxy endpoint: {PROXY_URL}")
        response = requests.get(PROXY_URL, timeout=15)
        print(f"Proxy HTTP status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Raw API JSON Response: {str(data)[:300]}")  # Print snippet for debugging
            
            # Navigate nested payload variations
            evses = []
            if isinstance(data, dict):
                evses = data.get("evses") or data.get("data", {}).get("evses") or data.get("connectors") or []
            elif isinstance(data, list):
                evses = data
                
            charger_index = 1
            for item in evses:
                if charger_index > 4:
                    break
                
                # Check top-level or nested connector/EVSE status
                status_raw = item.get("status") or item.get("evseStatus") or item.get("connectorStatus") or ""
                if not status_raw and "connectors" in item:
                    connectors = item.get("connectors", [])
                    if connectors:
                        status_raw = connectors[0].get("status", "")
                        
                formatted_status = parse_status(status_raw)
                status_list.append({"id": f"Charger 0{charger_index}", "status": formatted_status})
                charger_index += 1
        else:
            print(f"Proxy returned non-200 status: {response.text[:200]}")
            
    except Exception as e:
        print(f"Exception during proxy call: {e}")

    # Fallback padding if data parsing yielded fewer than 4 items
    while len(status_list) < 4:
        status_list.append({"id": f"Charger 0{len(status_list)+1}", "status": "Unknown ⚪"})

    payload = {
        "cardsV2": [{
            "cardId": "ea_target_auto_update",
            "card": {
                "header": {
                    "title": "⚡ EA Charger Status (Live)",
                    "subtitle": "Target (4001 S Maryland Pkwy)"
                },
                "sections": [{
                    "widgets": [
                        {"decoratedText": {"topLabel": item["id"], "text": item["status"]}}
                        for item in status_list
                    ]
                }]
            }
        }]
    }

    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    fetch_and_notify()
    
