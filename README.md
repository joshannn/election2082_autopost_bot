# Nepal Election 2082 — Auto-Poster Bot

An automated bot that scrapes live election results from **ekantipur.com**, generates stylized **1080×1080 Instagram images** for each constituency, and posts them to **Instagram** (and optionally **Telegram**) every 90 minutes.

---

## Features

- **Live scraping** — Fetches vote counts from `election.ekantipur.com` using Selenium
- **Image generation** — Creates clean, branded 1080×1080 PNG cards per constituency using Pillow
- **Instagram posting** — Posts one photo per constituency with a 60-second gap between each
- **Telegram support** — Optionally mirrors every post to a Telegram channel/group
- **Smart diffing** — Skips posting if no vote changes have occurred since the last cycle
- **Stale watermark** — Marks unchanged constituencies visually on the image
- **Auto-cleanup** — Keeps only the last 3 cycles of generated PNGs on disk
- **Session persistence** — Saves Instagram login session to avoid repeated logins
- **Cycle logging** — Logs all activity to both stdout and `logs/bot.log`

---

## Project Structure

```
.
├── main.py                  # Entry point — orchestrates the full cycle loop
├── scraper_ekantipur.py     # Candidate list + live vote scraper (Selenium)
├── image_generator.py       # Pillow-based image renderer
├── instagram_poster.py      # Instagram uploader via instagrapi
├── .env                     # Credentials (not committed)
├── output/                  # Generated PNG images (auto-managed)
└── logs/
    └── bot.log              # Persistent log file
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/nepal-election-bot.git
cd nepal-election-bot
```

### 2. Install dependencies

```bash
pip install pillow instagrapi selenium webdriver-manager requests python-dotenv
```

> **Font requirement:** The image generator uses **Poppins** (Google Fonts). Install it to `/usr/share/fonts/truetype/google-fonts/` on Linux, or it will fall back to Liberation Sans / Arial.

### 3. Configure credentials

Create a `.env` file in the project root:

```env
IG_USERNAME=your_instagram_username
IG_PASSWORD=your_instagram_password

# Optional — Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_channel_or_chat_id
```

> If `.env` is not present, the bot will prompt for credentials on startup.

---

## Usage

```bash
python main.py
```

The bot will:
1. Scrape live vote counts from ekantipur.com
2. Generate one PNG per constituency
3. Post each image to Instagram (60s gap between posts)
4. Mirror to Telegram if configured
5. Sleep 90 minutes, then repeat

Press `Ctrl+C` to stop gracefully.

---

## Image Design

Each generated image includes:

- **Red header banner** — "ELECTION RESULTS UPDATE"
- **Blue constituency bar** — Constituency name + timestamp
- **Candidate rows** — Name, party, vote count (top 3 per constituency)
- **Leader highlight** — Larger vote number for the leading candidate
- **Footer** — Follow prompt + `#NepalElection2082` hashtag
- **Stale watermark** — Shown if no votes changed since the last cycle

---

## Configuration

Key constants in `main.py`:

| Constant | Default | Description |
|---|---|---|
| `INTERVAL_MINUTES` | `90` | Minutes between full cycles |
| `PHOTO_GAP_SECONDS` | `60` | Seconds between individual Instagram posts |
| `OUTPUT_DIR` | `"output"` | Directory for generated PNGs |
| `KEEP_CYCLES` | `3` | Number of past cycles to keep on disk |

---

## Dependencies

| Package | Purpose |
|---|---|
| `pillow` | Image generation |
| `instagrapi` | Instagram API client |
| `selenium` | Browser automation for scraping |
| `webdriver-manager` | Auto-manages ChromeDriver |
| `requests` | Telegram HTTP API calls |
| `python-dotenv` | `.env` file loading |

---

## Notes

- Instagram limits carousel posts to **10 images**. Since this bot posts individually (one image per constituency), this limit does not apply.
- Selenium requires **Google Chrome** to be installed on the host machine.
- Instagram may trigger 2FA or challenge flows on first login. Handle these manually and the session file will be saved for future runs.
- This project is intended for **election reporting and public information purposes only**.

---

## License

MIT License — free to use, modify, and distribute.
