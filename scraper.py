import json
import requests
from bs4 import BeautifulSoup

with open("config.json", "r") as f:
    config = json.load(f)

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1365118003976601681/PJi6J7GBkbBwotBi_OkKT9UrChdylnfIsfWQ28hW0XMExbxT-Pmkt7a9dQk5RQXc2n8M"

def send_to_discord(message):
    print("Posting to Discord:", message)
    requests.post(DISCORD_WEBHOOK, json={"content": message})

for site in config:
    print(f"Checking {site['name']}...")
    try:
        res = requests.get(site["url"], timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        listings = soup.select(site["selector"])
        
        for job in listings:
            text = job.text.strip().lower()
            href = job.get("href", "")
            if any(keyword in text for keyword in site["keywords"]):
                full_link = href if href.startswith("http") else site["base_url"] + href
                send_to_discord(f"📢 **{text}**
🔗 {full_link}")
    except Exception as e:
        print(f"Error checking {site['name']}: {e}")
