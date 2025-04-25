import json
import requests
from bs4 import BeautifulSoup
import hashlib
import os

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

# Discord webhook URL
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/your-webhook-url"  # ← Replace with your actual webhook

# File to store seen job hashes
SEEN_FILE = "seen_jobs.txt"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobBot/1.0)"}

# Load seen jobs
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
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": message})
    except Exception as e:
        print("❌ Failed to send message to Discord:", e)

found_jobs = 0  # Counter to track if any jobs matched

# Loop through all configured job boards
for site in config:
    print(f"Checking {site['name']}...")
    try:
        res = requests.get(site["url"], headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        listings = soup.select(site["selector"])
        print(f"✅ Found {len(listings)} elements using selector: {site['selector']}")

        for job in listings:
            text = job.text.strip().lower()

            # Special logic: if job is a <span> inside an <a> (ChristianTechJobs)
            if job.name == "span" and job.parent.name == "a":
                href = job.parent.get("href", "")
            else:
                href = job.get("href", "") if job.name == "a" else ""
                if not href:
                    # Try finding a nearby <a> if not in the same tag
                    link_elem = job.find("a") or job.find_parent("a")
                    href = link_elem.get("href", "") if link_elem else ""

            full_link = href if href.startswith("http") else site["base_url"] + href

            # Check if job is new and keyword matches
            if not job_seen(full_link) and any(k in text for k in site["keywords"]):
                send_to_discord(f"📢 **{text}**\n🔗 {full_link}")
                mark_job_seen(full_link)
                found_jobs += 1

    except Exception as e:
        print(f"❌ Error checking {site['name']}: {e}")

# Fallback message
if found_jobs == 0:
    send_to_discord("✅ Job check completed. No new matching jobs found.")
