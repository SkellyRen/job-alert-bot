# 📢 Job Alert Bot

**GitHub Actions-powered job scraper for tech roles with Discord alerts and duplicate tracking.**

This bot monitors a configurable list of job boards and posts matching opportunities to a Discord channel using a webhook. It runs on a schedule using GitHub Actions, filters jobs by keywords, and avoids duplicate alerts using a persistent hash list.

---

## 🚀 Features

- ✅ Scheduled scraping with [GitHub Actions](https://docs.github.com/en/actions)
- ✅ Customizable keyword filtering
- ✅ Discord integration via webhook
- ✅ Duplicate prevention with `seen_jobs.txt`
- ✅ Easy to extend via config

---

## 📁 File Structure

```
.
├── scraper.py          # Main scraping script
├── config.json         # List of job boards and keywords
├── seen_jobs.txt       # Hashes of already-posted jobs
└── .github/workflows
    └── jobcheck.ymal    # GitHub Actions schedule & bot runner
```

---

## ⚙️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-username/job-alert-bot.git
cd job-alert-bot
```

### 2. Add your Discord Webhook (securely)

- Go to **Settings > Secrets and variables > Actions > New repository secret**
- Name it `DISCORD_WEBHOOK`
- Paste your Discord webhook URL as the value

### 3. Customize Job Sources & Keywords

Edit [`config.json`](./config.json) to define the job boards and keywords you want to track.

### 4. Enable the GitHub Action

The bot will run automatically on your defined schedule (see `.github/workflows/jobcheck.yml`).

---

## 📅 Schedule

By default, the bot runs **four times daily**:
- 8:00 AM
- 12:00 PM
- 5:00 PM
- 8:00 PM (local time converted to UTC in cron)

---

## 🛡️ Responsible Scraping

This bot:
- Uses respectful scheduling (4x daily)
- Makes only one request per job board
- Avoids scraping private or login-protected data
- Minimizes load and avoids abuse

---

## 📄 License

MIT License — feel free to fork and adapt!
