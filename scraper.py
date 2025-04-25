import json
import requests
from bs4 import BeautifulSoup
import hashlib
import os

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

# Your actual Discord webhook
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/your-webhook-url"  # Replace this

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
        print("❌ Failed to send to Discord:", e)

found_jobs = 0

for site in config:
    print(f"Checking {site['name']}...")
    try:
        res = requests.get(site["url"], headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        listings = soup.select(site["selector"])
        print(f"✅ Found {len(listings)} elements using selector: {site['selector']}")

        for job in listings:
            # === ChurchStaffing special case ===
            if site["name"].startswith("ChurchStaffing"):
                title_elem = job.find("span", class_="searchResultTitle")
                if not title_elem:
                    continue
                text = " ".join(title_elem.get_text(strip=True).split())
                href = job.get("href", "")
                full_link = href if href.startswith("http") else site["base_url"] + href

            # === ChristianTechJobs special case ===
            elif site["name"].startswith("Christian Tech Jobs"):
                text_raw = job.text.strip()
                text = " ".join(text_raw.split())
                link_elem = job.find_parent("a")
                href = link_elem.get("href", "") if link_elem else ""
                full_link = href if href.startswith("http") else site["base_url"] + href

            # === General case (Rock RMS, etc.) ===
            else:
                text_raw = job.text.strip()
                text = " ".join(text_raw.split())
                href = job.get("href", "")
                if not href:
                    link_elem = job.find("a") or job.find_parent("a")
                    href = link_elem.get("href", "") if link_elem else ""
                full_link = href if href.startswith("http") else site["base_url"] + href

            # Keyword filtering
            if not job_seen(full_link) and any(k in text.lower() for k in site["keywords"]):
                send_to_discord(f"📢 **{text}**\n🔗 {full_link}")
                mark_job_seen(full_link)
                found_jobs += 1

    except Exception as e:
        print(f"❌ Error checking {site['name']}: {e}")

if found_jobs == 0:
    send_to_discord("✅ Job check completed. No new matching jobs found.")
