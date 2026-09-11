import asyncio
import bisect
import datetime
import os
import re
import time
from pathlib import Path

import requests
import serial
import winrt.windows.media.control as media_control


# ============================================================
# KONFIGURASI
# ============================================================

PORT = os.getenv("SERIAL_PORT", "COM5")
BAUDRATE = int(os.getenv("SERIAL_BAUDRATE", "115200"))
LYRICS_FOLDER = Path(os.getenv("LYRICS_FOLDER", "lyrics"))

CHECK_SONG_INTERVAL = 0.5
CHECK_POSITION_INTERVAL = 0.03
LRCLIB_URL = os.getenv("LRCLIB_URL", "https://lrclib.net/api/get")


# ============================================================
# SERIAL ARDUINO
# ============================================================

def open_arduino():
    try:
        device = serial.Serial(PORT, BAUDRATE, timeout=0.1)
        time.sleep(2)
        print("[OK] Arduino terhubung di", PORT)
        return device
    except (serial.SerialException, ValueError) as exc:
        print("[ERROR] Arduino gagal terhubung:", exc)
        raise SystemExit(1)


# ============================================================
# UTILITAS
# ============================================================

def normalize(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def ensure_folder():
    LYRICS_FOLDER.mkdir(parents=True, exist_ok=True)


def find_local_lyrics(artist, title):
    ensure_folder()
    artist_key = normalize(artist)
    title_key = normalize(title)

    for path in LYRICS_FOLDER.glob("*.lrc"):
        filename_key = normalize(path.stem)
        if artist_key in filename_key and title_key in filename_key:
            return path
    return None


# ============================================================
# LRCLIB
# ============================================================

def get_lyrics_from_lrclib(artist, title):
    local_file = find_local_lyrics(artist, title)

    if local_file:
        print("[CACHE]", local_file)
        try:
            return local_file.read_text(encoding="utf-8")
        except OSError as exc:
            print("[CACHE ERROR]", exc)

    print("[LRCLIB] Mencari lirik...")

    try:
        response = requests.get(
            LRCLIB_URL,
            params={"artist_name": artist, "track_name": title},
            headers={"User-Agent": "SpotifyLyricsArduino/1.0"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        lyrics = data.get("syncedLyrics")

        if not lyrics:
            print("[LRCLIB] Lirik tidak ditemukan.")
            return None

        ensure_folder()
        filepath = LYRICS_FOLDER / f"{normalize(artist)}-{normalize(title)}.lrc"
        filepath.write_text(lyrics, encoding="utf-8")
        print("[CACHE] Lirik disimpan:", filepath)
        return lyrics

    except (requests.RequestException, ValueError, OSError) as exc:
        print("[LRCLIB ERROR]", exc)
        return None


# ============================================================
# PARSE FILE LRC
# ============================================================

def parse_lrc(text):
    result = []
    if not text:
        return result

    pattern = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\](.*)")

    for line in text.splitlines():
        match = pattern.match(line)
        if not match:
            continue

        minutes = int(match.group(1))
        seconds = float(match.group(2))
        lyric = match.group(3).strip()
        result.append((minutes * 60 + seconds, lyric))

    result.sort(key=lambda item: item[0])
    return result


# ============================================================
# WINDOWS MEDIA SESSION
# ============================================================

async def get_session():
    try:
        manager_class = getattr(
            media_control, "GlobalSystemMediaTransportControlsSessionManager"
        )
        manager = await manager_class.request_async()

        for session in manager.get_sessions():
            try:
                properties = await session.try_get_media_properties_async()
                if properties is None:
                    continue

                title = properties.title or ""
                artist = properties.artist or ""
                if title.strip():
                    return session, title, artist
            except Exception:
                continue

    except Exception as exc:
        print("[SESSION ERROR]", exc)

    return None, "", ""


async def get_position(session):
    try:
        timeline = session.get_timeline_properties()
        playback_info = session.get_playback_info()
        position = timeline.position.total_seconds()

        is_playing = (
            playback_info.playback_status
            == media_control.GlobalSystemMediaTransportControlsSessionPlaybackStatus.PLAYING
        )

        if is_playing:
            now = datetime.datetime.now(datetime.timezone.utc)
            elapsed = (now - timeline.last_updated_time).total_seconds()
            if elapsed > 0:
                position += elapsed

        return position
    except Exception:
        return 0.0


# ============================================================
# ARDUINO LCD
# ============================================================

def send_to_arduino(arduino, text):
    text = (text or " ").replace("\r", " ").replace("\n", " ")

    try:
        arduino.write((text + "\n").encode("utf-8"))
        arduino.flush()
        print("[LCD]", text)
    except serial.SerialException as exc:
        print("[SERIAL ERROR]", exc)


# ============================================================
# LIRIK SESUAI WAKTU
# ============================================================

def get_current_lyric(lyrics, position):
    if not lyrics:
        return ""

    timestamps = [timestamp for timestamp, _ in lyrics]
    index = bisect.bisect_right(timestamps, position) - 1
    return "" if index < 0 else lyrics[index][1]


# ============================================================
# MAIN
# ============================================================

async def main():
    arduino = open_arduino()
    print("[INFO] Menunggu lagu Spotify...")

    current_session = None
    current_song = ""
    lyrics = []
    last_song_check = 0.0
    last_lyric = None

    try:
        while True:
            now = time.monotonic()

            if current_session is None or now - last_song_check >= CHECK_SONG_INTERVAL:
                last_song_check = now
                session, title, artist = await get_session()

                if session is not None:
                    song_id = normalize(artist) + "|" + normalize(title)

                    if song_id != current_song:
                        current_session = session
                        current_song = song_id
                        lyrics = []
                        last_lyric = None
                        print("\n[SONG]", artist, "-", title)
                        send_to_arduino(arduino, "Mencari lirik...")

                        lrc_text = await asyncio.to_thread(
                            get_lyrics_from_lrclib, artist, title
                        )

                        if lrc_text:
                            lyrics = parse_lrc(lrc_text)
                            print("[OK]", len(lyrics), "baris lirik dimuat.")
                        else:
                            print("[INFO] Tidak ada lirik.")
                            send_to_arduino(arduino, "Lirik tidak ditemukan")

            if current_session and lyrics:
                position = await get_position(current_session)
                lyric = get_current_lyric(lyrics, position)

                if lyric != last_lyric:
                    send_to_arduino(arduino, lyric)
                    last_lyric = lyric

            await asyncio.sleep(CHECK_POSITION_INTERVAL)
    finally:
        arduino.close()
        print("[INFO] Serial ditutup.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Program dihentikan.")
