import asyncio
import os
import re
import time
import datetime
import bisect
import requests
import serial

import winrt.windows.media.control as media_control


# ============================================================
# KONFIGURASI
# ============================================================

PORT = "COM5"
BAUDRATE = 115200

LYRICS_FOLDER = "lyrics"

CHECK_SONG_INTERVAL = 0.5
CHECK_POSITION_INTERVAL = 0.03  # dipercepat dari 0.05 -> 0.03 (30ms)

LRCLIB_URL = "https://lrclib.net/api/get"


# ============================================================
# SERIAL ARDUINO
# ============================================================

try:
    arduino = serial.Serial(PORT, BAUDRATE, timeout=0.1)
    time.sleep(2)
    print("[OK] Arduino terhubung di", PORT)
except Exception as e:
    print("[ERROR] Arduino gagal terhubung:", e)
    raise SystemExit


# ============================================================
# UTILITAS
# ============================================================

def normalize(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def ensure_folder():
    if not os.path.exists(LYRICS_FOLDER):
        os.makedirs(LYRICS_FOLDER)


def find_local_lyrics(artist, title):
    ensure_folder()
    artist_key = normalize(artist)
    title_key = normalize(title)

    for filename in os.listdir(LYRICS_FOLDER):
        if not filename.lower().endswith(".lrc"):
            continue
        filename_key = normalize(os.path.splitext(filename)[0])
        if artist_key in filename_key and title_key in filename_key:
            return os.path.join(LYRICS_FOLDER, filename)

    return None


# ============================================================
# LRCLIB
# ============================================================

def get_lyrics_from_lrclib(artist, title):
    local_file = find_local_lyrics(artist, title)

    if local_file:
        print("[CACHE]", local_file)
        try:
            with open(local_file, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            print("[CACHE ERROR]", e)

    print("[LRCLIB] Mencari lirik...")

    try:
        response = requests.get(
            LRCLIB_URL,
            params={"artist_name": artist, "track_name": title},
            headers={"User-Agent": "SpotifyLyricsArduino/1.0"},
            timeout=10
        )

        if response.status_code != 200:
            print("[LRCLIB ERROR]", response.status_code)
            return None

        data = response.json()
        lyrics = data.get("syncedLyrics")

        if not lyrics:
            print("[LRCLIB] Lirik tidak ditemukan.")
            return None

        ensure_folder()
        filename = normalize(artist) + "-" + normalize(title) + ".lrc"
        filepath = os.path.join(LYRICS_FOLDER, filename)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(lyrics)

        print("[CACHE] Lirik disimpan:", filepath)
        return lyrics

    except Exception as e:
        print("[LRCLIB ERROR]", e)
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
        timestamp = minutes * 60 + seconds

        result.append((timestamp, lyric))

    result.sort(key=lambda x: x[0])
    return result


# ============================================================
# WINDOWS MEDIA SESSION
# ============================================================

async def get_session():
    try:
        manager_class = getattr(
            media_control,
            "GlobalSystemMediaTransportControlsSessionManager"
        )
        manager = await manager_class.request_async()
        sessions = manager.get_sessions()

        for session in sessions:
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

    except Exception as e:
        print("[SESSION ERROR]", e)

    return None, "", ""


async def get_position(session):
    """
    Posisi lagu diekstrapolasi berdasarkan waktu yang berlalu
    sejak Windows terakhir kali melaporkan posisi, supaya nilainya
    tidak "beku" di antara update Spotify -> Windows.
    """

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
            last_updated = timeline.last_updated_time
            elapsed = (now - last_updated).total_seconds()

            if elapsed > 0:
                position += elapsed

        return position

    except Exception:
        return 0.0


# ============================================================
# ARDUINO LCD
# ============================================================

def send_to_arduino(text):
    if not text:
        text = " "

    text = text.replace("\r", " ")
    text = text.replace("\n", " ")

    try:
        arduino.write((text + "\n").encode("utf-8"))
        arduino.flush()
        print("[LCD]", text)
    except Exception as e:
        print("[SERIAL ERROR]", e)


# ============================================================
# LIRIK SESUAI WAKTU
# ============================================================

def get_current_lyric(lyrics, position):
    if not lyrics:
        return ""

    timestamps = [lyric[0] for lyric in lyrics]
    index = bisect.bisect_right(timestamps, position) - 1

    if index < 0:
        return ""

    return lyrics[index][1]


# ============================================================
# MAIN
# ============================================================

async def main():
    print("[INFO] Menunggu lagu Spotify...")

    current_session = None
    current_song = ""
    lyrics = []

    last_song_check = 0
    last_lyric = None

    while True:
        now = time.monotonic()

        # --------------------------------------------------------
        # CEK LAGU BARU — dibatasi interval, tidak menghambat
        # update posisi/lirik di bawahnya
        # --------------------------------------------------------
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
                    print()
                    print("[SONG]", artist, "-", title)
                    send_to_arduino("Mencari lirik...")

                    lrc_text = await asyncio.to_thread(
                        get_lyrics_from_lrclib, artist, title
                    )

                    if lrc_text:
                        lyrics = parse_lrc(lrc_text)
                        print("[OK]", len(lyrics), "baris lirik dimuat.")
                    else:
                        print("[INFO] Tidak ada lirik.")
                        send_to_arduino("Lirik tidak ditemukan")

        # --------------------------------------------------------
        # UPDATE LIRIK — prioritas utama, jalan tiap iterasi cepat
        # --------------------------------------------------------
        if current_session and lyrics:
            position = await get_position(current_session)
            lyric = get_current_lyric(lyrics, position)

            if lyric != last_lyric:
                send_to_arduino(lyric)
                last_lyric = lyric

        await asyncio.sleep(CHECK_POSITION_INTERVAL)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
        print("[INFO] Program dihentikan.")
    finally:
        try:
            arduino.close()
            print("[INFO] Serial ditutup.")
        except Exception:
            pass