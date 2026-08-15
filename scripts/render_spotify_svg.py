import base64
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["SPOTIFY_REFRESH_TOKEN"]

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "spotify-top-tracks.svg")


def get_access_token():
    data = urllib.parse.urlencode(
        {"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN}
    ).encode()
    auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=data,
        headers={"Authorization": f"Basic {auth}"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)["access_token"]


def get_top_tracks(token, limit=5):
    req = urllib.request.Request(
        f"https://api.spotify.com/v1/me/top/tracks?time_range=short_term&limit={limit}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req) as resp:
        body = json.load(resp)
    tracks = []
    for item in body.get("items", []):
        name = item["name"]
        artist = ", ".join(a["name"] for a in item["artists"])
        tracks.append((name, artist))
    return tracks


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_svg(tracks):
    row_h = 34
    width = 480
    height = 60 + row_h * len(tracks) + 20
    rows = []
    y = 70
    for i, (name, artist) in enumerate(tracks, start=1):
        label = f"{i}. {name} — {artist}"
        if len(label) > 58:
            label = label[:55] + "..."
        rows.append(
            f'<text x="30" y="{y}" font-family="Menlo, monospace" '
            f'font-size="14" fill="#e5e5e5">{esc(label)}</text>'
        )
        y += row_h
    body = "\n  ".join(rows)
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" rx="14" fill="#181818"/>
  <circle cx="30" cy="32" r="10" fill="#1DB954"/>
  <text x="50" y="37" font-family="Menlo, monospace" font-size="16" font-weight="bold" fill="#ffffff">Top tracks this month</text>
  {body}
  <text x="30" y="{height - 12}" font-family="Menlo, monospace" font-size="10" fill="#6b6b6b">updated {updated}</text>
</svg>
"""


def main():
    token = get_access_token()
    tracks = get_top_tracks(token)
    if not tracks:
        tracks = [("No listening data yet", "check back after a few plays")]
    svg = render_svg(tracks)
    out_path = os.path.abspath(OUT_PATH)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(svg)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
