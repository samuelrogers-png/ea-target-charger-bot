import os
import requests

WEBHOOK_URL = os.environ.get("CHAT_WEBHOOK_URL")

# Cloudflare proxy relay URL
PROXY_URL = "https://summer-bush-6b1d.helpmeblizzard.workers.dev"

def parse_status(raw_val):
    """Maps raw EA API status strings to precise UI status representations."""
    if not raw_val:
        return "Unknown ⚪"
        
    s = str(raw_val).upper().strip()
    
    # Check for active charging/occupied states
    if any(k in s for k in ["OCCUPIED", "CHARGING", "IN_USE", "USE", "BUSY", "PLUGGED", "PREPARING", "CONNECTED"]):
        return "In Use 🔵"
    # Check for out-of-service states
    elif any(k in s for k in ["OUT", "OFFLINE", "DOWN", "FAULT", "UNAVAIL", "MAINTENANCE", "DISABLED"]):
        return "Offline 🔴"
    # Check for available/free states
    elif any(k in s for k in ["AVAIL", "AVAILABLE", "FREE", "READY", "IDLE", "OPEN"]):
        return "Available 🟢"
        
    return f"Status: {s}"

def fetch_and_notify():
    status_list = []
    
    try:
        response = requests.get(PROXY_URL, timeout=15)
        print(f"Proxy HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Support various EA JSON payload structures
            evses = []
            if isinstance(data, dict):
                evses = data.get("evses") or data.get("connectors") or data.get("data", {}).get("evses") or []
            elif isinstance(data, list):
                evses = data
                
            charger_index = 1
            for evse in evses:
                if charger_index > 4:
                    break
                
                # Check top-level or nested connector statuses
                status_raw = evse.get("status") or evse.get("evseStatus") or evse.get("connectorStatus") or ""
                if not status_raw and "connectors" in evse:
                    connectors = evse.get("connectors", [])
                    if isinstance(connectors, list) and len(connectors) > 0:
                        status_raw = connectors[0].get("status", "")

                status_list.append({
                    "id": f"Charger 0{charger_index}",
                    "status": parse_status(status_raw)
                })
                charger_index += 1

    except Exception as e:
        print(f"Fetch Error: {e}")

    # Padding to keep card formatting uniform
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
    
