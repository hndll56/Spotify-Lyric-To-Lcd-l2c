import asyncio
import os
import re
import time
import datetime
import bisect
from urllib.parse import quote

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
CHECK_POSITION_INTERVAL = 0.03

# Interval tampilan untuk lirik tanpa timestamp
PLAIN_LYRICS_INTERVAL = 3.0

LRCLIB_URL = "https://lrclib.net/api/get"
LYRICS_OVH_URL = "https://api.lyrics.ovh/v1"

# ============================================================
# ICON INSTRUMENTAL
# ============================================================
# Byte 0x01 dikirim mentah ke Arduino. Selama sketch Arduino
# memanggil lcd.createChar(1, ...) untuk mendaftarkan bitmap
# not musik di slot custom-char 1, karakter LiquidCrystal akan
# otomatis menampilkan ikon not musik saat menerima byte ini
# (lihat catatan Arduino yang disertakan bersama patch ini).
NOTE_ICON = "\x01"


# ============================================================
# SERIAL ARDUINO
# ============================================================

try:
    arduino = serial.Serial(
        PORT,
        BAUDRATE,
        timeout=0.1
    )

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


def get_cache_filename(artist, title, extension):
    artist_key = normalize(artist)
    title_key = normalize(title)

    return f"{artist_key}-{title_key}{extension}"


# ============================================================
# CARI CACHE LOKAL
# ============================================================

def find_local_lyrics(artist, title):
    ensure_folder()

    artist_key = normalize(artist)
    title_key = normalize(title)

    for filename in os.listdir(LYRICS_FOLDER):

        if not filename.lower().endswith((".lrc", ".txt")):
            continue

        filename_key = normalize(
            os.path.splitext(filename)[0]
        )

        if artist_key in filename_key and title_key in filename_key:
            return os.path.join(LYRICS_FOLDER, filename)

    return None


# ============================================================
# LRCLIB
# ============================================================

def get_lyrics_from_lrclib(artist, title):
    print("[LRCLIB] Mencari lirik...")

    try:
        response = requests.get(
            LRCLIB_URL,
            params={
                "artist_name": artist,
                "track_name": title
            },
            headers={
                "User-Agent": "SpotifyLyricsArduino/1.0"
            },
            timeout=10
        )

        if response.status_code != 200:
            print(
                "[LRCLIB] Tidak ditemukan:",
                response.status_code
            )
            return None

        data = response.json()

        # Prioritaskan syncedLyrics
        synced_lyrics = data.get("syncedLyrics")

        if synced_lyrics:
            ensure_folder()

            filename = get_cache_filename(
                artist,
                title,
                ".lrc"
            )

            filepath = os.path.join(
                LYRICS_FOLDER,
                filename
            )

            with open(filepath, "w", encoding="utf-8") as file:
                file.write(synced_lyrics)

            print("[LRCLIB] Synced lyrics ditemukan.")
            print("[CACHE] Disimpan:", filepath)

            return synced_lyrics

        # Jika tidak ada syncedLyrics, gunakan plainLyrics
        plain_lyrics = data.get("plainLyrics")

        if plain_lyrics:
            ensure_folder()

            filename = get_cache_filename(
                artist,
                title,
                ".txt"
            )

            filepath = os.path.join(
                LYRICS_FOLDER,
                filename
            )

            with open(filepath, "w", encoding="utf-8") as file:
                file.write(plain_lyrics)

            print("[LRCLIB] Plain lyrics ditemukan.")
            print("[CACHE] Disimpan:", filepath)

            return plain_lyrics

        print("[LRCLIB] Lirik kosong.")
        return None

    except requests.RequestException as e:
        print("[LRCLIB ERROR]", e)
        return None

    except Exception as e:
        print("[LRCLIB ERROR]", e)
        return None


# ============================================================
# LYRICS.OVH
# ============================================================

def get_lyrics_from_lyrics_ovh(artist, title):
    print("[LYRICS.OVH] Mencari lirik...")

    try:
        # quote() diperlukan agar judul/artis dengan spasi aman
        artist_encoded = quote(artist, safe="")
        title_encoded = quote(title, safe="")

        url = (
            f"{LYRICS_OVH_URL}/"
            f"{artist_encoded}/"
            f"{title_encoded}"
        )

        response = requests.get(
            url,
            headers={
                "User-Agent": "SpotifyLyricsArduino/1.0"
            },
            timeout=10
        )

        if response.status_code != 200:
            print(
                "[LYRICS.OVH] Tidak ditemukan:",
                response.status_code
            )
            return None

        data = response.json()

        lyrics = data.get("lyrics", "").strip()

        if not lyrics:
            print("[LYRICS.OVH] Lirik kosong.")
            return None

        ensure_folder()

        filename = get_cache_filename(
            artist,
            title,
            ".txt"
        )

        filepath = os.path.join(
            LYRICS_FOLDER,
            filename
        )

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(lyrics)

        print("[LYRICS.OVH] Lirik ditemukan.")
        print("[CACHE] Disimpan:", filepath)

        return lyrics

    except requests.RequestException as e:
        print("[LYRICS.OVH ERROR]", e)
        return None

    except Exception as e:
        print("[LYRICS.OVH ERROR]", e)
        return None


# ============================================================
# DATABASE GABUNGAN
# ============================================================

def get_lyrics_from_databases(artist, title):
    """
    Urutan pencarian:

    1. Cache lokal
    2. LRCLIB
    3. lyrics.ovh
    """

    # --------------------------------------------------------
    # CACHE LOKAL
    # --------------------------------------------------------

    local_file = find_local_lyrics(artist, title)

    if local_file:
        print("[CACHE] Menggunakan:", local_file)

        try:
            with open(
                local_file,
                "r",
                encoding="utf-8"
            ) as file:
                return file.read()

        except Exception as e:
            print("[CACHE ERROR]", e)

    # --------------------------------------------------------
    # DATABASE 1: LRCLIB
    # --------------------------------------------------------

    print()
    print("[DATABASE 1/2] LRCLIB")

    lyrics = get_lyrics_from_lrclib(
        artist,
        title
    )

    if lyrics:
        print("[SUCCESS] Lirik ditemukan dari LRCLIB.")
        return lyrics

    # --------------------------------------------------------
    # DATABASE 2: LYRICS.OVH
    # --------------------------------------------------------

    print()
    print("[DATABASE 2/2] lyrics.ovh")

    lyrics = get_lyrics_from_lyrics_ovh(
        artist,
        title
    )

    if lyrics:
        print("[SUCCESS] Lirik ditemukan dari lyrics.ovh.")
        return lyrics

    # --------------------------------------------------------
    # GAGAL
    # --------------------------------------------------------

    print()
    print("[FAILED] Lirik tidak ditemukan di kedua database.")

    return None


# ============================================================
# PARSE LRC ATAU PLAIN TEXT
# ============================================================

def parse_lyrics(text):
    result = []

    if not text:
        return result

    # ========================================================
    # PARSE LRC
    # ========================================================

    pattern = re.compile(
        r"^\[(\d+):(\d+(?:\.\d+)?)\](.*)$"
    )

    has_timestamp = False

    for line in text.splitlines():

        match = pattern.match(line)

        if not match:
            continue

        has_timestamp = True

        minutes = int(match.group(1))
        seconds = float(match.group(2))
        lyric = match.group(3).strip()

        timestamp = minutes * 60 + seconds

        result.append(
            (timestamp, lyric)
        )

    if has_timestamp:
        result.sort(key=lambda x: x[0])
        return result

    # ========================================================
    # PLAIN TEXT
    # ========================================================

    plain_lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        plain_lines.append(line)

    # Karena lyrics.ovh tidak memiliki timestamp,
    # buat timestamp buatan setiap 3 detik.
    for index, line in enumerate(plain_lines):

        timestamp = index * PLAIN_LYRICS_INTERVAL

        result.append(
            (timestamp, line)
        )

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


# ============================================================
# POSISI LAGU
# ============================================================

async def get_position(session):
    """
    Posisi lagu diekstrapolasi berdasarkan waktu yang berlalu
    sejak Windows terakhir kali melaporkan posisi.
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
            now = datetime.datetime.now(
                datetime.timezone.utc
            )

            last_updated = timeline.last_updated_time

            elapsed = (
                now - last_updated
            ).total_seconds()

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
        arduino.write(
            (text + "\n").encode("utf-8")
        )

        arduino.flush()

        print("[LCD]", text)

    except Exception as e:
        print("[SERIAL ERROR]", e)


# ============================================================
# CARI LIRIK SESUAI POSISI
# ============================================================

def get_current_lyric(lyrics, position):
    """
    PATCH: bagian instrumental (belum ada lirik yang mulai, atau
    baris lirik memang kosong seperti "[01:15.00]" tanpa teks -
    penanda instrumental umum di file LRC) sekarang menampilkan
    NOTE_ICON, bukan spasi kosong.
    """

    if not lyrics:
        return ""

    timestamps = [
        lyric[0]
        for lyric in lyrics
    ]

    index = bisect.bisect_right(
        timestamps,
        position
    ) - 1

    # Sebelum baris lirik pertama dimulai -> intro instrumental
    if index < 0:
        return NOTE_ICON

    lyric_text = lyrics[index][1]

    # Baris lirik kosong -> jeda/instrumental di tengah lagu
    if lyric_text == "":
        return NOTE_ICON

    return lyric_text


# ============================================================
# RESET STATUS (dipakai saat tidak ada lagu yang diputar)
# ============================================================

def reset_state():
    """
    FIX: dipanggil saat sesi media hilang (Spotify berhenti/
    ditutup/berpindah ke app lain tanpa media). Sebelumnya
    status lama (sesi, lagu, lirik) tidak pernah dibersihkan,
    jadi LCD bisa menampilkan lirik basi dari lagu sebelumnya.
    """

    send_to_arduino("Menunggu lagu...")

    return None, "", [], None


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

        try:
            now = time.monotonic()

            # ====================================================
            # CEK LAGU BARU
            # ====================================================

            if (
                current_session is None
                or now - last_song_check >= CHECK_SONG_INTERVAL
            ):

                last_song_check = now

                session, title, artist = await get_session()

                if session is not None:

                    song_id = (
                        normalize(artist)
                        + "|"
                        + normalize(title)
                    )

                    # ------------------------------------------------
                    # JIKA LAGU BERUBAH
                    # ------------------------------------------------

                    if song_id != current_song:

                        current_session = session
                        current_song = song_id

                        lyrics = []
                        last_lyric = None

                        print()
                        print("[SONG]", artist, "-", title)

                        send_to_arduino(
                            "Mencari lirik..."
                        )

                        lyrics_text = await asyncio.to_thread(
                            get_lyrics_from_databases,
                            artist,
                            title
                        )

                        if lyrics_text:

                            lyrics = parse_lyrics(
                                lyrics_text
                            )

                            print(
                                "[OK]",
                                len(lyrics),
                                "baris lirik dimuat."
                            )

                            if lyrics:
                                send_to_arduino(
                                    lyrics[0][1]
                                )

                                last_lyric = lyrics[0][1]

                        else:

                            print("[INFO] Tidak ada lirik.")

                            send_to_arduino(
                                "Lirik tidak ditemukan"
                            )

                else:
                    # ------------------------------------------------
                    # FIX: tidak ada sesi media aktif sama sekali
                    # (Spotify ditutup/berhenti/tidak ada apa pun yang
                    # diputar). Bersihkan status lama supaya LCD tidak
                    # nyangkut di lirik/lagu sebelumnya.
                    # ------------------------------------------------

                    if current_session is not None:

                        print()
                        print("[INFO] Tidak ada lagu yang diputar.")

                        (
                            current_session,
                            current_song,
                            lyrics,
                            last_lyric
                        ) = reset_state()

            # ====================================================
            # UPDATE LIRIK
            # ====================================================

            if current_session and lyrics:

                position = await get_position(
                    current_session
                )

                lyric = get_current_lyric(
                    lyrics,
                    position
                )

                if lyric != last_lyric:

                    send_to_arduino(lyric)

                    last_lyric = lyric

            await asyncio.sleep(
                CHECK_POSITION_INTERVAL
            )

        except Exception as e:
            # FIX: bungkus satu iterasi loop dengan try/except supaya
            # error tak terduga (misal Arduino sempat lepas, atau
            # exception dari winrt) tidak menghentikan seluruh program.
            print("[LOOP ERROR]", e)
            await asyncio.sleep(CHECK_POSITION_INTERVAL)


# ============================================================
# START PROGRAM
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