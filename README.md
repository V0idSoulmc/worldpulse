# 🌍 WorldPulse Bot

> A GitHub bot that fetches **live weather** and **world news** every day and commits a beautiful HTML dashboard to your repository — generating **real, meaningful contributions** on your profile.

![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-automated-2ea44f?logo=github-actions)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ What it does

Every day at **07:00 UTC**, a GitHub Action automatically:

1. 🌡️ Fetches **live weather** for 5 world cities (via [Open-Meteo](https://open-meteo.com) — **no API key needed**)
2. 📰 Fetches **latest news** in 3 categories (World, Tech, Science) via BBC RSS feeds
3. 🎨 Generates a beautiful **HTML dashboard** (`index.html`)
4. 💾 Saves a **JSON data snapshot** (`data/worldpulse.json`)
5. ✅ **Commits and pushes** — adding a real green square to your contribution graph

---

## 🚀 Quick Start (5 minutes)

### 1. Fork or create your repository

```bash
# Clone this project
git clone https://github.com/YOUR_USERNAME/worldpulse.git
cd worldpulse
```

### 2. Enable GitHub Pages (optional, to host the dashboard)

Go to your repo → **Settings** → **Pages** → Source: `main` branch, `/ (root)` → **Save**

Your dashboard will be live at `https://YOUR_USERNAME.github.io/worldpulse/`

### 3. Push to GitHub — the bot starts automatically!

```bash
git add .
git commit -m "🚀 Initial commit"
git push
```

The GitHub Action runs every day at 07:00 UTC. You can also trigger it manually:  
**Actions tab** → `WorldPulse Daily Update` → **Run workflow**

---

## 🔧 Customize

### Add or change cities

Edit `CITIES` in `update_site.py`:

```python
CITIES = [
    {"name": "Berlin",   "lat": 52.5200, "lon": 13.4050, "flag": "🇩🇪"},
    {"name": "Toronto",  "lat": 43.6532, "lon": -79.3832,"flag": "🇨🇦"},
    # Add as many as you want!
]
```

### Change the update schedule

Edit `.github/workflows/daily-update.yml`:

```yaml
schedule:
  - cron: "0 7 * * *"   # 07:00 UTC daily
  # - cron: "0 */6 * * *"  # Every 6 hours (4 commits/day!)
  # - cron: "0 7 * * 1-5"  # Weekdays only
```

### Add more news categories

```python
NEWS_FEEDS = [
    ("World",      "http://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Technology", "http://feeds.bbci.co.uk/news/technology/rss.xml"),
    ("Science",    "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml"),
    ("Business",   "http://feeds.bbci.co.uk/news/business/rss.xml"),  # ← add this
]
```

---

## 🗂️ Project Structure

```
worldpulse/
├── .github/
│   └── workflows/
│       └── daily-update.yml    # GitHub Actions workflow
├── data/
│   └── worldpulse.json         # Latest data snapshot (auto-generated)
├── index.html                  # Dashboard (auto-generated)
├── update_site.py              # Main bot script
└── README.md
```

---

## 📡 Data Sources

| Data        | Source                                  | API Key? |
|-------------|------------------------------------------|----------|
| Weather     | [Open-Meteo](https://open-meteo.com)     | ❌ None  |
| News        | [BBC RSS Feeds](https://bbc.co.uk/news)  | ❌ None  |

**100% free. No sign-up. No limits.**

---

## 📜 License

MIT — fork it, customize it, make it yours.
