import os
import requests
from playwright.sync_api import sync_playwright

WEBHOOK_URL = os.environ.get("CHAT_WEBHOOK_URL")
STATION_URL = "https://www.plugshare.com/location/345793" # Maryland Target EA Station ID

def scrape_and_notify():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(STATION_URL, wait_until="networkidle")
        
        # Scrapes live outlet availability elements
        plugs = page.query_selector_all(".plug-status-item")
        
        status_list = []
        for index, plug in enumerate(plugs[:4]):
            text = plug.inner_text()
            if "Available" in text:
                status = "Available 🟢"
            elif "Occupied" in text or "In Use" in text:
                status = "In Use 🔵"
            else:
                status = "Offline 🔴"
            status_list.append({"id": f"Charger 0{index+1}", "status": status})
            
        browser.close()
        
        # Fallback formatting if station selectors change
        while len(status_list) < 4:
            status_list.append({"id": f"Charger 0{len(status_list)+1}", "status": "Unknown ⚪"})

        # Build Google Chat Card Payload
        payload = {
            "cardsV2": [{
                "cardId": "ea_target_auto_update",
                "card": {
                    "header": {
                        "title": "⚡ EA Charger Status (Automated)",
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

        # Post to Google Chat Webhook
        requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    scrape_and_notify()
  
