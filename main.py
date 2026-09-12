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

# FIX: pakai path absolut di sebelah file script ini, bukan folder
# relatif "lyrics" yang tergantung dari mana perintah dijalankan.
# Ini menghindari error "Access is denied" kalau script dijalankan
# dari folder yang izin tulisnya dibatasi Windows/OneDrive/antivirus.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LYRICS_FOLDER = os.path.join(SCRIPT_DIR, "lyrics")

CHECK_SONG_INTERVAL = 0.5
CHECK_POSITION_INTERVAL = 0.02  # dipercepat supaya lebih realtime

# Interval tampilan untuk lirik tanpa timestamp
PLAIN_LYRICS_INTERVAL = 3.0

LRCLIB_URL = "https://lrclib.net/api/get"
LYRICS_OVH_URL = "https://api.lyrics.ovh/v1"

# Dipakai sebagai durasi baris untuk baris TERAKHIR (tidak ada baris
# berikutnya untuk dijadikan patokan jarak).
FALLBACK_LINE_DURATION = 6.0

# ------------------------------------------------------------
# PENJADWALAN KATA (dibuat "seamless" & mengikuti tempo nyanyian,
# bukan menyebar rata ke seluruh jeda sampai baris berikutnya)
# ------------------------------------------------------------

# Perkiraan waktu dasar per kata (detik) -> kira-kira tempo bicara/
# nyanyi normal. Sebelumnya kata disebar rata ke SELURUH jarak
# sampai baris berikutnya (termasuk jeda diam), sehingga terasa
# lambat/ketinggalan dari lagu aslinya. Sekarang kata-kata langsung
# tampil dengan tempo ini, lalu SISA jarak jadi jeda diam menunggu
# baris berikutnya (bukan ikut memperlambat munculnya kata).
# (Sempat dibuat 0.28 lalu dirasa terlalu cepat -> dinaikkan lagi.)
BASE_WORD_TIME = 0.4

# Batas bawah waktu per kata, supaya baris yang padat kata (jarak ke
# baris berikutnya sempit) tetap selesai tampil tepat waktu.
MIN_WORD_TIME = 0.18

NOTE_ICON = "INSTRUMENTAL"

# Penanda ke Arduino: "mulai baris lirik baru, bersihkan layar dan
# mulai bangun kalimat dari kosong lagi".
NEW_LINE_MARKER = "NEWLINE"

# ------------------------------------------------------------
# KOREKSI SINKRONISASI (kalau lirik terasa MENDAHULUI atau TELAT
# dari lagu aslinya).
#
# Ini wajar terjadi berbeda-beda per lagu, karena file LRC di LRCLIB
# itu hasil crowd-source -> tingkat presisi sync-nya beda-beda per
# lagu (ada yang pas, ada yang timestamp-nya sedikit maju). Di luar
# itu, perangkat audio (speaker Bluetooth, dsb) biasanya juga punya
# delay sendiri yang bikin lirik terasa lebih "mendahului" suara asli
# yang kamu dengar.
#
# - Kalau lirik SERING muncul lebih DULU dari suara -> isi angka
#   POSITIF di MANUAL_SYNC_OFFSET (menunda kemunculan lirik).
# - Kalau lirik TELAT -> isi angka NEGATIF (memajukan lirik).
# Satuan detik. Coba mulai dari 0.3-0.5 kalau audio kamu lewat
# Bluetooth (biasanya ada delay bawaan di situ).
#
# Selain itu, kalau file .lrc-nya sendiri punya baris "[offset:xxx]"
# (dalam milidetik), itu otomatis ikut dipakai sebagai koreksi
# tambahan di atas MANUAL_SYNC_OFFSET ini.
# ------------------------------------------------------------
MANUAL_SYNC_OFFSET = 0.0


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
        try:
            os.makedirs(LYRICS_FOLDER)
        except Exception as e:
            print(
                "[ERROR] Gagal membuat folder lirik:",
                LYRICS_FOLDER,
                "-",
                e
            )
            raise


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

    print()
    print("[DATABASE 1/2] LRCLIB")

    lyrics = get_lyrics_from_lrclib(
        artist,
        title
    )

    if lyrics:
        print("[SUCCESS] Lirik ditemukan dari LRCLIB.")
        return lyrics

    print()
    print("[DATABASE 2/2] lyrics.ovh")

    lyrics = get_lyrics_from_lyrics_ovh(
        artist,
        title
    )

    if lyrics:
        print("[SUCCESS] Lirik ditemukan dari lyrics.ovh.")
        return lyrics

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

    pattern = re.compile(
        r"^\[(\d+):(\d+(?:\.\d+)?)\](.*)$"
    )

    # Beberapa file .lrc punya baris metadata "[offset:xxx]" (dalam
    # milidetik) yang menandakan koreksi sinkronisasi bawaan dari
    # file itu sendiri. Kita baca kalau ada, lalu gabungkan dengan
    # MANUAL_SYNC_OFFSET di bawah.
    offset_pattern = re.compile(
        r"^\[offset:\s*([+-]?\d+(?:\.\d+)?)\]",
        re.IGNORECASE
    )

    # Beberapa penyedia lirik punya format "enhanced LRC" yang berisi
    # timestamp PER KATA di dalam baris, contoh:
    #   [00:12.34]nobody <00:12.55>knows <00:12.80>what <00:13.00>i see
    # Kalau format ini ada, kita pakai timestamp aslinya -> kata akan
    # muncul PERSIS mengikuti waktu di lagu (bukan estimasi lagi).
    word_tag_pattern = re.compile(
        r"<(\d+):(\d+(?:\.\d+)?)>"
    )

    def parse_word_level(line_start, content):
        matches = list(word_tag_pattern.finditer(content))

        if not matches:
            return None

        word_times = []

        pre_text = content[:matches[0].start()].strip()

        for word in pre_text.split():
            word_times.append((line_start, word))

        for i, tag in enumerate(matches):
            minutes = int(tag.group(1))
            seconds = float(tag.group(2))
            word_timestamp = minutes * 60 + seconds

            segment_end = (
                matches[i + 1].start()
                if i + 1 < len(matches)
                else len(content)
            )

            segment_text = content[tag.end():segment_end].strip()

            for word in segment_text.split():
                word_times.append((word_timestamp, word))

        return word_times if word_times else None

    embedded_offset_seconds = 0.0

    has_timestamp = False

    for line in text.splitlines():

        offset_match = offset_pattern.match(line)

        if offset_match:
            embedded_offset_seconds = (
                float(offset_match.group(1)) / 1000.0
            )
            continue

        match = pattern.match(line)

        if not match:
            continue

        has_timestamp = True

        minutes = int(match.group(1))
        seconds = float(match.group(2))
        raw_content = match.group(3)

        timestamp = minutes * 60 + seconds

        word_times = parse_word_level(timestamp, raw_content)

        # Teks polos (tanpa tag <mm:ss.xx>) tetap disimpan -> dipakai
        # untuk word-wrap tampilan & deteksi baris kosong/instrumental.
        plain_lyric = word_tag_pattern.sub("", raw_content).strip()

        result.append(
            (timestamp, plain_lyric, word_times)
        )

    if has_timestamp:

        total_offset = embedded_offset_seconds + MANUAL_SYNC_OFFSET

        if total_offset != 0.0:
            adjusted_result = []

            for timestamp, plain_lyric, word_times in result:

                adjusted_word_times = None

                if word_times:
                    adjusted_word_times = [
                        (max(t + total_offset, 0.0), word)
                        for t, word in word_times
                    ]

                adjusted_result.append(
                    (
                        max(timestamp + total_offset, 0.0),
                        plain_lyric,
                        adjusted_word_times
                    )
                )

            result = adjusted_result

        result.sort(key=lambda x: x[0])
        return result

    plain_lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        plain_lines.append(line)

    for index, line in enumerate(plain_lines):

        timestamp = index * PLAIN_LYRICS_INTERVAL

        result.append(
            (timestamp, line, None)
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
# CARI INDEKS BARIS SESUAI POSISI
# ============================================================

def get_current_line_index(lyrics, position):
    if not lyrics:
        return -1

    timestamps = [lyric[0] for lyric in lyrics]

    return bisect.bisect_right(timestamps, position) - 1


# ============================================================
# BUAT JADWAL KATA UNTUK SATU BARIS (REALTIME, BUKAN DIBAGI RATA
# KE SELURUH JEDA SAMPAI BARIS BERIKUTNYA)
# ============================================================

def build_word_schedule(lyrics, index):
    """
    Prioritas 1: kalau baris ini punya timestamp PER KATA asli (format
    enhanced LRC, lihat parse_lyrics), pakai itu langsung -> kata
    muncul PERSIS sesuai waktu di lagu, tidak ada estimasi/delay sama
    sekali.

    Prioritas 2 (fallback, dipakai untuk mayoritas file LRC biasa yang
    cuma punya timestamp per BARIS): kita harus mengira-ngira kapan
    tiap kata muncul, karena datanya memang tidak punya info itu.

    Pendekatan lama: bagi rata jarak-ke-baris-berikutnya ke semua
    kata -> kalau ada jeda diam sebelum baris berikutnya, kata jadi
    ikut disebar pelan dan terasa ketinggalan dari lagu aslinya.

    Pendekatan sekarang: kata muncul dengan tempo tetap (BASE_WORD_TIME,
    diperberat sedikit sesuai panjang kata) -> lebih mendekati tempo
    nyanyian asli dan terasa realtime. Sisa jarak ke baris berikutnya
    (kalau ada) jadi jeda diam menunggu, BUKAN ikut memperlambat
    kemunculan kata.
    """

    line_start, line_text, word_times = lyrics[index]

    if word_times:
        return word_times

    words = line_text.split()

    if not words:
        return []

    if index + 1 < len(lyrics):
        gap = lyrics[index + 1][0] - line_start
    else:
        gap = FALLBACK_LINE_DURATION

    # Jangan sampai kurang dari batas bawah tiap kata, meskipun
    # jarak ke baris berikutnya sangat sempit/negatif (data tidak rapi).
    gap = max(gap, MIN_WORD_TIME * len(words))

    # Bobot tiap kata berdasarkan panjang huruf, supaya kata panjang
    # dapat porsi waktu sedikit lebih besar dari kata pendek.
    weights = [max(len(word), 3) for word in words]
    total_weight = sum(weights)

    estimated_duration = BASE_WORD_TIME * len(words)

    # Pakai yang lebih kecil: jangan lebih lambat dari tempo normal,
    # tapi juga jangan lebih lama dari jarak nyata ke baris berikutnya.
    duration = min(estimated_duration, gap)
    duration = max(duration, MIN_WORD_TIME * len(words))

    schedule = []
    timestamp = line_start

    for word, weight in zip(words, weights):
        word_time = duration * (weight / total_weight)

        schedule.append((timestamp, word))

        timestamp += word_time

    return schedule


# ============================================================
# RESET STATUS (dipakai saat tidak ada lagu yang diputar)
# ============================================================

def reset_state():
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

    # Status khusus mode scroll (per-kata).
    # PENTING: pakai None sebagai nilai awal (bukan -1), karena -1
    # adalah nilai index yang VALID (artinya "sebelum lirik pertama
    # / instrumental intro"). Kalau nilai awal ini juga -1, saat lagu
    # baru dimulai dengan intro instrumental maka index pertama yang
    # terdeteksi (-1) akan dianggap "tidak berubah" dari nilai awal,
    # sehingga penanda INSTRUMENTAL tidak pernah terkirim dan layar
    # nyangkut di "Mencari lirik...". Dengan None, perubahan index
    # apa pun (termasuk ke -1) pasti terdeteksi sebagai baru.
    current_line_index = None
    word_schedule = []
    word_pointer = 0

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

                    if song_id != current_song:

                        current_session = session
                        current_song = song_id

                        lyrics = []
                        last_lyric = None

                        current_line_index = None
                        word_schedule = []
                        word_pointer = 0

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

                        else:

                            print("[INFO] Tidak ada lirik.")

                            send_to_arduino(
                                "Lirik tidak ditemukan"
                            )

                else:
                    if current_session is not None:

                        print()
                        print("[INFO] Tidak ada lagu yang diputar.")

                        (
                            current_session,
                            current_song,
                            lyrics,
                            last_lyric
                        ) = reset_state()

                        current_line_index = None
                        word_schedule = []
                        word_pointer = 0

            # ====================================================
            # UPDATE LIRIK
            # ====================================================

            if current_session and lyrics:

                position = await get_position(
                    current_session
                )

                index = get_current_line_index(lyrics, position)

                # ------------------------------------------------
                # BARIS BERGANTI -> SIAPKAN JADWAL KATA BARU
                # ------------------------------------------------

                if index != current_line_index:

                    current_line_index = index

                    if index < 0 or lyrics[index][1] == "":
                        # Intro sebelum lirik pertama, atau baris
                        # kosong -> instrumental
                        word_schedule = [(position, NOTE_ICON)]
                    else:
                        # Kirim penanda baris baru dulu supaya Arduino
                        # bersihkan layar sebelum kata pertama datang
                        send_to_arduino(NEW_LINE_MARKER)

                        word_schedule = build_word_schedule(
                            lyrics,
                            index
                        )

                    word_pointer = 0

                # ------------------------------------------------
                # KIRIM KATA YANG JADWALNYA SUDAH LEWAT
                # ------------------------------------------------

                while (
                    word_pointer < len(word_schedule)
                    and position >= word_schedule[word_pointer][0]
                ):

                    word_to_send = word_schedule[word_pointer][1]

                    send_to_arduino(word_to_send)

                    word_pointer += 1

            await asyncio.sleep(
                CHECK_POSITION_INTERVAL
            )

        except Exception as e:
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