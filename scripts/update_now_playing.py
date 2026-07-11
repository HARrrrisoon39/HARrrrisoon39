import os
import base64
import requests
import xml.sax.saxutils as saxutils

CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["SPOTIFY_REFRESH_TOKEN"]


def get_access_token():
    creds = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {creds}"},
        data={"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_now_playing(token):
    resp = requests.get(
        "https://api.spotify.com/v1/me/player/currently-playing",
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code == 204 or resp.status_code == 404:
        return None
    resp.raise_for_status()
    data = resp.json()
    if not data or not data.get("is_playing"):
        return None
    item = data.get("item")
    if not item:
        return None
    return {
        "title": item["name"],
        "artist": ", ".join(a["name"] for a in item["artists"]),
        "url": item["external_urls"]["spotify"],
    }


def get_recently_played(token):
    resp = requests.get(
        "https://api.spotify.com/v1/me/player/recently-played?limit=1",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    if not items:
        return None
    track = items[0]["track"]
    return {
        "title": track["name"],
        "artist": ", ".join(a["name"] for a in track["artists"]),
        "url": track["external_urls"]["spotify"],
        "recent": True,
    }


def truncate(text, max_chars):
    return text if len(text) <= max_chars else text[: max_chars - 1] + "…"


def build_svg(title, artist, url, is_recent=False):
    label = "LAST PLAYED" if is_recent else "NOW PLAYING"
    title_safe = saxutils.escape(truncate(title, 28))
    artist_safe = saxutils.escape(truncate(artist, 36))
    url_safe = saxutils.escape(url)

    return f"""<svg width="420" height="148" viewBox="0 0 420 148" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    @keyframes spin {{
      from {{ transform: rotate(-15deg); }}
      to   {{ transform: rotate(15deg); }}
    }}
    @keyframes b1 {{ 0%,100%{{height:4px}}  50%{{height:14px}} }}
    @keyframes b2 {{ 0%,100%{{height:10px}} 50%{{height:4px}}  }}
    @keyframes b3 {{ 0%,100%{{height:6px}}  50%{{height:14px}} }}
    @keyframes b4 {{ 0%,100%{{height:14px}} 50%{{height:6px}}  }}
    @keyframes progress {{ 0%{{width:80px}} 100%{{width:280px}} }}
    .album         {{ animation: spin 2s ease-in-out infinite alternate; transform-origin: 50px 50px; }}
    .b1 {{ animation: b1 0.8s ease-in-out infinite;       }}
    .b2 {{ animation: b2 0.8s ease-in-out infinite 0.1s;  }}
    .b3 {{ animation: b3 0.8s ease-in-out infinite 0.2s;  }}
    .b4 {{ animation: b4 0.8s ease-in-out infinite 0.15s; }}
    .progress-fill {{ animation: progress 6s ease-in-out infinite alternate; }}
  </style>

  <rect width="420" height="148" rx="14" fill="#1a1a2e"/>
  <rect width="420" height="148" rx="14" fill="none" stroke="#2d2d5e" stroke-width="1"/>

  <g class="album">
    <rect x="16" y="16" width="68" height="68" rx="10" fill="url(#albumGrad)"/>
    <text x="50" y="60" font-size="28" text-anchor="middle" fill="rgba(255,255,255,0.3)" font-family="Arial">&#9835;</text>
  </g>

  <text x="102" y="34" font-size="10" font-weight="700" fill="#1db954"
        font-family="Arial, sans-serif" letter-spacing="1">{label}</text>

  <g transform="translate(200, 34)">
    <rect class="b1" x="0"  y="0" width="3" height="4"  rx="2" fill="#1db954" transform="translate(0,10)"/>
    <rect class="b2" x="5"  y="0" width="3" height="10" rx="2" fill="#1db954" transform="translate(0,4)"/>
    <rect class="b3" x="10" y="0" width="3" height="6"  rx="2" fill="#1db954" transform="translate(0,8)"/>
    <rect class="b4" x="15" y="0" width="3" height="14" rx="2" fill="#1db954" transform="translate(0,0)"/>
  </g>

  <text x="102" y="54" font-size="16" font-weight="700" fill="#ffffff"
        font-family="Arial, sans-serif">{title_safe}</text>

  <text x="102" y="70" font-size="12" fill="#8b949e"
        font-family="Arial, sans-serif">{artist_safe}</text>

  <rect x="102" y="82" width="300" height="3" rx="2" fill="#2a2a4a"/>
  <rect class="progress-fill" x="102" y="82" width="80" height="3" rx="2" fill="#1db954"/>

  <line x1="16" y1="101" x2="404" y2="101" stroke="#2d2d5e" stroke-width="1"/>

  <a href="{url_safe}">
    <rect x="110" y="112" width="200" height="26" rx="13" fill="#1db954"/>
    <path d="M122 121.5 Q128 119.2 134 121.5" stroke="#000" stroke-width="1.8" fill="none" stroke-linecap="round"/>
    <path d="M122.5 124.5 Q128 122.5 133.5 124.5" stroke="#000" stroke-width="1.6" fill="none" stroke-linecap="round"/>
    <path d="M123.5 127.2 Q128 125.8 132.5 127.2" stroke="#000" stroke-width="1.4" fill="none" stroke-linecap="round"/>
    <text x="224" y="129" font-size="10.5" font-weight="700" fill="#000000"
          font-family="Arial, sans-serif" text-anchor="middle" letter-spacing="0.8">&#x25B6;  PLAY ON SPOTIFY</text>
  </a>

  <defs>
    <linearGradient id="albumGrad" x1="0" y1="0" x2="68" y2="68" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#c724d4"/>
      <stop offset="100%" stop-color="#7928ca"/>
    </linearGradient>
  </defs>
</svg>"""


def main():
    token = get_access_token()
    track = get_now_playing(token) or get_recently_played(token)

    if track:
        svg = build_svg(track["title"], track["artist"], track["url"], track.get("recent", False))
    else:
        svg = build_svg("Nothing playing", "", "https://open.spotify.com")

    with open("now-playing.svg", "w", encoding="utf-8") as f:
        f.write(svg)

    status = "recently played" if track and track.get("recent") else "now playing"
    name = track["title"] if track else "nothing"
    print(f"Updated: {name} ({status})")


if __name__ == "__main__":
    main()
