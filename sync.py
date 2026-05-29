import os
import re
import json
import shutil
import requests
import subprocess
from pathlib import Path
import sys
sys.stdout.reconfigure(encoding="utf-8")
import argparse
from mutagen.id3 import TPE2
from mutagen.id3 import (
    ID3,
    TIT2,
    TPE1,
    TALB,
    TCON,
    TYER,
    APIC,
)
from mutagen.mp4 import MP4, MP4Cover
import base64
from pyDes import des, ECB, PAD_PKCS5


CONFIG = json.load(open("config.json"))

LB_USER = CONFIG["listenbrainz_user"]
MUSIC_DIR = Path(CONFIG["music_dir"])
BAD_WORDS = [x.lower() for x in CONFIG["bad_words"]]

HEADERS = {
    "User-Agent": "ListenBrainzSync/1.0"
}


def sanitize(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)


def get_playlists():
    url = f"https://api.listenbrainz.org/1/user/{LB_USER}/playlists/createdfor"

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        print("Failed to fetch playlists")
        return []

    data = r.json()

    playlists = []

    for item in data["playlists"]:

        playlist = item["playlist"]

        title = playlist["title"]

        identifier = playlist["identifier"]

        playlists.append({
            "title": title,
            "id": identifier.split("/")[-1]
        })

    return playlists


def get_tracks(playlist_id):
    url = f"https://api.listenbrainz.org/1/playlist/{playlist_id}"

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        print(f"Failed to fetch tracks for {playlist_id}")
        return []

    data = r.json()

    tracks = []

    playlist = data.get("playlist", {})

    for t in playlist.get("track", []):

        artist = t.get("creator", "").strip()
        title = t.get("title", "").strip()

        if not artist or not title:
            continue

        tracks.append({
            "artist": artist,
            "title": title
        })

    return tracks


def enrich_metadata(track):
    query = f"{track['title']} {track['artist']}"

    url = "https://itunes.apple.com/search"

    params = {
        "term": query,
        "entity": "song",
        "limit": 1
    }

    try:
        r = requests.get(url, params=params)
        data = r.json()

        if data["resultCount"] > 0:
            item = data["results"][0]

            track["album"] = item.get("collectionName")
            track["genre"] = item.get("primaryGenreName")
            track["year"] = item.get("releaseDate", "")[:4]
            track["duration"] = item.get("trackTimeMillis", 0) / 1000.0

            art = item.get("artworkUrl100")

            if art:
                track["cover_url"] = art.replace(
                    "100x100",
                    "1000x1000"
                )

    except Exception as e:
        print("Metadata fetch failed:", e)

    return track


def is_bad_result(text):
    text = text.lower()

    for word in BAD_WORDS:
        if word in text:
            return True

    return False


def search_jiosaavn(query):
    url = "https://www.jiosaavn.com/api.php"
    params = {
        "__call": "search.getResults",
        "q": query,
        "p": 1,
        "n": 5,
        "_format": "json",
        "_marker": 0
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=20)
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            if results:
                return results[0]
    except Exception as e:
        print("JioSaavn search failed:", e)
    return None

def get_dec_url(enc_url):
    des_cipher = des(b"38346591", ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)
    enc_url = base64.b64decode(enc_url.strip())
    dec_url = des_cipher.decrypt(enc_url, padmode=PAD_PKCS5).decode("utf-8")
    dec_url = dec_url.replace("_96.mp4", "_320.mp4")
    return dec_url

def download_song(track, outdir):
    artist = track["artist"]
    title = track["title"]

    query = f"{title} {artist} official audio"

    print(f"Searching JioSaavn: {title} {artist}")
    saavn_result = search_jiosaavn(f"{title} {artist}")
    
    import html
    if saavn_result:
        expected_duration = track.get("duration", 0)
        saavn_duration = int(saavn_result.get("duration", 0))
        
        is_duration_match = True
        if expected_duration > 0 and saavn_duration > 0:
            if abs(expected_duration - saavn_duration) > 10:
                is_duration_match = False
                print(f"Duration mismatch! Expected {expected_duration:.0f}s, got {saavn_duration}s. Falling back to yt-dlp.")
                
        if is_duration_match:
            # Only overwrite title and artist if we don't already have a valid artist. 
            # (If we have an artist, it means iTunes or the user provided clean, reliable metadata)
            if "song" in saavn_result and not track.get("artist"):
                track["title"] = html.unescape(saavn_result["song"])
            if "primary_artists" in saavn_result and not track.get("artist"):
                track["artist"] = html.unescape(saavn_result["primary_artists"])
            
            # Prioritize iTunes/existing metadata for Album, Year, and Cover 
            # because JioSaavn search often returns singles or compilation albums instead of the original album.
            if "album" in saavn_result and not track.get("album"):
                track["album"] = html.unescape(saavn_result["album"])
            if "year" in saavn_result and not track.get("year"):
                track["year"] = saavn_result["year"]
            if "image" in saavn_result and not track.get("cover_url"):
                cover_url = re.sub(r'-\d+x\d+\.(jpg|webp)', '-500x500.jpg', saavn_result["image"])
                track["cover_url"] = cover_url
        else:
            saavn_result = None

    safe_name = sanitize(track["title"])

    final_mp4 = outdir / f"{safe_name}.mp4"
    final_mp3 = outdir / f"{safe_name}.mp3"

    if final_mp4.exists():
        print(f"Skipping existing: {safe_name}")
        return final_mp4
    if final_mp3.exists():
        print(f"Skipping existing: {safe_name}")
        return final_mp3

    if saavn_result and "encrypted_media_url" in saavn_result:
        try:
            print("Downloading from JioSaavn...")
            dec_url = get_dec_url(saavn_result["encrypted_media_url"])
            
            # Download mp4 directly without ffmpeg conversion
            with requests.get(dec_url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(final_mp4, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            if final_mp4.exists():
                return final_mp4
            else:
                print("JioSaavn download failed, falling back to yt-dlp")
        except Exception as e:
            print("JioSaavn processing failed:", e)
            print("Falling back to yt-dlp")

    print("Searching YouTube:", query)

    cmd = [
        "yt-dlp",

        f"ytsearch1:{query}",

        "--extract-audio",

        "--audio-format",
        "mp3",

        "--audio-quality",
        "0",

        "--embed-thumbnail",
        "--embed-metadata",

        "--no-playlist",

        "--output",
        str(outdir / f"{safe_name}.%(ext)s")
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )

    if result.returncode != 0:
        print("yt-dlp failed")
        print(result.stderr[:1000])
        return None

    if final_mp3.exists():
        return final_mp3

    print("MP3 not found after download")
    return None


def embed_metadata(file_path, track):
    file_str = str(file_path)
    if file_str.endswith(".mp4") or file_str.endswith(".m4a"):
        try:
            audio = MP4(file_path)
        except:
            print("Could not load MP4 tags")
            return
            
        if track.get("title"):
            audio["\xa9nam"] = track["title"]
        if track.get("artist"):
            audio["\xa9ART"] = track["artist"]
        
        album_artist = track.get("album_artist", track.get("artist"))
        if album_artist:
            audio["aART"] = album_artist
            
        if track.get("album"):
            audio["\xa9alb"] = track["album"]
        if track.get("genre"):
            audio["\xa9gen"] = track["genre"]
        if track.get("year"):
            audio["\xa9day"] = str(track["year"])
            
        if track.get("cover_url"):
            try:
                img = requests.get(track["cover_url"]).content
                covr_fmt = MP4Cover.FORMAT_PNG if track["cover_url"].endswith("png") else MP4Cover.FORMAT_JPEG
                audio["covr"] = [MP4Cover(img, covr_fmt)]
            except Exception as e:
                print("Cover art failed:", e)
                
        audio.save()
        return

    try:
        audio = ID3(file_path)
    except:
        audio = ID3()

    audio.delall("TIT2")
    audio.delall("TPE1")
    audio.delall("TPE2")
    audio.delall("TALB")
    audio.delall("TCON")
    audio.delall("TYER")
    audio.delall("APIC")

    audio.add(
        TIT2(
            encoding=3,
            text=track["title"]
        )
    )

    audio.add(
        TPE1(
            encoding=3,
            text=track["artist"]
        )
    )

    audio.add(
        TPE2(
            encoding=3,
            text=track.get(
                "album_artist",
                track["artist"]
            )
        )
    )

    if track.get("album"):
        audio.add(
            TALB(
                encoding=3,
                text=track["album"]
            )
        )

    if track.get("genre"):
        audio.add(
            TCON(
                encoding=3,
                text=track["genre"]
            )
        )

    if track.get("year"):
        audio.add(
            TYER(
                encoding=3,
                text=str(track["year"])
            )
        )

    if track.get("cover_url"):
        try:
            img = requests.get(track["cover_url"]).content

            audio.add(
                APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3,
                    desc="Cover",
                    data=img
                )
            )

        except Exception as e:
            print("Cover art failed:", e)

    audio.save(file_path)

def download_single_song(query):
    folder = MUSIC_DIR / "Singles"

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    track = {
        "artist": "",
        "title": query
    }

    parts = query.split(" - ", 1)

    if len(parts) == 2:
        track["artist"] = parts[0]
        track["title"] = parts[1]

    track = enrich_metadata(track)

    mp3 = download_song(track, folder)

    if mp3:
        embed_metadata(mp3, track)
        print("Finished")

def download_album(album_name):
    print(f"Searching album: {album_name}")

    url = "https://itunes.apple.com/search"

    params = {
        "term": album_name,
        "entity": "album",
        "limit": 1
    }

    r = requests.get(url, params=params)

    data = r.json()

    if data["resultCount"] == 0:
        print("Album not found")
        return

    album = data["results"][0]

    collection_id = album["collectionId"]

    lookup = requests.get(
        "https://itunes.apple.com/lookup",
        params={
            "id": collection_id,
            "entity": "song"
        }
    ).json()

    album_title = sanitize(album["collectionName"])

    folder = MUSIC_DIR / album_title

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    tracks = lookup["results"][1:]

    print(f"Tracks found: {len(tracks)}")

    for idx, t in enumerate(tracks, start=1):

        cover = (
            t.get("artworkUrl100", "")
             .replace("100x100", "1000x1000")
        )

        track = {
            "artist": t.get("artistName", ""),
            "title": t.get("trackName", ""),
            "album": t.get("collectionName", ""),
            "album_artist": album.get("artistName", "Various Artists"),
            "genre": t.get("primaryGenreName", ""),
            "year": t.get("releaseDate", "")[:4],
            "cover_url": cover,
            "duration": t.get("trackTimeMillis", 0) / 1000.0
        }

        print(
            f"[{idx}/{len(tracks)}] "
            f"{track['artist']} - {track['title']}"
        )

        mp3 = download_song(track, folder)

        if mp3:
            embed_metadata(mp3, track)

    print("Album finished")

def select_playlists(playlists):
    print("\nAvailable playlists:\n")

    for idx, playlist in enumerate(playlists, start=1):
        print(f"[{idx}] {playlist['title']}")

    print("\nType playlist numbers separated by commas")
    print("Example: 1,2")
    print("Or type: all")

    choice = input("\nSelect playlists: ").strip()

    if choice.lower() == "all":
        return playlists

    selected = []

    try:
        indexes = [
            int(x.strip()) - 1
            for x in choice.split(",")
        ]

        for i in indexes:
            if 0 <= i < len(playlists):
                selected.append(playlists[i])

    except:
        print("Invalid selection")
        return []

    return selected

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "mode",
        nargs="?",
        default="playlist"
    )

    parser.add_argument(
        "query",
        nargs="*"
    )

    args = parser.parse_args()

    query = " ".join(args.query)

    if args.mode == "song":

        if not query:
            print("Provide song name")
            return

        download_single_song(query)
        return

    if args.mode == "album":

        if not query:
            print("Provide album name")
            return

        download_album(query)
        return

    playlists = get_playlists()

    if not playlists:
        print("No playlists found")
        return

    playlists = select_playlists(playlists)

    if not playlists:
        print("Nothing selected")
        return

    for playlist in playlists:
        pname = sanitize(playlist["title"])

        print(f"\n==========")
        print(f"Playlist: {pname}")
        print("==========")

        folder = MUSIC_DIR / pname

        if folder.exists():
            shutil.rmtree(folder)

        folder.mkdir(
            parents=True,
            exist_ok=True
        )

        tracks = get_tracks(playlist["id"])

        print(f"Tracks found: {len(tracks)}")

        for idx, track in enumerate(tracks, start=1):

            print(
                f"\n[{idx}/{len(tracks)}] "
                f"{track['artist']} - {track['title']}"
            )

            track = enrich_metadata(track)

            mp3 = download_song(track, folder)

            if not mp3:
                continue

            embed_metadata(mp3, track)

            print("Finished")


if __name__ == "__main__":
    main()
