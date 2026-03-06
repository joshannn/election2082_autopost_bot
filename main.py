"""
main.py — Nepal Election 2082 Auto-Update Bot
Scrapes -> Generates Images -> Posts one photo at a time -> Sleeps 90 min -> Repeats

Features:
- One photo per constituency posted individually (no carousel)
- 60 second gap between each photo post
- Full cycle repeats every 90 minutes
- Skips posting if votes have not changed since last cycle
- Loads credentials from .env file
- Logs to both stdout and logs/bot.log
- Cleans up old PNG files (keeps last 3 cycles)
- Posts to Telegram as well if configured
"""

import time
import os
import logging
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[Main] Loaded credentials from .env file.")
except ImportError:
    print("[Main] python-dotenv not installed. Reading environment variables directly.")

from scraper_ekantipur import fetch_popular_candidates
from image_generator import generate_all_images, cleanup_old_images
from instagram_poster import InstagramPoster

INTERVAL_MINUTES  = 90      # full cycle repeats every 90 min
PHOTO_GAP_SECONDS = 60      # gap between individual photo posts
OUTPUT_DIR        = "output"
KEEP_CYCLES       = 3


# ══════════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════════

def setup_logging():
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/bot.log", encoding="utf-8"),
        ],
    )

log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# CREDENTIALS
# ══════════════════════════════════════════════════════════════════

def get_credentials() -> tuple[str, str, str | None]:
    ig_user  = os.environ.get("IG_USERNAME", "").strip()
    ig_pass  = os.environ.get("IG_PASSWORD", "").strip()
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip() or None

    if not ig_user or not ig_pass:
        print("=" * 55)
        print("  Nepal Election 2082 - Instagram Auto-Poster")
        print("=" * 55)
        print("  Tip: set IG_USERNAME and IG_PASSWORD in a .env")
        print("  file to skip this prompt on future runs.")
        print()
        if not ig_user:
            ig_user = input("Instagram username: ").strip()
        if not ig_pass:
            import getpass
            ig_pass = getpass.getpass("Instagram password: ")
        print()

    return ig_user, ig_pass, tg_token


# ══════════════════════════════════════════════════════════════════
# TELEGRAM
# ══════════════════════════════════════════════════════════════════

def post_photo_to_telegram(image_path: str, bot_token: str, caption: str) -> bool:
    try:
        import requests
    except ImportError:
        log.warning("[Telegram] 'requests' not installed. Skipping.")
        return False

    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not chat_id:
        log.warning("[Telegram] TELEGRAM_CHAT_ID not set. Skipping.")
        return False

    try:
        with open(image_path, "rb") as f:
            resp = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendPhoto",
                data={"chat_id": chat_id, "caption": caption},
                files={"photo": f},
                timeout=60,
            )
        if resp.ok:
            return True
        else:
            log.error(f"[Telegram] Failed: {resp.text}")
            return False
    except Exception as e:
        log.error(f"[Telegram] Error: {e}")
        return False


# ══════════════════════════════════════════════════════════════════
# VOTE DIFF
# ══════════════════════════════════════════════════════════════════

def _vote_snapshot(candidates: list[dict]) -> dict[str, int]:
    return {c["name"]: c.get("votes", 0) for c in candidates}


def _stale_constituencies(
    prev: dict[str, int],
    curr_candidates: list[dict],
) -> set[str]:
    from collections import defaultdict
    by_area: dict[str, list[dict]] = defaultdict(list)
    for c in curr_candidates:
        by_area[c["constituency"]].append(c)
    stale = set()
    for area, group in by_area.items():
        if all(prev.get(c["name"], 0) == c.get("votes", 0) for c in group):
            stale.add(area)
    return stale


# ══════════════════════════════════════════════════════════════════
# BUILD CAPTION FOR A SINGLE PHOTO
# ══════════════════════════════════════════════════════════════════

def _build_caption(constituency: str, candidates: list[dict], photo_num: int, total: int) -> str:
    now   = datetime.now().strftime("%d %b %Y, %I:%M %p")
    lines = [
        f"Nepal Election 2082 - Live Update",
        f"Constituency: {constituency}  [{photo_num}/{total}]",
        "",
    ]
    for i, c in enumerate(candidates[:3]):
        prefix = ">" if i == 0 else " "
        votes  = f"{c['votes']:,}" if c.get("votes", 0) > 0 else "Pending"
        lines.append(f"{prefix} {c['name']} ({c['party']}) - {votes} votes")

    lines.extend([
        "",
        f"Updated: {now}",
        "Source: ekantipur.com",
        "",
        "#NepalElection2082 #Nepal #Election2082 #NepaliPolitics",
    ])
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════
# MAIN UPDATE CYCLE
# ══════════════════════════════════════════════════════════════════

def run_update_cycle(
    poster: InstagramPoster,
    tg_token: str | None,
    prev_snapshot: dict[str, int],
) -> dict[str, int]:

    log.info("=" * 55)
    log.info(f"Starting update cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. Scrape
    try:
        candidates = fetch_popular_candidates()
    except Exception as e:
        log.error(f"Scraping failed: {e}")
        return prev_snapshot

    if not candidates:
        log.warning("No candidates returned. Skipping cycle.")
        return prev_snapshot

    log.info(f"Loaded {len(candidates)} candidates")

    # 2. Check for any vote changes
    curr_snapshot = _vote_snapshot(candidates)
    any_change    = not prev_snapshot or any(
        curr_snapshot.get(n, 0) != prev_snapshot.get(n, 0)
        for n in curr_snapshot
    )

    if not any_change:
        log.info("No vote changes since last cycle. Skipping post.")
        return prev_snapshot

    stale = _stale_constituencies(prev_snapshot, candidates)
    if stale:
        log.info(f"Stale (unchanged): {', '.join(sorted(stale))}")

    # 3. Generate images
    try:
        image_paths = generate_all_images(
            candidates,
            output_dir=OUTPUT_DIR,
            stale_constituencies=stale,
        )
    except Exception as e:
        log.error(f"Image generation failed: {e}")
        return prev_snapshot

    if not image_paths:
        log.warning("No images generated. Skipping.")
        return prev_snapshot

    log.info(f"Generated {len(image_paths)} images")

    # 4. Group images back to constituencies for captions
    from collections import defaultdict
    by_area: dict[str, list[dict]] = defaultdict(list)
    for c in candidates:
        by_area[c["constituency"]].append(c)
    for group in by_area.values():
        group.sort(key=lambda x: x.get("votes", 0), reverse=True)

    total = len(image_paths)

    # 5. Post each image individually with a gap
    posted  = 0
    failed  = 0

    for idx, image_path in enumerate(image_paths, start=1):
        # Derive constituency name from filename
        fname    = Path(image_path).stem          # e.g. Jhapa-5_20260306_1920
        area_key = "_".join(fname.split("_")[:-2]) # strip timestamp
        area_key = area_key.replace("_", " ")

        # Find matching constituency candidates for caption
        cands_for_area = by_area.get(area_key, [])
        caption = _build_caption(area_key, cands_for_area, idx, total)

        log.info(f"Posting {idx}/{total}: {area_key} ...")

        # Instagram
        ig_ok = False
        try:
            ig_ok = poster.post_image(image_path, caption)
        except Exception as e:
            log.error(f"Instagram post failed for {area_key}: {e}")

        if ig_ok:
            posted += 1
            log.info(f"  Instagram: posted")
        else:
            failed += 1
            log.error(f"  Instagram: FAILED")

        # Telegram (same image, same caption)
        if tg_token:
            tg_ok = post_photo_to_telegram(image_path, tg_token, caption)
            if tg_ok:
                log.info(f"  Telegram:  posted")
            else:
                log.error(f"  Telegram:  FAILED")

        # Gap between posts — skip after last one
        if idx < total:
            log.info(f"  Waiting {PHOTO_GAP_SECONDS}s before next post ...")
            time.sleep(PHOTO_GAP_SECONDS)

    log.info(f"Cycle complete: {posted} posted, {failed} failed out of {total}")

    # 6. Cleanup old PNGs
    cleanup_old_images(OUTPUT_DIR, keep_cycles=KEEP_CYCLES)

    return curr_snapshot


# ══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════

def main():
    setup_logging()
    ig_user, ig_pass, tg_token = get_credentials()

    poster = InstagramPoster(ig_user, ig_pass)
    if not poster.login():
        log.critical("Could not log in to Instagram. Exiting.")
        return

    if tg_token:
        log.info("Telegram token found — will post to Telegram too.")
    else:
        log.info("No TELEGRAM_BOT_TOKEN set — Telegram disabled.")

    log.info(f"Bot started.")
    log.info(f"  Posting: 1 photo per constituency, {PHOTO_GAP_SECONDS}s gap between each.")
    log.info(f"  Cycle repeats every {INTERVAL_MINUTES} minutes.")
    log.info(f"  Press Ctrl+C to stop.")

    prev_snapshot: dict[str, int] = {}

    while True:
        try:
            prev_snapshot = run_update_cycle(poster, tg_token, prev_snapshot)
        except KeyboardInterrupt:
            log.info("Stopped by user.")
            break
        except Exception as e:
            log.error(f"Unexpected error: {e}")
            log.info("Will retry next cycle ...")

        log.info(f"Sleeping {INTERVAL_MINUTES} min until next cycle ...")
        try:
            time.sleep(INTERVAL_MINUTES * 60)
        except KeyboardInterrupt:
            log.info("Stopped by user.")
            break


if __name__ == "__main__":
    main()