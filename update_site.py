#!/usr/bin/env python3
"""
WorldPulse Bot — Fetches live weather + world news and generates a beautiful HTML dashboard.
Designed to be run daily via GitHub Actions for real, meaningful commits.
"""

import json
import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────
CITIES = [
    {"name": "Paris",    "lat": 48.8566,  "lon": 2.3522,   "flag": "🇫🇷"},
    {"name": "New York", "lat": 40.7128,  "lon": -74.0060, "flag": "🇺🇸"},
    {"name": "Tokyo",    "lat": 35.6762,  "lon": 139.6503, "flag": "🇯🇵"},
    {"name": "London",   "lat": 51.5074,  "lon": -0.1278,  "flag": "🇬🇧"},
    {"name": "Sydney",   "lat": -33.8688, "lon": 151.2093, "flag": "🇦🇺"},
]

# Free RSS feeds — no API key required
NEWS_FEEDS = [
    ("World",      "http://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Technology", "http://feeds.bbci.co.uk/news/technology/rss.xml"),
    ("Science",    "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml"),
]

OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}"
    "&current=temperature_2m,weathercode,windspeed_10m,relativehumidity_2m"
    "&timezone=auto"
)

WMO_CODES = {
    0:  ("Clear sky",        "☀️"),
    1:  ("Mainly clear",     "🌤️"),
    2:  ("Partly cloudy",    "⛅"),
    3:  ("Overcast",         "☁️"),
    45: ("Fog",              "🌫️"),
    48: ("Icy fog",          "🌫️"),
    51: ("Light drizzle",    "🌦️"),
    53: ("Drizzle",          "🌦️"),
    55: ("Dense drizzle",    "🌧️"),
    61: ("Light rain",       "🌧️"),
    63: ("Rain",             "🌧️"),
    65: ("Heavy rain",       "🌧️"),
    71: ("Light snow",       "❄️"),
    73: ("Snow",             "❄️"),
    75: ("Heavy snow",       "❄️"),
    80: ("Rain showers",     "🌦️"),
    81: ("Rain showers",     "🌦️"),
    82: ("Heavy showers",    "⛈️"),
    95: ("Thunderstorm",     "⛈️"),
    99: ("Thunderstorm+hail","⛈️"),
}

OUTPUT_FILE = Path("index.html")
DATA_FILE   = Path("data/worldpulse.json")


# ── Data Fetching ───────────────────────────────────────────────────────────────

def fetch_url(url: str, timeout: int = 10) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "WorldPulse-Bot/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_weather(city: dict) -> dict:
    url = OPEN_METEO_URL.format(lat=city["lat"], lon=city["lon"])
    raw = json.loads(fetch_url(url))
    cur = raw["current"]
    code = cur["weathercode"]
    desc, icon = WMO_CODES.get(code, ("Unknown", "🌡️"))
    return {
        "city":     city["name"],
        "flag":     city["flag"],
        "temp":     round(cur["temperature_2m"]),
        "wind":     round(cur["windspeed_10m"]),
        "humidity": cur["relativehumidity_2m"],
        "desc":     desc,
        "icon":     icon,
    }


def fetch_news(label: str, url: str, max_items: int = 6) -> list[dict]:
    raw = fetch_url(url).decode("utf-8", errors="replace")
    root = ET.fromstring(raw)
    ns = {"media": "http://search.yahoo.com/mrss/"}
    items = []
    for item in root.findall(".//item")[:max_items]:
        title = (item.findtext("title") or "").strip()
        link  = (item.findtext("link")  or "").strip()
        desc  = (item.findtext("description") or "").strip()
        # strip HTML tags from description
        import re
        desc = re.sub(r"<[^>]+>", "", desc)[:200]
        pub   = (item.findtext("pubDate") or "").strip()
        items.append({"title": title, "link": link, "desc": desc, "pub": pub})
    return items


# ── HTML Generation ─────────────────────────────────────────────────────────────

def weather_card(w: dict) -> str:
    return f"""
      <div class="weather-card">
        <div class="city-header">
          <span class="flag">{w['flag']}</span>
          <span class="city-name">{w['city']}</span>
        </div>
        <div class="weather-icon">{w['icon']}</div>
        <div class="temp">{w['temp']}°C</div>
        <div class="weather-desc">{w['desc']}</div>
        <div class="weather-meta">
          <span>💨 {w['wind']} km/h</span>
          <span>💧 {w['humidity']}%</span>
        </div>
      </div>"""


def news_section(label: str, items: list[dict]) -> str:
    cards = ""
    for i, n in enumerate(items):
        cards += f"""
        <a class="news-card" href="{n['link']}" target="_blank" rel="noopener">
          <div class="news-index">{str(i+1).zfill(2)}</div>
          <div class="news-content">
            <div class="news-title">{n['title']}</div>
            <div class="news-desc">{n['desc']}</div>
          </div>
        </a>"""
    return f"""
    <section class="news-section">
      <h2 class="section-title"><span class="section-label">{label}</span></h2>
      <div class="news-grid">{cards}
      </div>
    </section>"""


def render_html(weather_data: list[dict], news_data: list[tuple], now: datetime) -> str:
    weather_cards = "".join(weather_card(w) for w in weather_data)
    news_sections = "".join(news_section(label, items) for label, items in news_data)
    timestamp = now.strftime("%A %d %B %Y — %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>WorldPulse — Live Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=Outfit:wght@300;400;600&display=swap" rel="stylesheet"/>
  <style>
    :root {{
      --bg:        #07080d;
      --surface:   #0e1018;
      --border:    #1d2030;
      --accent:    #e8ff47;
      --accent2:   #47c8ff;
      --text:      #e4e6f0;
      --muted:     #5a5f7a;
      --card-bg:   #111420;
      --radius:    12px;
    }}

    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'Outfit', sans-serif;
      font-weight: 300;
      min-height: 100vh;
      overflow-x: hidden;
    }}

    /* Animated background grid */
    body::before {{
      content: '';
      position: fixed; inset: 0;
      background-image:
        linear-gradient(var(--border) 1px, transparent 1px),
        linear-gradient(90deg, var(--border) 1px, transparent 1px);
      background-size: 48px 48px;
      opacity: 0.4;
      pointer-events: none;
      z-index: 0;
    }}

    .container {{
      position: relative;
      z-index: 1;
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 24px 80px;
    }}

    /* ── Header ── */
    header {{
      padding: 56px 0 40px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 48px;
    }}

    .eyebrow {{
      font-family: 'DM Mono', monospace;
      font-size: 11px;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: var(--accent);
    }}

    h1 {{
      font-family: 'DM Serif Display', serif;
      font-size: clamp(2.5rem, 6vw, 4.5rem);
      line-height: 1;
      letter-spacing: -0.02em;
      color: #fff;
    }}

    h1 em {{
      font-style: italic;
      color: var(--accent);
    }}

    .subtitle {{
      font-size: 14px;
      color: var(--muted);
      margin-top: 4px;
    }}

    .timestamp-badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 100px;
      padding: 6px 16px;
      font-family: 'DM Mono', monospace;
      font-size: 11px;
      color: var(--muted);
      margin-top: 16px;
      width: fit-content;
    }}

    .live-dot {{
      width: 6px; height: 6px;
      background: var(--accent);
      border-radius: 50%;
      animation: pulse 2s infinite;
    }}

    @keyframes pulse {{
      0%, 100% {{ opacity: 1; transform: scale(1); }}
      50% {{ opacity: 0.4; transform: scale(0.8); }}
    }}

    /* ── Section titles ── */
    .section-title {{
      font-family: 'DM Serif Display', serif;
      font-size: 1.6rem;
      font-weight: 400;
      color: #fff;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .section-title::after {{
      content: '';
      flex: 1;
      height: 1px;
      background: var(--border);
    }}

    .section-label {{ white-space: nowrap; }}

    /* ── Weather ── */
    .weather-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 56px;
    }}

    .weather-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 20px 16px;
      transition: border-color 0.2s, transform 0.2s;
      cursor: default;
    }}

    .weather-card:hover {{
      border-color: var(--accent);
      transform: translateY(-2px);
    }}

    .city-header {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
    }}

    .flag {{ font-size: 1.4rem; }}

    .city-name {{
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 0.02em;
      color: var(--muted);
      text-transform: uppercase;
    }}

    .weather-icon {{
      font-size: 2.2rem;
      margin: 4px 0;
    }}

    .temp {{
      font-family: 'DM Serif Display', serif;
      font-size: 2.4rem;
      color: #fff;
      line-height: 1;
    }}

    .weather-desc {{
      font-size: 12px;
      color: var(--muted);
      margin: 4px 0 12px;
    }}

    .weather-meta {{
      display: flex;
      gap: 12px;
      font-family: 'DM Mono', monospace;
      font-size: 11px;
      color: var(--muted);
    }}

    /* ── News ── */
    .news-section {{ margin-bottom: 48px; }}

    .news-grid {{
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}

    .news-card {{
      display: grid;
      grid-template-columns: 48px 1fr;
      gap: 16px;
      align-items: start;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 16px 20px;
      text-decoration: none;
      color: inherit;
      transition: border-color 0.2s, background 0.2s;
    }}

    .news-card:hover {{
      border-color: var(--accent2);
      background: #131624;
    }}

    .news-index {{
      font-family: 'DM Mono', monospace;
      font-size: 11px;
      color: var(--accent);
      padding-top: 3px;
    }}

    .news-title {{
      font-size: 14px;
      font-weight: 600;
      color: var(--text);
      line-height: 1.4;
      margin-bottom: 4px;
    }}

    .news-desc {{
      font-size: 12px;
      color: var(--muted);
      line-height: 1.5;
    }}

    /* ── Footer ── */
    footer {{
      margin-top: 64px;
      padding-top: 24px;
      border-top: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-family: 'DM Mono', monospace;
      font-size: 11px;
      color: var(--muted);
    }}

    footer a {{ color: var(--accent2); text-decoration: none; }}

    /* Animate cards in */
    .weather-card, .news-card {{
      animation: fadeUp 0.4s ease both;
    }}

    @keyframes fadeUp {{
      from {{ opacity: 0; transform: translateY(12px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}

    @media (max-width: 640px) {{
      .weather-grid {{ grid-template-columns: repeat(2, 1fr); }}
      footer {{ flex-direction: column; gap: 8px; text-align: center; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="eyebrow">🌍 WorldPulse — Auto-generated dashboard</div>
      <h1>World <em>Weather</em><br>& Latest <em>News</em></h1>
      <p class="subtitle">Updated automatically every day via GitHub Actions.</p>
      <div class="timestamp-badge">
        <div class="live-dot"></div>
        {timestamp}
      </div>
    </header>

    <section style="margin-bottom: 56px;">
      <h2 class="section-title"><span class="section-label">🌡️ Weather Around the World</span></h2>
      <div class="weather-grid">
        {weather_cards}
      </div>
    </section>

    {news_sections}

    <footer>
      <span>WorldPulse Bot — Real data, real commits ✦ <a href="https://open-meteo.com" target="_blank">Open-Meteo</a> + <a href="https://bbc.com" target="_blank">BBC News</a></span>
      <span>Generated {timestamp}</span>
    </footer>
  </div>
</body>
</html>"""


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    now = datetime.now(timezone.utc)
    print(f"[WorldPulse] Running at {now.isoformat()}")

    # Fetch weather
    print("[WorldPulse] Fetching weather data...")
    weather_data = []
    for city in CITIES:
        try:
            w = fetch_weather(city)
            weather_data.append(w)
            print(f"  ✓ {city['name']}: {w['temp']}°C {w['icon']}")
        except Exception as e:
            print(f"  ✗ {city['name']}: {e}")

    # Fetch news
    print("[WorldPulse] Fetching news feeds...")
    news_data = []
    for label, url in NEWS_FEEDS:
        try:
            items = fetch_news(label, url)
            news_data.append((label, items))
            print(f"  ✓ {label}: {len(items)} articles")
        except Exception as e:
            print(f"  ✗ {label}: {e}")

    # Generate HTML
    print("[WorldPulse] Generating HTML...")
    html = render_html(weather_data, news_data, now)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"  ✓ Written to {OUTPUT_FILE}")

    # Save JSON snapshot
    DATA_FILE.parent.mkdir(exist_ok=True)
    snapshot = {
        "generated_at": now.isoformat(),
        "weather":       weather_data,
        "news":          {label: items for label, items in news_data},
    }
    DATA_FILE.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ Data snapshot saved to {DATA_FILE}")

    print("[WorldPulse] Done ✅")


if __name__ == "__main__":
    main()
