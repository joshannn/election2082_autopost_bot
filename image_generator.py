"""
image_generator.py — Generates 1080x1080 Instagram election update images.
Design: Instagram post mockup with red header banner, blue constituency bar,
white candidate cards with vote counts, and footer CTA.
Matches the reference design style.
"""

from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os

# ── Canvas ───────────────────────────────────────────────────────
WIDTH, HEIGHT = 1080, 1080

# ── Colors ───────────────────────────────────────────────────────
OUTER_BG       = "#EBEBEB"
CARD_BG        = "#FFFFFF"
RED_HEADER     = "#CC1F1F"
BLUE_BAR       = "#5B9BD5"
BLUE_BAR_TEXT  = "#FFFFFF"
CANDIDATE_BG   = "#FFFFFF"
CANDIDATE_BDR  = "#E8E8E8"
NAME_COLOR     = "#1A1A1A"
VOTE_LABEL_R   = "#CC1F1F"
VOTE_NUM_COLOR = "#1A1A1A"
VOTE_NUM_2ND   = "#CC1F1F"
RED_TICK       = "#CC1F1F"
GRAY_LABEL     = "#888888"
DIVIDER        = "#E0E0E0"
FOOTER_ICON_R  = "#CC1F1F"
LIVE_RED       = "#CC1F1F"
SHADOW_COLOR   = "#CCCCCC"
STALE_COLOR    = "#D1D5DB"
DIRECT_LABEL   = "#666666"
NEPAL_LABEL    = "#555555"

# ── Font paths ───────────────────────────────────────────────────
POPPINS_BOLD    = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
POPPINS_MEDIUM  = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
POPPINS_REGULAR = "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf"
POPPINS_LIGHT   = "/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf"
FALLBACK_BOLD    = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FALLBACK_REGULAR = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
WIN_BOLD        = "C:/Windows/Fonts/arialbd.ttf"
WIN_REGULAR     = "C:/Windows/Fonts/arial.ttf"


def _font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    mapping = {
        "bold":    [POPPINS_BOLD,    WIN_BOLD,    FALLBACK_BOLD],
        "medium":  [POPPINS_MEDIUM,  WIN_BOLD,    FALLBACK_BOLD],
        "regular": [POPPINS_REGULAR, WIN_REGULAR, FALLBACK_REGULAR],
        "light":   [POPPINS_LIGHT,   WIN_REGULAR, FALLBACK_REGULAR],
    }
    for path in mapping.get(weight, mapping["regular"]):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# Pre-load fonts
F_BANNER_TITLE  = _font(44, "bold")
F_NEPAL_LABEL   = _font(22, "medium")
F_BLUE_BAR_NAME = _font(26, "bold")
F_BLUE_BAR_TIME = _font(18, "regular")
F_DIRECT_LABEL  = _font(17, "regular")
F_CAND_NAME     = _font(26, "bold")
F_VOTE_LABEL    = _font(20, "bold")
F_VOTE_NUM_LG   = _font(38, "bold")
F_VOTE_NUM_MD   = _font(32, "bold")
F_FOOTER_MAIN   = _font(22, "bold")
F_FOOTER_LIVE   = _font(22, "bold")
F_FOOTER_HASH   = _font(18, "regular")
F_STALE         = _font(18, "bold")


# ── Helpers ──────────────────────────────────────────────────────

def _tw(draw, text, font) -> int:
    return draw.textbbox((0, 0), text, font=font)[2]

def _th(draw, text, font) -> int:
    b = draw.textbbox((0, 0), text, font=font)
    return b[3] - b[1]

def _truncate(draw, text: str, font, max_width: int) -> str:
    if _tw(draw, text, font) <= max_width:
        return text
    while text and _tw(draw, text + "...", font) > max_width:
        text = text[:-1]
    return text + "..."

def _shadow_rect(draw, xy, radius=18, shadow_offset=6):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(
        [x0 + shadow_offset, y0 + shadow_offset,
         x1 + shadow_offset, y1 + shadow_offset],
        radius=radius, fill=SHADOW_COLOR
    )
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=CARD_BG)

def _hline(draw, x0, x1, y, color=DIVIDER, width=1):
    draw.line([(x0, y), (x1, y)], fill=color, width=width)

def _megaphone(draw, cx, cy, size=1.0, color="#FFFFFF"):
    """Draw a simple megaphone icon."""
    s = size
    draw.polygon([
        (int(cx - 12*s), int(cy - 8*s)),
        (int(cx + 2*s),  int(cy - 8*s)),
        (int(cx + 14*s), int(cy - 18*s)),
        (int(cx + 14*s), int(cy + 18*s)),
        (int(cx + 2*s),  int(cy + 8*s)),
        (int(cx - 12*s), int(cy + 8*s)),
    ], fill=color)
    for off, r in [(6, 10), (13, 17)]:
        draw.arc(
            [int(cx + off*s), int(cy - r*s),
             int(cx + off*s + r*2*s), int(cy + r*s)],
            start=-60, end=60, fill=color, width=max(2, int(3*s))
        )


# ══════════════════════════════════════════════════════════════════
# MAIN GENERATOR
# ══════════════════════════════════════════════════════════════════

def generate_election_image(
    candidates: list[dict],
    constituency: str | None = None,
    output_path: str = "election_update.png",
    stale: bool = False,
) -> str:

    img  = Image.new("RGB", (WIDTH, HEIGHT), OUTER_BG)
    draw = ImageDraw.Draw(img)

    if not candidates:
        draw.text((100, HEIGHT // 2), "No data available",
                  fill=NAME_COLOR, font=F_BANNER_TITLE)
        img.save(output_path)
        return output_path

    leader    = candidates[0]
    contenders = candidates[1:3]
    area      = constituency or leader.get("constituency", "")
    now       = datetime.now().strftime("%I:%M %p")
    all_cands = [leader] + list(contenders)

    MARGIN = 48
    cx0, cy0, cx1, cy1 = MARGIN, MARGIN, WIDTH - MARGIN, HEIGHT - MARGIN
    pad = 22

    _shadow_rect(draw, [cx0, cy0, cx1, cy1], radius=20, shadow_offset=8)

    y = cy0

    # 1. Red banner header
    banner_h = 88
    draw.rounded_rectangle([cx0, y, cx1, y + banner_h], radius=20, fill=RED_HEADER)
    draw.rectangle([cx0, y + banner_h - 22, cx1, y + banner_h], fill=RED_HEADER)
    _megaphone(draw, cx0 + 42, y + banner_h // 2, size=1.1)

    title   = "ELECTION RESULTS UPDATE"
    title_w = _tw(draw, title, F_BANNER_TITLE)
    draw.text(
        ((WIDTH - title_w) // 2 + 10,
         y + (banner_h - _th(draw, title, F_BANNER_TITLE)) // 2),
        title, fill="#FFFFFF", font=F_BANNER_TITLE
    )
    y += banner_h

    # 2. Nepal 2082 subtitle
    sub   = "NEPAL  \u00b7  2082"
    sub_w = _tw(draw, sub, F_NEPAL_LABEL)
    sub_y = y + 16
    draw.text(((WIDTH - sub_w) // 2, sub_y), sub, fill=NEPAL_LABEL, font=F_NEPAL_LABEL)
    y = sub_y + _th(draw, sub, F_NEPAL_LABEL) + 16

    # 3. Blue constituency bar
    bx0, bx1 = cx0 + pad, cx1 - pad
    bar_h = 54
    draw.rounded_rectangle([bx0, y, bx1, y + bar_h], radius=8, fill=BLUE_BAR)

    area_label = _truncate(draw, area.upper(), F_BLUE_BAR_NAME, bx1 - bx0 - 230)
    draw.text((bx0 + 16, y + 13), area_label, fill=BLUE_BAR_TEXT, font=F_BLUE_BAR_NAME)

    upd_str = f"Updated: {now}"
    upd_w   = _tw(draw, upd_str, F_BLUE_BAR_TIME)
    draw.text((bx1 - upd_w - 16, y + 17), upd_str, fill=BLUE_BAR_TEXT, font=F_BLUE_BAR_TIME)
    y += bar_h + 10

    # 4. Direct election label
    draw.text((bx0 + 4, y), "DIRECT ELECTION-2082", fill=DIRECT_LABEL, font=F_DIRECT_LABEL)
    y += _th(draw, "DIRECT ELECTION-2082", F_DIRECT_LABEL) + 12

    # 5. Candidate rows
    row_h   = 90
    row_gap = 10
    rx0     = cx0 + pad
    rx1     = cx1 - pad
    rw      = rx1 - rx0
    rpad    = 20

    for i, c in enumerate(all_cands):
        ry      = y + i * (row_h + row_gap)
        c_votes = c.get("votes", 0)
        is_lead = (i == 0)

        draw.rounded_rectangle(
            [rx0, ry, rx1, ry + row_h],
            radius=10, fill=CANDIDATE_BG, outline=CANDIDATE_BDR, width=1
        )

        # Candidate name
        name_text = _truncate(draw, c["name"].upper(), F_CAND_NAME, rw - 200)
        draw.text((rx0 + rpad, ry + 13), name_text, fill=NAME_COLOR, font=F_CAND_NAME)

        # Vote count label in red
        vc_text = f"Vote Count : {c_votes:,}" if c_votes > 0 else "Vote Count : Pending"
        draw.text((rx0 + rpad, ry + 50), vc_text, fill=VOTE_LABEL_R, font=F_VOTE_LABEL)

        # Vote number right-aligned
        v_str  = f"{c_votes:,}" if c_votes > 0 else "-"
        v_font = F_VOTE_NUM_LG if is_lead else F_VOTE_NUM_MD
        v_col  = VOTE_NUM_COLOR if is_lead else VOTE_NUM_2ND
        vw     = _tw(draw, v_str, v_font)
        vx     = rx1 - rpad - vw
        vy     = ry + 16
        draw.text((vx, vy), v_str, fill=v_col, font=v_font)

        # Red underline tick under vote number
        if c_votes > 0:
            tick_w = min(vw, 30)
            tick_y = vy + _th(draw, v_str, v_font) + 4
            draw.rectangle(
                [rx1 - rpad - tick_w, tick_y, rx1 - rpad, tick_y + 5],
                fill=RED_TICK
            )

    y += len(all_cands) * (row_h + row_gap)

    # 6. Stale watermark
    if stale:
        wm   = "NO CHANGE SINCE LAST UPDATE"
        wm_w = _tw(draw, wm, F_STALE)
        draw.text(((WIDTH - wm_w) // 2, y + 8), wm, fill=STALE_COLOR, font=F_STALE)

    # 7. Footer
    footer_y = cy1 - 74
    _hline(draw, cx0 + pad, cx1 - pad, footer_y, DIVIDER)

    follow_x = cx0 + 62
    follow_y = footer_y + 12

    _megaphone(draw, cx0 + 36, follow_y + 14, size=0.9, color=FOOTER_ICON_R)

    f1  = "FOLLOW FOR "
    f1w = _tw(draw, f1, F_FOOTER_MAIN)
    draw.text((follow_x, follow_y), f1, fill=NAME_COLOR, font=F_FOOTER_MAIN)
    draw.text((follow_x + f1w, follow_y), "LIVE", fill=LIVE_RED, font=F_FOOTER_LIVE)
    live_w = _tw(draw, "LIVE", F_FOOTER_LIVE)
    draw.text((follow_x + f1w + live_w, follow_y), " ELECTION UPDATES!",
              fill=NAME_COLOR, font=F_FOOTER_MAIN)

    # Social icons (bookmark, comment, heart)
    icon_y = follow_y + 5
    icon_x = cx1 - 30
    gap    = 44

    bx = icon_x - 14
    draw.polygon([
        (bx, icon_y), (bx + 22, icon_y),
        (bx + 22, icon_y + 28), (bx + 11, icon_y + 20), (bx, icon_y + 28),
    ], outline=GRAY_LABEL, width=2)

    commx = bx - gap
    draw.ellipse([commx - 12, icon_y, commx + 12, icon_y + 22], outline=GRAY_LABEL, width=2)
    draw.polygon([
        (commx - 5, icon_y + 20), (commx - 11, icon_y + 30), (commx + 3, icon_y + 24)
    ], fill=GRAY_LABEL)

    hx = commx - gap
    hy = icon_y + 2
    draw.ellipse([hx - 11, hy, hx, hy + 12], fill=FOOTER_ICON_R)
    draw.ellipse([hx, hy, hx + 11, hy + 12], fill=FOOTER_ICON_R)
    draw.polygon([(hx - 11, hy + 8), (hx + 11, hy + 8), (hx, hy + 24)], fill=FOOTER_ICON_R)

    hash_text = "#NepalElection2082"
    hash_w    = _tw(draw, hash_text, F_FOOTER_HASH)
    draw.text(((WIDTH - hash_w) // 2, follow_y + 38), hash_text,
              fill=GRAY_LABEL, font=F_FOOTER_HASH)

    img.save(output_path, "PNG")
    print(f"[ImageGen] Saved -> {output_path}")
    return output_path


# ══════════════════════════════════════════════════════════════════
# BATCH GENERATOR
# ══════════════════════════════════════════════════════════════════

def generate_all_images(
    candidates: list[dict],
    output_dir: str = "output",
    stale_constituencies: set[str] | None = None,
) -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    stale_constituencies = stale_constituencies or set()

    groups: dict[str, list[dict]] = {}
    for c in candidates:
        key = c.get("constituency", "Unknown")
        groups.setdefault(key, []).append(c)

    ts    = datetime.now().strftime("%Y%m%d_%H%M")
    paths = []

    for area, group in groups.items():
        group.sort(key=lambda x: x.get("votes", 0), reverse=True)
        safe  = area.replace(" ", "_").replace("/", "-")
        fname = f"{output_dir}/{safe}_{ts}.png"
        path  = generate_election_image(
            group, constituency=area, output_path=fname,
            stale=(area in stale_constituencies),
        )
        paths.append(path)

    return paths


def cleanup_old_images(output_dir: str = "output", keep_cycles: int = 3):
    if not os.path.isdir(output_dir):
        return
    pngs = sorted(
        [f for f in os.listdir(output_dir) if f.endswith(".png")], reverse=True
    )
    seen_ts: list[str] = []
    for fname in pngs:
        parts = fname.rsplit("_", 2)
        if len(parts) >= 2:
            ts = "_".join(parts[-2:]).replace(".png", "")
            if ts not in seen_ts:
                seen_ts.append(ts)
    to_delete = seen_ts[keep_cycles:]
    deleted   = 0
    for fname in pngs:
        for old_ts in to_delete:
            if old_ts in fname:
                try:
                    os.remove(os.path.join(output_dir, fname))
                    deleted += 1
                except OSError:
                    pass
                break
    if deleted:
        print(f"[ImageGen] Cleaned up {deleted} old PNG(s) from {output_dir}/")