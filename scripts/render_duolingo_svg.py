import datetime
import json
import os
import urllib.request

USERNAME = "AndyHo96"
BASE = os.path.join(os.path.dirname(__file__), "..")
HISTORY_PATH = os.path.join(BASE, "assets", "duolingo-history.json")
OUT_PATH = os.path.join(BASE, "assets", "duolingo.svg")

GREEN = "#58CC02"
GREEN_DIM = "#2b5c10"
EMPTY = "#242424"


def fetch_profile():
    req = urllib.request.Request(
        f"https://www.duolingo.com/2017-06-30/users?username={USERNAME}",
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
    )
    with urllib.request.urlopen(req) as resp:
        users = json.load(resp).get("users", [])
    if not users:
        raise RuntimeError(f"Duolingo user {USERNAME} not found")
    return users[0]


def load_history():
    try:
        with open(HISTORY_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_history(history):
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=1, sort_keys=True)


def update_history(history, profile, today):
    prev_dates = [d for d in history if d < today.isoformat()]
    prev = history[max(prev_dates)] if prev_dates else None
    xp_today = profile["totalXp"] - prev["totalXp"] if prev else 0
    # practiced = streak grew or is intact vs yesterday, or XP moved
    practiced = xp_today > 0 or (prev is not None and profile["streak"] > prev["streak"])
    history[today.isoformat()] = {
        "streak": profile["streak"],
        "totalXp": profile["totalXp"],
        "practiced": practiced,
    }
    return history


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_svg(profile, history, today):
    width = 1000
    height = 210
    streak = profile["streak"]
    total_xp = profile["totalXp"]
    start_date = (
        profile.get("streakData", {}).get("currentStreak", {}).get("startDate", "")
    )
    courses = sorted(
        [(c["title"], c["xp"]) for c in profile.get("courses", []) if c.get("xp", 0) > 0],
        key=lambda c: -c[1],
    )[:5]

    cell = 11
    gap = 3
    weeks = 26
    grid_w = weeks * (cell + gap)
    grid_x = width - grid_w - 24
    grid_y = 62

    cells = []
    for week in range(weeks):
        for day in range(7):
            days_ago = (weeks - 1 - week) * 7 + (6 - day)
            date = today - datetime.timedelta(days=days_ago)
            if date > today:
                continue
            entry = history.get(date.isoformat())
            if entry is None:
                fill = EMPTY
            elif entry.get("practiced"):
                fill = GREEN
            else:
                fill = GREEN_DIM
            x = grid_x + week * (cell + gap)
            y = grid_y + day * (cell + gap)
            cells.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{fill}"/>'
            )

    course_bits = []
    cx = 24
    for name, xp in courses:
        label = f"{name} {xp:,} XP"
        w = 14 + len(label) * 7.3
        course_bits.append(
            f'<rect x="{cx:.0f}" y="150" width="{w:.0f}" height="22" rx="11" fill="{EMPTY}"/>'
        )
        course_bits.append(
            f'<text x="{cx + w / 2:.0f}" y="165" text-anchor="middle" '
            f'font-family="Menlo, monospace" font-size="11" fill="#c8c8c8">{esc(label)}</text>'
        )
        cx += w + 10

    since = f" · since {start_date}" if start_date else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" rx="14" fill="#181818"/>
  <circle cx="24" cy="26" r="8" fill="{GREEN}"/>
  <text x="42" y="31" font-family="Menlo, monospace" font-size="15" font-weight="bold" fill="#ffffff">Duolingo</text>
  <text x="{width - 18}" y="31" font-family="Menlo, monospace" font-size="10" fill="#6b6b6b" text-anchor="end">updated {today.isoformat()}</text>
  <line x1="0" y1="46" x2="{width}" y2="46" stroke="#2a2a2a" stroke-width="1"/>

  <text x="24" y="96" font-family="Menlo, monospace" font-size="34" font-weight="bold" fill="{GREEN}">🔥 {streak}</text>
  <text x="24" y="116" font-family="Menlo, monospace" font-size="12" fill="#9b9b9b">day streak{since}</text>
  <text x="24" y="138" font-family="Menlo, monospace" font-size="12" fill="#c8c8c8">{total_xp:,} total XP</text>

  {"".join(course_bits)}

  <text x="{grid_x}" y="{grid_y - 8}" font-family="Menlo, monospace" font-size="10" fill="#6b6b6b">practice days</text>
  {"".join(cells)}
</svg>
"""


def main():
    today = datetime.date.today()
    profile = fetch_profile()
    history = load_history()
    history = update_history(history, profile, today)
    save_history(history)
    svg = render_svg(profile, history, today)
    out_path = os.path.abspath(OUT_PATH)
    with open(out_path, "w") as f:
        f.write(svg)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
