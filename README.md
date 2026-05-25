# BrainzPod 🎧

> ⚠️ Please keep in mind that this is a vibecoded project.

BrainzPod syncs your ListenBrainz recommendation playlists, downloads clean audio from YouTube using yt-dlp, embeds proper metadata + album art, and organizes everything into beautiful playlist folders ready for:

- iPods
- Rockbox
- Foobar2000
- iTunes
- Jellyfin
- offline music libraries

---

# Features ✨

- Sync ListenBrainz recommendation playlists
- Download single songs
- Download full albums
- Proper metadata embedding
- Embedded album art
- Soundtrack / OST support
- Album Artist support for correct iPod grouping
- MP3 conversion via FFmpeg
- Playlist selection CLI
- iPod-friendly folder structure
- No streaming subscriptions required

---

# Example Folder Structure

```text
Music/
├── Weekly Jams/
│   ├── Joji - Slow Dancing in the Dark.mp3
│   ├── Kendrick Lamar - luther.mp3
│   └── ...
│
├── Weekly Exploration/
│   ├── Elvis Presley - Can't Help Falling in Love.mp3
│   └── ...
│
├── Qala (Soundtrack from the Netflix Film)/
│   ├── Amit Trivedi - Ghodey Pe Sawaar.mp3
│   └── ...
│
└── Singles/
    └── Nujabes - Aruarian Dance.mp3
```

All files contain:

- title
- artist
- album
- album artist
- genre
- release year
- embedded cover art

---

# Installation ⚙️

## Requirements

- Python 3.10+
- FFmpeg
- yt-dlp

---

## Install FFmpeg

### Windows

Download:
https://ffmpeg.org/download.html

Add FFmpeg to PATH.

Verify:

```bash
ffmpeg -version
```

---

## Install Python dependencies

```bash
pip install yt-dlp requests mutagen
```

---

# Configuration

Create a `config.json` file:

```json
{
  "listenbrainz_user": "YOUR_USERNAME",

  "music_dir": "./Music",

  "bad_words": [
    "slowed",
    "reverb",
    "sped up",
    "live",
    "concert",
    "8d",
    "bass boosted",
    "edit"
  ]
}
```

---

# Usage 🚀

## Sync ListenBrainz playlists

```bash
py sync.py
```

You’ll get an interactive playlist selector:

```text
Available playlists:

[1] Weekly Exploration...
[2] Weekly Jams...

Select playlists:
>
```

---

## Download a single song

```bash
py sync.py song "Joji - Slow Dancing in the Dark"
```

---

## Download an album

```bash
py sync.py album "Qala"
```

Works great with:

- movie soundtracks
- anime OSTs
- compilations
- Bollywood albums
- game soundtracks

---

# How It Works 🧠

```text
ListenBrainz
        ↓
Recommendation playlists
        ↓
yt-dlp audio retrieval
        ↓
Metadata enrichment
        ↓
Album art embedding
        ↓
iPod-ready MP3 library
```

Metadata and cover art are fetched from:

- Apple Music/iTunes APIs
- MusicBrainz ecosystem metadata

YouTube is used only as the audio source.

---

# Why BrainzPod Exists

Streaming services solved convenience.

They also quietly deleted:

- ownership
- permanence
- intentional listening
- weird little MP3 rituals

BrainzPod is for people who still enjoy:

- offline libraries
- curated playlists
- retro music players
- open music ecosystems
- syncing music like it’s 2007 but with modern metadata sorcery

---

# Disclaimer ⚠️

BrainzPod does not host or distribute music.

It retrieves publicly accessible media using yt-dlp. Users are responsible for complying with local laws and platform terms of service.

---

# Roadmap 🛣️

Planned ideas:

- Lyrics embedding
- MusicBrainz duration verification
- Duplicate detection
- Concurrent downloads
- ReplayGain normalization
- Automatic latest-playlist sync
- Rockbox playlist export
- Jellyfin integration
- Automatic iPod syncing
- Better metadata providers
- Configurable download quality

---

# Credits ❤️

Powered by:

- ListenBrainz
- MusicBrainz
- yt-dlp
- FFmpeg
- Mutagen

---

# BrainzPod 🎵

> Open metadata. Offline music. Tiny glowing clickwheel.
