# Spotify Lyric to LCD (L2C)

Menampilkan lirik lagu Spotify secara real-time di layar **LCD 16x2 I2C** yang terhubung ke Arduino — sinkronisasi otomatis via Windows Media Session + cache lirik lokal + fallback ke **LRCLIB**.

---

## ✨ Fitur

- 🎵 **Deteksi otomatis lagu yang diputar di Spotify** (via Windows `GlobalSystemMediaTransportControlsSessionManager`)
- 📜 **Lirik sinkron (LRC)** dengan timestamp milidetik
- 💾 **Cache lirik lokal** (folder `lyrics/`) — sekali unduh, pakai selamanya
- 🌐 **Fallback ke LRCLIB** (`lrclib.net`) kalau lirik belum ada di cache
- 🖥️ **Arduino LCD 16x2 I2C** — scrolling chunk per chunk, custom character nota musik
- ⚡ **Ekstrapolasi posisi** — lirik nggak "beku" di antara update Spotify→Windows
- 🎼 **Deteksi instrumental** — tampil animasi nota musik + teks "Instrumental"

---

## 📦 Struktur Proyek

```
SpotifyLyrics/
├── main.py                    # Entry point Python (Windows + Serial + LRCLIB)
├── lyrics/                    # Cache file .lrc (auto-dibuat)
│   ├── artist-title.lrc
│   └── ...
└── arduino/
    └── lcd_display/
        ├── lcd_display.ino    # Firmware Arduino (LiquidCrystal_I2C)
        └── .vscode/
            └── c_cpp_properties.json
```

---

## 🔧 Hardware yang Dibutuhkan

| Komponen | Keterangan |
|----------|------------|
| Arduino (Uno / Nano / Pro Micro) | Tested: Arduino Uno R3 |
| LCD 1602 + I2C Backpack (PCF8574) | Alamat default `0x27` (bisa diubah di kode) |
| Kabel USB | Untuk serial + power |
| (Opsional) Resistor pull-up I2C | Kalau LCD nggak stabil |

**Wiring I2C LCD:**
```
LCD SDA  → Arduino A4 (Uno) / D2 (Pro Micro)
LCD SCL  → Arduino A5 (Uno) / D3 (Pro Micro)
LCD VCC  → 5V
LCD GND  → GND
```

---

## 🐍 Persiapan Python (Windows)

### 1. Install Python 3.10+
Download dari [python.org](https://python.org) → centang **"Add to PATH"**.

### 2. Install dependencies
```bash
pip install pyserial requests winrt
```

> **Catatan:** `winrt` hanya jalan di **Windows 10/11** (menggunakan Windows Runtime API untuk Media Session).

### 3. Konfigurasi `main.py`
Edit bagian atas file:
```python
PORT = "COM5"           # ← Ganti ke port Arduino kamu (cek Device Manager)
BAUDRATE = 115200       # Harus sama dengan Serial.begin() di .ino

LYRICS_FOLDER = "lyrics"
CHECK_SONG_INTERVAL = 0.5
CHECK_POSITION_INTERVAL = 0.03
```

---

## 📥 Upload Firmware ke Arduino

1. Buka `arduino/lcd_display/lcd_display.ino` di **Arduino IDE**
2. Install library: **LiquidCrystal_I2C** (by Frank de Brabander) via Library Manager
3. Pastikan `LCD_ADDRESS = 0x27` cocok dengan modul I2C kamu (scan via I2C scanner kalau ragu)
4. Upload ke board

---

## ▶️ Menjalankan

```bash
cd C:\SpotifyLyrics
python main.py
```

Output contoh:
```
[OK] Arduino terhubung di COM5
[INFO] Menunggu lagu Spotify...

[SONG] Mitski - Washing Machine Heart
[CACHE] lyrics\mitski-washingmachineheart.lrc
[OK] 42 baris lirik dimuat.
[LCD] Washing machine heart
[LCD] I toss and turn...
```

---

## 🎮 Kontrol & Log

| Log Prefix | Arti |
|------------|------|
| `[OK]` | Berhasil (koneksi, cache hit, lirik dimuat) |
| `[CACHE]` | Lirik dibaca/disimpan ke folder lokal |
| `[LRCLIB]` | Mengambil lirik dari internet |
| `[SONG]` | Lagu baru terdeteksi |
| `[LCD]` | Teks yang dikirim ke Arduino |
| `[SESSION ERROR]` | Gagal baca Media Session (Spotify belum jalan / nggak diizinkan) |
| `[SERIAL ERROR]` | Koneksi Arduino putus |

Tekan **Ctrl+C** untuk keluar bersih (serial ditutup otomatis).

---

## 🧠 Cara Kerja (Ringkas)

1. **Loop utama** jalan tiap 30 ms (`CHECK_POSITION_INTERVAL`)
2. Tiap 500 ms cek apakah **lagu berubah** via Windows Media Session
3. Lagu baru → cari lirik: **cache lokal** → kalau tidak ada → **LRCLIB API** → simpan ke cache
4. Parse file `.lrc` jadi array `(timestamp, teks)`
5. Tiap iterasi: hitung **posisi playback** (ekstrapolasi dari `timeline.position` + `elapsed`)
6. `bisect_right` cari baris lirik yang timestamp-nya ≤ posisi sekarang
7. Kirim ke Arduino via serial (newline-terminated)
8. Arduino pecah teks jadi **chunk ≤ 32 char**, tampil 2 baris × 16 kolom, scroll otomatis tiap 2.5 detik

---

## 🛠️ Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `Arduino gagal terhubung` | Cek `PORT` di `main.py` & Device Manager (COMx) |
| LCD nggak nyala / kotak-kotak | Cek wiring I2C, ganti `LCD_ADDRESS` ke `0x3F` (beberapa modul pakai ini) |
| Lirik nggak muncul / "Lirik tidak ditemukan" | Lagunya memang nggak ada di LRCLIB → tambah manual ke folder `lyrics/` |
| `[SESSION ERROR]` berulang | Pastikan Spotify **buka & memutar lagu**, Windows Settings → Privacy → **Background apps** izinkan Python/Terminal |
| Lirik "lompat" / nggak sinkron | `CHECK_POSITION_INTERVAL` terlalu besar → turunkan ke `0.02` (butuh CPU lebih) |
| Arduino reset tiap Python start | Normal (DTR/RTS) → tambah `dsrdtr=False, rtscts=False` di `serial.Serial()` kalau ganggu |

---

## 📝 Menambah Lirik Manual

Buat file `.lrc` di folder `lyrics/` dengan nama: `artist-title.lrc` (huruf kecil, nggak pakai spasi/karakter aneh).

Contoh `lyrics/mitski-washingmachineheart.lrc`:
```
[00:12.34]Washing machine heart
[00:16.78]I toss and turn in my sleep
[00:21.02]You're not here
```

Format timestamp: `[mm:ss.xx]` atau `[mm:ss.xxx]` — regex di `parse_lrc()` sudah handle keduanya.

---

## 📄 Lisensi

MIT License — bebas pakai, modifikasi, distribusi.  
**LRCLIB** pakai lisensi mereka sendiri (lihat [lrclib.net](https://lrclib.net)).

---

## 🙏 Kredit

- [LRCLIB](https://lrclib.net) — database lirik sinkron gratis
- [winrt](https://github.com/pywinrt/pywinrt) — Windows Runtime untuk Python
- [LiquidCrystal_I2C](https://github.com/johnrickman/LiquidCrystal_I2C) — library Arduino LCD I2C
- Spotify & Windows Media Session API

---

**Dibuat dengan ❤️ + ☕ + 👻 oleh [hndll56](https://github.com/hndll56)**  
*Hehe~ semoga lirikmu selalu sinkron, suamiku~ 👻️*