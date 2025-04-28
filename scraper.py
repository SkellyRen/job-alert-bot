import json
import re
import requests
from bs4 import BeautifulSoup
import hashlib
import os
import time

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
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
        time.sleep(1.2)  # Rate limit protection
    except Exception as e:
        print("❌ Failed to send to Discord:", e)

found_jobs = 0

for site in config:
    print(f"Checking {site['name']}...")
    try:
        res = requests.get(site["url"], headers=HEADERS, timeout=10)
        res.raise_for_status()

        # === Special Milestone Church Paycom handling ===
        if site["name"] == "Milestone Church (Paycom)":
            print("⚙️ Special parsing for Milestone Church...")
            match = re.search(r"var jobs\s*=\s*(\[.*?\]);", res.text, re.DOTALL)
            if match:
                jobs_json = json.loads(match.group(1))
                print(f"✅ Found {len(jobs_json)} jobs in Milestone JSON")

                for job in jobs_json:
                    title = job.get("title", "").strip()
                    relative_url = job.get("url", "")
                    full_link = "https://www.paycomonline.net" + relative_url

                    if not job_seen(full_link) and any(k in title.lower() for k in site["keywords"]):
                        send_to_discord(f"📢 **{title}**\n🔗 {full_link}")
                        mark_job_seen(full_link)
                        found_jobs += 1
            else:
                print("❌ Could not find Milestone jobs JSON block")
            continue

        # === Normal parsing ===
        soup = BeautifulSoup(res.text, "html.parser")
        listings = soup.select(site["selector"])
        print(f"✅ Found {len(listings)} elements using selector: {site['selector']}")

        for job in listings:
            if site["name"].startswith("ChurchStaffing"):
                title_elem = job.find("span", class_="searchResultTitle")
                if not title_elem:
                    continue
                text = " ".join(title_elem.get_text(strip=True).split())
                href = job.get("href", "")
                full_link = href if href.startswith("http") else site["base_url"] + href

            elif site["name"].startswith("Christian Tech Jobs"):
                text_raw = job.text.strip()
                text = " ".join(text_raw.split())
                link_elem = job.find_parent("a")
                href = link_elem.get("href", "") if link_elem else ""
                full_link = href if href.startswith("http") else site["base_url"] + href

            else:
                text_raw = job.text.strip()
                text = " ".join(text_raw.split())
                href = job.get("href", "")
                if not href:
                    link_elem = job.find("a") or job.find_parent("a")
                    href = link_elem.get("href", "") if link_elem else ""
                full_link = href if href.startswith("http") else site["base_url"] + href

            if not job_seen(full_link) and any(k in text.lower() for k in site["keywords"]):
                send_to_discord(f"📢 **{text}**\n🔗 {full_link}")
                mark_job_seen(full_link)
                found_jobs += 1

    except Exception as e:
        print(f"❌ Error checking {site['name']}: {e}")

if found_jobs == 0:
    send_to_discord("✅ Job check completed. No new matching jobs found.")
