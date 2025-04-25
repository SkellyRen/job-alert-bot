import json
import requests
from bs4 import BeautifulSoup
import hashlib
import os

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

# Your Discord webhook
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1365118003976601681/PJi6J7GBkbBwotBi_OkKT9UrChdylnfIsfWQ28hW0XMExbxT-Pmkt7a9dQk5RQXc2n8M"

SEEN_FILE = "seen_jobs.txt"
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; JobBot/1.0)'}

# Load seen job hashes
if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "r") as f:
        seen = set(f.read().splitlines())
else:
    seen = set()

def job_seen(url):
    job_id = hashlib.md5(url.encode()).hexdigest()
    return job_id in seen

def mark_job_seen(url):
    job_id = hashlib.md5(url.encode()).hexdigest()
    with open(SEEN_FILE, "a") as f:
        f.write(f"{job_id}\n")
    seen.add(job_id)

def send_to_discord(message):
    print("Posting to Discord:", message)
    requests.post(DISCORD_WEBHOOK, json={"content": message})

found_jobs = 0  # Track matches for fallback message

# Scrape and match
for site in config:
    print(f"Checking {site['name']}...")
    try:
        res = requests.get(site["url"], headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        listings = soup.select(site["selector"])
        print(f"Found {len(listings)} elements using selector: {site['selector']}")

        for job in listings:
            text = job.text.strip().lower()

            # Attempt to find a link associated with the job
            href = ""
            link_elem = job.find("a")
            if not link_elem:
                link_elem = job.find_next("a")
            if link_elem:
                href = link_elem.get("href", "")

            full_link = href if href.startswith("http") else site["base_url"] + href

            if not job_seen(full_link) and any(keyword in text for keyword in site["keywords"]):
                send_to_discord(f"📢 **{text}**\n🔗 {full_link}")
                mark_job_seen(full_link)
                found_jobs += 1

    except Exception as e:
        print(f"Error checking {site['name']}: {e}")

# Let user know script ran even if nothing matched
if found_jobs == 0:
    send_to_discord("✅ Job check completed. No new matching jobs found.")
