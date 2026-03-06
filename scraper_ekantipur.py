"""
scraper_ekantipur.py — Nepal Election 2082 Candidate Tracker
Uses hardcoded candidate list (verified) + scrapes live vote counts from ekantipur.
If scraping fails, candidates still appear with last known / zero votes.
"""

import re
import time
import json
import os
from datetime import datetime
from collections import defaultdict

# ══════════════════════════════════════════════════════════════════
# VERIFIED CANDIDATE LIST — Update this if candidates change
# ══════════════════════════════════════════════════════════════════

CANDIDATES = [
    # -- Jhapa-5 --
    {"name": "Balendra Shah",           "party": "Rastriya Swatantra Party",    "constituency": "Jhapa-5"},
    {"name": "KP Sharma Oli",           "party": "CPN-UML",                     "constituency": "Jhapa-5"},
    {"name": "Samir Tamang",            "party": "Shram Sanskriti Party",       "constituency": "Jhapa-5"},

    # -- Bhaktapur-2 --
    {"name": "Rajiv Khatri",            "party": "Rastriya Swatantra Party",    "constituency": "Bhaktapur-2"},
    {"name": "Mahesh Basnet",           "party": "CPN-UML",                     "constituency": "Bhaktapur-2"},
    {"name": "Kavir Rana",              "party": "Nepali Congress",             "constituency": "Bhaktapur-2"},

    # -- Chitwan-2 --
    {"name": "Rabi Lamichhane",         "party": "Rastriya Swatantra Party",    "constituency": "Chitwan-2"},
    {"name": "Meena Kumari Kharel",     "party": "Nepali Congress",             "constituency": "Chitwan-2"},
    {"name": "Ashim Ghimire",           "party": "CPN-UML",                     "constituency": "Chitwan-2"},

    # -- Rautahat-1 --
    {"name": "Rajesh Kumar Chaudhary",  "party": "Rastriya Swatantra Party",    "constituency": "Rautahat-1"},
    {"name": "Ajay Kumar Gupta",        "party": "CPN-UML",                     "constituency": "Rautahat-1"},
    {"name": "Anil Kumar Jha",          "party": "Nepali Congress",             "constituency": "Rautahat-1"},

    # -- Kathmandu-3 --
    {"name": "Raju Nath Pandey",        "party": "Rastriya Swatantra Party",    "constituency": "Kathmandu-3"},
    {"name": "Kulman Ghising",          "party": "Ujaylo Nepal Party",          "constituency": "Kathmandu-3"},
    {"name": "Ramesh Aryal",            "party": "Nepali Congress",             "constituency": "Kathmandu-3"},

    # -- Myagdi-1 --
    {"name": "Mahabir Pun",             "party": "Independent",                 "constituency": "Myagdi-1"},
    {"name": "Harikrishna Shrestha",    "party": "CPN-UML",                     "constituency": "Myagdi-1"},
    {"name": "Arjun Bahadur Thapa",     "party": "Nepali Communist Party",      "constituency": "Myagdi-1"},

    # -- Lalitpur-3 --
    {"name": "Tosima Karki",            "party": "Rastriya Swatantra Party",    "constituency": "Lalitpur-3"},
    {"name": "Jitendra Kumar Shrestha", "party": "Nepali Congress",             "constituency": "Lalitpur-3"},
    {"name": "Raj Kaji Maharjan",       "party": "Nepali Communist Party",      "constituency": "Lalitpur-3"},

    # -- Siraha-1 --
    {"name": "Bablu Gupta",             "party": "Rastriya Swatantra Party",    "constituency": "Siraha-1"},
    {"name": "Ram Sundar Chaudhary",    "party": "Nepali Congress",             "constituency": "Siraha-1"},
    {"name": "Ram Shankar Yadav",       "party": "CPN-UML",                     "constituency": "Siraha-1"},

    # -- Gulmi-1 --
    {"name": "Sagar Dhakal",            "party": "Rastriya Swatantra Party",    "constituency": "Gulmi-1"},
    {"name": "Pradip Kumar Gyawali",    "party": "CPN-UML",                     "constituency": "Gulmi-1"},
    {"name": "Chandrakant Bhandari",    "party": "Nepali Congress",             "constituency": "Gulmi-1"},

    # -- Gorkha-1 --
    {"name": "Ram Chandra Lamichhane",  "party": "CPN-UML",                     "constituency": "Gorkha-1"},
    {"name": "Prem Kumar Khatri",       "party": "Nepali Congress",             "constituency": "Gorkha-1"},
    {"name": "Hari Raj Adhikari",       "party": "Nepali Communist Party",      "constituency": "Gorkha-1"},

    # -- Tanahun-1 --
    {"name": "Swarnim Wagle",           "party": "Rastriya Swatantra Party",    "constituency": "Tanahun-1"},
    {"name": "Govind Bhattarai",        "party": "Nepali Congress",             "constituency": "Tanahun-1"},
    {"name": "Bhagwati Neupane",        "party": "CPN-UML",                     "constituency": "Tanahun-1"},

    # -- Nawalparasi West-1 --
    {"name": "Bikram Khanal",           "party": "Rastriya Swatantra Party",    "constituency": "Nawalparasi West-1"},
    {"name": "Binod Kumar Chaudhary",   "party": "Nepali Congress",             "constituency": "Nawalparasi West-1"},
    {"name": "Ram Prasad Pandey",       "party": "CPN-UML",                     "constituency": "Nawalparasi West-1"},

    # -- Jhapa-1 --
    {"name": "Nisha Dangi",             "party": "Rastriya Swatantra Party",    "constituency": "Jhapa-1"},
    {"name": "Kevalram Rai",            "party": "Shram Sanskriti Party",       "constituency": "Jhapa-1"},
    {"name": "Keshav Raj Pandey",       "party": "Nepali Congress",             "constituency": "Jhapa-1"},

    # -- Jhapa-2 --
    {"name": "Indira Rana Magar",       "party": "Rastriya Swatantra Party",    "constituency": "Jhapa-2"},
    {"name": "Dev Raj Ghimire",         "party": "CPN-UML",                     "constituency": "Jhapa-2"},
    {"name": "Keshav Kumar Bhandari",   "party": "Shram Sanskriti Party",       "constituency": "Jhapa-2"},

    # -- Sunsari-1 --
    {"name": "Goma Tamang",             "party": "Rastriya Swatantra Party",    "constituency": "Sunsari-1"},
    {"name": "Harka Raj Rai",           "party": "Shram Sanskriti Party",       "constituency": "Sunsari-1"},
    {"name": "Sujendra Tamang",         "party": "Nepali Congress",             "constituency": "Sunsari-1"},

    # -- Morang-6 --
    {"name": "Rubina Acharya",          "party": "Rastriya Swatantra Party",    "constituency": "Morang-6"},
    {"name": "Dr. Shekhar Koirala",     "party": "Nepali Congress",             "constituency": "Morang-6"},
    {"name": "Binod Prasad Dhakal",     "party": "CPN-UML",                     "constituency": "Morang-6"},

    # -- Sunsari-2 --
    {"name": "Lal Bikram Thapa",        "party": "Rastriya Swatantra Party",    "constituency": "Sunsari-2"},
    {"name": "Rajib Koirala",           "party": "Nepali Congress",             "constituency": "Sunsari-2"},
    {"name": "Ram Chandra Mehata",      "party": "Janata Samjbadi Party-Nepal", "constituency": "Sunsari-2"},

    # -- Khotang-1 --
    {"name": "Aren Rai",                "party": "Shram Sanskriti Party",       "constituency": "Khotang-1"},
    {"name": "Bir Kaji Rai",            "party": "Nepali Congress",             "constituency": "Khotang-1"},
    {"name": "Hari Roka",               "party": "Nepali Communist Party",      "constituency": "Khotang-1"},

    # -- Saptari-2 --
    {"name": "Ramji Yadav",             "party": "Rastriya Swatantra Party",    "constituency": "Saptari-2"},
    {"name": "Chandra Kant Raut",       "party": "Janamat Party",               "constituency": "Saptari-2"},
    {"name": "Umesh Kumar Yadav",       "party": "Janata Samjbadi Party-Nepal", "constituency": "Saptari-2"},

    # -- Sarlahi-4 --
    {"name": "Amaresh Kumar Singh",     "party": "Rastriya Swatantra Party",    "constituency": "Sarlahi-4"},
    {"name": "Gagan Kumar Thapa",       "party": "Nepali Congress",             "constituency": "Sarlahi-4"},
    {"name": "Amnish Kumar Yadav",      "party": "CPN-UML",                     "constituency": "Sarlahi-4"},

    # -- Saptari-3 --
    {"name": "Amar Kant Chaudhary",     "party": "Rastriya Swatantra Party",    "constituency": "Saptari-3"},
    {"name": "Upendra Yadav",           "party": "Janata Samjbadi Party-Nepal", "constituency": "Saptari-3"},
    {"name": "Dinesh Kumar Yadav",      "party": "Nepali Congress",             "constituency": "Saptari-3"},

    # -- Dhading-1 --
    {"name": "Aashika Tamang",          "party": "Rastriya Swatantra Party",    "constituency": "Dhading-1"},
    {"name": "Bhumi Prasad Tripathi",   "party": "CPN-UML",                     "constituency": "Dhading-1"},
    {"name": "Krishna Rijal",           "party": "Nepali Congress",             "constituency": "Dhading-1"},

    # -- Kailali-2 --
    {"name": "Surya Bahadur Thapa",     "party": "CPN-UML",                     "constituency": "Kailali-2"},
    {"name": "Vijay Bahadur Swar",      "party": "Nepali Congress",             "constituency": "Kailali-2"},
    {"name": "K.P. Khanal",             "party": "Rastriya Swatantra Party",    "constituency": "Kailali-2"},

    # -- Kanchanpur-1 --
    {"name": "Janak Singh Dhami",       "party": "Rastriya Swatantra Party",    "constituency": "Kanchanpur-1"},
    {"name": "Tara Lama Tamang",        "party": "CPN-UML",                     "constituency": "Kanchanpur-1"},
    {"name": "Bina Magar",              "party": "Nepali Communist Party",      "constituency": "Kanchanpur-1"},
]


# -- Party accent colors ---------------------------------------------
PARTY_ACCENT = {
    "Rastriya Swatantra Party":     "#F59E0B",
    "CPN-UML":                      "#DC2626",
    "Nepali Congress":              "#2563EB",
    "CPN (Maoist Centre)":          "#991B1B",
    "CPN (Maoist Center)":          "#991B1B",
    "Nepali Communist Party":       "#B91C1C",
    "Rastriya Prajatantra Party":   "#16A34A",
    "Janamat Party":                "#7C3AED",
    "Janata Samjbadi Party-Nepal":  "#E67E22",   # FIX: was "Samajbadi" (typo)
    "Ujaylo Nepal Party":           "#0EA5E9",
    "Shram Sanskriti Party":        "#8B5CF6",
    "Independent":                  "#6B7280",
}


def get_party_accent(party: str) -> str:
    for key, color in PARTY_ACCENT.items():
        if key.lower() in party.lower():
            return color
    return "#1a1a1a"


def clean_vote_count(raw) -> int:
    """Strip commas, newlines, spaces, non-numeric chars and return int."""
    if isinstance(raw, (int, float)):
        return int(raw)
    cleaned = re.sub(r"[^\d]", "", str(raw))
    return int(cleaned) if cleaned else 0


def _build_candidates_with_defaults() -> list[dict]:
    """Build full candidate list with default fields."""
    result = []
    for c in CANDIDATES:
        result.append({
            "name":         c["name"],
            "party":        c["party"],
            "constituency": c["constituency"],
            "votes":        0,
            "lead":         0,
            "status":       "pending",
            "accent":       get_party_accent(c["party"]),
        })
    return result


def _try_scrape_votes() -> dict[str, int] | None:
    """
    Try to scrape live vote counts from ekantipur.
    Returns a dict mapping candidate_name (lowercase) -> vote_count, or None on failure.
    """
    print("[Scraper] Attempting to scrape live vote counts ...")
    driver = None

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        opts.add_argument("--log-level=3")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)
        driver.implicitly_wait(5)

        vote_map = {}

        # Strategy 1: Scrape the main election page
        driver.get("https://election.ekantipur.com/?lng=eng")
        time.sleep(10)

        for i in range(5):
            driver.execute_script(f"window.scrollTo(0, {(i + 1) * 800});")
            time.sleep(2)

        # Try __NEXT_DATA__ JSON blob first (Next.js site)
        next_data = driver.execute_script(
            "const el = document.getElementById('__NEXT_DATA__'); "
            "return el ? el.textContent : null;"
        )
        if next_data:
            try:
                data = json.loads(next_data)
                _extract_votes_from_json(data, vote_map)
            except Exception:
                pass

        body_text = driver.execute_script("return document.body?.innerText || '';")
        _extract_votes_from_text(body_text, vote_map)

        # Strategy 2: Try known ekantipur election URL patterns.
        # The site uses numeric IDs or query params, not slug paths —
        # attempt a search-style URL per constituency as a best-effort probe.
        constituencies = list({c["constituency"] for c in CANDIDATES})
        for area in constituencies:
            slug = area.lower().replace(" ", "-")
            urls_to_try = [
                f"https://election.ekantipur.com/constituency/{slug}?lng=eng",
                f"https://election.ekantipur.com/result/{slug}?lng=eng",
            ]
            for url in urls_to_try:
                try:
                    driver.get(url)
                    time.sleep(3)
                    # If redirected away (404 page), skip
                    if "ekantipur.com" not in driver.current_url:
                        continue
                    page_text = driver.execute_script("return document.body?.innerText || '';")
                    _extract_votes_from_text(page_text, vote_map)
                    break
                except Exception:
                    continue

        driver.quit()

        if vote_map:
            print(f"[Scraper] Scraped votes for {len(vote_map)} candidates")
            return vote_map

    except ImportError:
        print("[Scraper] selenium/webdriver-manager not installed")
    except Exception as e:
        print(f"[Scraper] Scraping error: {e}")
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

    return None


def _extract_votes_from_json(obj, vote_map: dict, depth: int = 0):
    """Recursively search JSON for candidate names paired with vote counts."""
    if depth > 10:
        return

    known_names = {c["name"].lower() for c in CANDIDATES}

    if isinstance(obj, dict):
        name_val = (
            obj.get("candidate_name") or obj.get("candidateName")
            or obj.get("name") or ""
        )
        vote_val = (
            obj.get("votes") or obj.get("vote_count")
            or obj.get("voteCount") or obj.get("total_votes")
        )

        if name_val and vote_val:
            name_lower = name_val.strip().lower()
            for known in known_names:
                if known in name_lower or name_lower in known:
                    vote_map[known] = clean_vote_count(vote_val)
                    break

        for val in obj.values():
            _extract_votes_from_json(val, vote_map, depth + 1)

    elif isinstance(obj, list):
        for item in obj:
            _extract_votes_from_json(item, vote_map, depth + 1)


def _extract_votes_from_text(text: str, vote_map: dict):
    """
    Scan page text for known candidate names near vote numbers.
    Requires numbers to be >= 3 digits to avoid matching constituency
    numbers like the '5' in 'Jhapa-5'.
    """
    if not text:
        return

    lines = [l.strip() for l in text.split("\n") if l.strip()]

    for i, line in enumerate(lines):
        line_lower = line.lower()

        for c in CANDIDATES:
            name_lower = c["name"].lower()
            if name_lower not in line_lower:
                continue

            search_window = " ".join(lines[i: i + 4])
            # Require at least 3 digits to skip constituency numbers
            numbers = re.findall(r"[\d,]{3,}", search_window)

            for num_str in numbers:
                vote = clean_vote_count(num_str)
                if vote > 0:
                    existing = vote_map.get(name_lower, 0)
                    if vote > existing:
                        vote_map[name_lower] = vote
                    break


def _enrich_leads(candidates: list[dict]) -> list[dict]:
    """Calculate lead margins and status per constituency."""
    groups = defaultdict(list)
    for c in candidates:
        groups[c["constituency"]].append(c)

    for area, group in groups.items():
        group.sort(key=lambda x: x["votes"], reverse=True)
        if len(group) >= 2 and group[0]["votes"] > 0:
            group[0]["lead"] = group[0]["votes"] - group[1]["votes"]
            group[0]["status"] = "leading"
            for c in group[1:]:
                c["lead"] = 0
                c["status"] = "trailing"

    return candidates


def fetch_popular_candidates() -> list[dict]:
    """
    Main entry point.
    1. Start with verified candidate list
    2. Try to scrape live vote counts
    3. Merge votes into candidate list
    4. Calculate leads
    """
    candidates = _build_candidates_with_defaults()
    vote_map = _try_scrape_votes()

    if vote_map:
        for c in candidates:
            name_lower = c["name"].lower()
            if name_lower in vote_map:
                c["votes"] = vote_map[name_lower]
                c["status"] = "counted"

        counted = sum(1 for c in candidates if c["votes"] > 0)
        print(f"[Scraper] Merged votes for {counted}/{len(candidates)} candidates")
    else:
        print("[Scraper] Could not scrape live votes — candidates loaded with 0 votes")

    candidates = _enrich_leads(candidates)
    return candidates


def get_candidates_by_constituency() -> dict[str, list[dict]]:
    """Return candidates grouped by constituency, sorted by votes descending."""
    candidates = fetch_popular_candidates()
    groups = defaultdict(list)
    for c in candidates:
        groups[c["constituency"]].append(c)

    for group in groups.values():
        group.sort(key=lambda x: x["votes"], reverse=True)

    return dict(groups)


if __name__ == "__main__":
    groups = get_candidates_by_constituency()

    print(f"\n{'=' * 75}")
    print(f"  Nepal Election 2082 -- {len(groups)} Constituencies, "
          f"{sum(len(g) for g in groups.values())} Candidates")
    print(f"{'=' * 75}")

    for area, group in groups.items():
        print(f"\n  {area}")
        print(f"  {'-' * 65}")
        for c in group:
            status = "[LEAD]" if c["status"] == "leading" else "      "
            print(
                f"    {status} {c['name']:28} | {c['party']:30} | "
                f"{c['votes']:>8,} votes"
            )
