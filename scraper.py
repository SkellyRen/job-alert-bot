import json
import requests
from bs4 import BeautifulSoup
import hashlib
import os
import time

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

# Your actual Discord webhook
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
        if site.get("api_mode"):
            # API mode (Virtuous)
            res = requests.get(site["url"], headers=HEADERS, timeout=10)
            res.raise_for_status()
            data = res.json()
            jobs = data.get("jobBoard", {}).get("jobPostings", [])
            print(f"✅ Found {len(jobs)} job listings via API")

            for job in jobs:
                title = job.get("title", "")
                full_link = f"{site['base_url']}/jobs/{job.get('id', '')}"
                text = f"{title}"

                if not job_seen(full_link) and any(k in text.lower() for k in site["keywords"]):
                    send_to_discord(f"📢 **{title}**\n🔗 {full_link}")
                    mark_job_seen(full_link)
                    found_jobs += 1

        elif site["name"].startswith("Milestone Church"):
            # Special Milestone parsing
            res = requests.get(site["url"], headers=HEADERS, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            scripts = soup.find_all("script")
            jobs_data = []
            for script in scripts:
                if "var jobs = " in script.text:
                    js_text = script.text
                    start = js_text.find("var jobs = ") + len("var jobs = ")
                    end = js_text.find("];", start) + 1
                    jobs_json = js_text[start:end]
                    try:
                        jobs_data = json.loads(jobs_json)
                    except Exception as e:
                        print("❌ Error parsing Milestone job JSON:", e)
                    break

            listings = jobs_data
            print(f"✅ Found {len(listings)} job listings via embedded JSON")

            for job in listings:
                title = job["title"]
                full_link = site["base_url"] + job["url"]
                description = job.get("description", "")

                text = f"{title} {description}"
                if not job_seen(full_link) and any(k in text.lower() for k in site["keywords"]):
                    send_to_discord(f"📢 **{title}**\n🔗 {full_link}")
                    mark_job_seen(full_link)
                    found_jobs += 1

        else:
            # Normal HTML scraping
            res = requests.get(site["url"], headers=HEADERS, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            listings = soup.select(site["selector"])
            print(f"✅ Found {len(listings)} elements using selector: {site['selector']}")

            for job in listings:
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
