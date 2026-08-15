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


def truncate(s, max_len):
    return s if len(s) <= max_len else s[: max_len - 1] + "…"


def render_svg(tracks):
    width = 1000
    header_h = 46
    row_h = 96
    height = header_h + row_h + 26
    col_w = width / len(tracks)

    cols = []
    dividers = []
    for i, (name, artist) in enumerate(tracks):
        x = i * col_w
        pad = 18
        cols.append(f"""
  <text x="{x + pad:.1f}" y="{header_h + 26}" font-family="Menlo, monospace" font-size="11" fill="#1DB954">{i + 1:02d}</text>
  <text x="{x + pad:.1f}" y="{header_h + 48}" font-family="Menlo, monospace" font-size="13.5" font-weight="bold" fill="#ffffff">{esc(truncate(name, int(col_w // 8)))}</text>
  <text x="{x + pad:.1f}" y="{header_h + 68}" font-family="Menlo, monospace" font-size="12" fill="#9b9b9b">{esc(truncate(artist, int(col_w // 8.5)))}</text>""")
        if i > 0:
            dividers.append(
                f'<line x1="{x:.1f}" y1="{header_h + 14}" x2="{x:.1f}" y2="{header_h + row_h - 8}" stroke="#2a2a2a" stroke-width="1"/>'
            )

    body = "".join(cols)
    div_lines = "\n  ".join(dividers)
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" rx="14" fill="#181818"/>
  <circle cx="24" cy="23" r="8" fill="#1DB954"/>
  <text x="42" y="28" font-family="Menlo, monospace" font-size="15" font-weight="bold" fill="#ffffff">Top tracks this month</text>
  <text x="{width - 18}" y="28" font-family="Menlo, monospace" font-size="10" fill="#6b6b6b" text-anchor="end">updated {updated}</text>
  <line x1="0" y1="{header_h}" x2="{width}" y2="{header_h}" stroke="#2a2a2a" stroke-width="1"/>
  {div_lines}
  {body}
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
