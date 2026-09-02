import os
import requests

WEBHOOK_URL = os.environ.get("CHAT_WEBHOOK_URL")
PROXY_URL = "https://summer-bush-6b1d.helpmeblizzard.workers.dev"

def fetch_and_notify():
    status_list = []
    debug_info = ""
    
    try:
        response = requests.get(PROXY_URL, timeout=15)
        print(f"Proxy HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Print top-level data structure for debugging
            if isinstance(data, dict):
                print(f"Top-level keys returned: {list(data.keys())}")
                evses = data.get("evses") or data.get("data", {}).get("evses") or data.get("connectors") or []
            elif isinstance(data, list):
                evses = data
            else:
                evses = []
                
            print(f"Found {len(evses)} EVSE entries.")
            
            charger_index = 1
            for evse in evses:
                if charger_index > 4:
                    break
                
                # Capture every possible raw status value
                raw_status = evse.get("status") or evse.get("evseStatus") or evse.get("operationalStatus") or "NO_STATUS_KEY"
                
                # Check nested connectors if top-level status isn't present
                if raw_status == "NO_STATUS_KEY" and "connectors" in evse:
                    connectors = evse.get("connectors", [])
                    if isinstance(connectors, list) and len(connectors) > 0:
                        raw_status = f"Connector[0]: {connectors[0].get('status', 'NONE')}"

                status_list.append({
                    "id": f"Charger 0{charger_index}",
                    "status": f"Raw API: {raw_status}"
                })
                charger_index += 1
                
            debug_info = f"Parsed {len(status_list)} chargers from raw payload."
        else:
            debug_info = f"Proxy returned status code {response.status_code}"

    except Exception as e:
        print(f"Error fetching proxy: {e}")
        debug_info = f"Error: {e}"

    if not status_list:
        status_list = [{"id": "Debug Info", "status": debug_info}]

    payload = {
        "cardsV2": [{
            "cardId": "ea_target_auto_update",
            "card": {
                "header": {
                    "title": "⚡ EA Charger Status (Raw Debug)",
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
    
