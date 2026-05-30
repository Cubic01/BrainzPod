# BrainzPod 🎧

> ⚠️ Please keep in mind that this is a vibecoded project.

BrainzPod syncs your ListenBrainz recommendation playlists, downloads clean audio from YouTube and JioSaavn, embeds proper metadata + album art, and organizes everything into beautiful playlist folders ready for offline music libraries (iPods, Rockbox, Jellyfin).

## ✨ Features

- **Universal Playlist Support (NEW)**: Paste a playlist URL from **Spotify**, **Apple Music**, **JioSaavn**, or **YouTube** to download it automatically.
- **ListenBrainz Sync**: Interactive CLI to sync your ListenBrainz recommendation playlists natively.
- **Album & Track Downloader**: Easily download entire albums or search for specific single tracks.
- **Smart Metadata**: Fetches exact metadata (Title, Artist, Album, Cover Art, Year) from the iTunes API and embeds it into the MP3.
- **High-Quality Audio**: Downloads the highest quality audio available using JioSaavn, with a smart fallback to `yt-dlp` (YouTube) if a track is missing or the duration is incorrect.

## 🚀 Installation

Ensure you have Python 3.8+ and **FFmpeg** installed on your system.

```bash
pip install -r requirements.txt
```

*For ListenBrainz sync:* Create a `config.json` with your username (`"listenbrainz_user": "USERNAME"`).

## 🛠️ Usage

**Download a Spotify/Apple Music/JioSaavn Playlist:**
```bash
python sync.py playlist "https://music.apple.com/us/playlist/..."
```

**Sync ListenBrainz Playlists:**
```bash
python sync.py
```

**Download an Album:**
```bash
python sync.py album "AM Arctic Monkeys"
```

**Download a Single Track:**
```bash
python sync.py song "Joji - Slow Dancing in the Dark"
```

## 🧠 Why BrainzPod Exists

Streaming services solved convenience but quietly deleted ownership, permanence, and intentional listening. BrainzPod is for people who still enjoy curated offline libraries, retro music players (like iPods), and syncing music like it’s 2007—but with modern metadata sorcery!

## ❤️ Credits

Powered by:
- ListenBrainz & MusicBrainz
- yt-dlp & FFmpeg
- Mutagen & Rich

> Open metadata. Offline music. 
