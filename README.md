# Spotify Lyric To LCD I2C

Proyek Python dan Arduino berbasis Windows untuk menampilkan lirik Spotify yang tersinkronisasi pada LCD 16x2 I2C.

**Bahasa:** Bahasa Indonesia | [English](README.en.md)

## Fitur

- Membaca Spotify Desktop melalui Windows Media Session.
- Mengambil lirik LRC dari cache lokal atau LRCLIB.
- Mengirim teks lirik ke Arduino melalui USB Serial.
- Menggulir teks panjang pada LCD.

## Persyaratan

- Windows 10/11
- Python 3.10 atau lebih baru
- Spotify Desktop
- Arduino Uno, Nano, atau Pro Micro
- LCD 1602 dengan modul I2C
- Arduino IDE

## Instalasi Python

### Virtual environment (disarankan)

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Jika PowerShell memblokir aktivasi, gunakan Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

### Tanpa virtual environment

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Konfigurasi

Salin `.env.example` menjadi `.env.local`:

```powershell
Copy-Item .env.example .env.local
```

Contoh isi:

```env
SERIAL_PORT=COM5
BAUD_RATE=115200
LYRICS_FOLDER=lyrics
LRCLIB_URL=https://lrclib.net/api/get
```

Jangan commit `.env.local` ke GitHub.

## Skema Wiring Arduino

Proyek menggunakan **Arduino Uno/Nano + LCD 1602 I2C**. Hanya empat kabel yang diperlukan.

### Arduino Uno

| Pin LCD I2C | Pin Arduino Uno | Fungsi |
|---|---|---|
| GND | GND | Ground |
| VCC | 5V | Catu daya |
| SDA | A4 / SDA | Data I2C |
| SCL | A5 / SCL | Clock I2C |

```text
LCD 1602 I2C                 Arduino Uno
┌─────────────┐              ┌───────────┐
│ GND ────────┼──────────────┤ GND       │
│ VCC ────────┼──────────────┤ 5V        │
│ SDA ────────┼──────────────┤ A4 / SDA  │
│ SCL ────────┼──────────────┤ A5 / SCL  │
└─────────────┘              └───────────┘
```

### Arduino Nano

| Pin LCD I2C | Pin Arduino Nano | Fungsi |
|---|---|---|
| GND | GND | Ground |
| VCC | 5V | Catu daya |
| SDA | A4 | Data I2C |
| SCL | A5 | Clock I2C |

### Catatan wiring

- Gunakan kabel USB **data**, bukan kabel yang hanya untuk mengisi daya.
- Pastikan GND, VCC, SDA, dan SCL tidak tertukar.
- Sketch menggunakan alamat LCD `0x27` dan baud rate `115200`.
- Jika LCD menyala tetapi kosong, cek kontras potentiometer dan alamat I2C.
- Sebagian modul menggunakan alamat `0x3F`. Jika hasil I2C scanner adalah `0x3F`, ubah sketch:

```cpp
#define LCD_ADDRESS 0x3F
```

## Upload Arduino

1. Buka `arduino/lcd_display/lcd_display.ino` di Arduino IDE.
2. Instal library `LiquidCrystal_I2C`.
3. Pilih board Arduino dan port COM yang benar.
4. Hubungkan LCD sesuai skema wiring.
5. Upload sketch.

Sketch menerima pesan Serial pada baud rate `115200`. Setiap pesan harus diakhiri newline (`\n`).

## Menjalankan Program

1. Hubungkan Arduino dan LCD.
2. Upload sketch Arduino.
3. Tutup Serial Monitor agar port COM tidak terkunci.
4. Buka Spotify Desktop dan putar lagu.
5. Buka terminal pada folder repository.
6. Aktifkan `.venv` jika menggunakannya.
7. Jalankan:

```powershell
python main.py
```

## Troubleshooting

- `ModuleNotFoundError`: aktifkan `.venv` atau instal `requirements.txt`.
- `WinError 5: Access is denied: 'lyrics'`: jalankan program dari folder utama repository.
- Arduino tidak terhubung: cek kabel USB data, COM port, baud rate, dan aplikasi lain yang memakai COM port.
- LCD kosong: cek alamat I2C, kontras, VCC, GND, SDA, dan SCL.
- Karakter aneh: pastikan baud rate Python dan Arduino sama-sama `115200`.
- Spotify tidak terdeteksi: gunakan Spotify Desktop, putar lagu, lalu restart Spotify jika perlu.
- Lirik tidak ditemukan: cek koneksi internet atau tambahkan file `.lrc` ke folder `lyrics/`.

## Struktur Proyek

```text
main.py
lyrics/
arduino/lcd_display/lcd_display.ino
requirements.txt
.env.example
```

## Credits

- [LRCLIB](https://lrclib.net) — Data lirik tersinkronisasi.
- [pywinrt](https://github.com/pywinrt/pywinrt) — Windows Runtime dan Windows Media Session.
- [LiquidCrystal_I2C](https://github.com/johnrickman/LiquidCrystal_I2C) — Library LCD I2C Arduino.
- Spotify Desktop — Sumber informasi media.
- Windows Media Session API — Informasi lagu yang sedang aktif.

## Lisensi

MIT License. Lihat file `LICENSE`.

Proyek ini merupakan proyek edukasi independen dan tidak berafiliasi dengan Spotify.
