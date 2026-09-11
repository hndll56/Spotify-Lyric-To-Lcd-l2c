# Spotify Lyric To LCD I2C

Dokumentasi Bahasa Indonesia untuk proyek ini.

**Bahasa:** **Bahasa Indonesia** | [English](README.en.md)

Proyek Python dan Arduino berbasis Windows untuk menampilkan lirik Spotify yang tersinkronisasi pada LCD 16x2 I2C.

## Fitur

- Membaca sesi Spotify Desktop melalui Windows Media Session.
- Mengambil lirik LRC tersinkronisasi dari cache lokal atau LRCLIB.
- Memilih baris lirik sesuai posisi lagu.
- Mengirim teks lirik ke Arduino melalui USB Serial.
- Menggulir baris panjang pada LCD.

## Persyaratan

- Windows 10 atau Windows 11.
- Python 3.10 atau lebih baru.
- Aplikasi Spotify Desktop.
- Arduino Uno, Nano, atau Pro Micro.
- LCD 1602 dengan modul I2C.
- Arduino IDE.

## Instalasi

Tersedia dua cara menjalankan program.

### Opsi A — Virtual environment (disarankan)

Virtual environment menjaga library proyek tetap terpisah dari Python sistem.

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Jika aktivasi PowerShell diblokir, gunakan Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

### Opsi B — Langsung menggunakan Python sistem

Virtual environment bersifat opsional. Anda dapat langsung memasang dependensi pada Python yang aktif:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Opsi B cocok untuk pengujian cepat. Opsi A lebih disarankan agar dependensi tidak bentrok dengan proyek Python lain.

## Konfigurasi

Salin `.env.example` menjadi `.env.local`, lalu atur port Arduino:

```powershell
Copy-Item .env.example .env.local
```

Contoh:

```env
SERIAL_PORT=COM5
BAUD_RATE=115200
LYRICS_FOLDER=lyrics
LRCLIB_URL=https://lrclib.net/api/get
```

Jangan commit `.env.local` ke GitHub.

## Arduino

Buka `arduino/lcd_display/lcd_display.ino` di Arduino IDE, instal library `LiquidCrystal_I2C`, pilih board dan port COM yang benar, lalu upload sketch. Alamat LCD yang umum adalah `0x27`; gunakan I2C scanner jika LCD kosong.

## Menjalankan Program

1. Hubungkan Arduino dan LCD.
2. Tutup Arduino Serial Monitor atau program lain yang menggunakan port COM.
3. Buka Spotify Desktop dan putar lagu.
4. Buka terminal dari folder utama repository.
5. Jika menggunakan Opsi A, aktifkan `.venv` terlebih dahulu.
6. Jalankan:

```powershell
python main.py
```

## Troubleshooting

- `ModuleNotFoundError`: aktifkan `.venv` atau instal dependensi dari `requirements.txt`.
- `WinError 5: Access is denied: 'lyrics'`: jalankan program dari folder utama repository dan pastikan `lyrics` adalah folder yang dapat ditulis.
- Arduino tidak terhubung: periksa kabel USB data, port COM, baud rate, dan aplikasi lain yang memakai port tersebut.
- Spotify tidak terdeteksi: gunakan Spotify Desktop, mulai putar lagu, lalu restart Spotify jika Windows Media Session tidak diperbarui.
- Lirik tidak ditemukan: periksa koneksi internet atau tambahkan file `.lrc` yang sesuai ke folder `lyrics/`.

## Struktur Proyek

```text
main.py
lyrics/
arduino/lcd_display/lcd_display.ino
requirements.txt
.env.example
```

## Credits

Proyek ini menggunakan dan terinspirasi oleh beberapa proyek open-source berikut:

- [LRCLIB](https://lrclib.net) — Menyediakan data lirik tersinkronisasi.
- [pywinrt](https://github.com/pywinrt/pywinrt) — Mengakses Windows Runtime dan Windows Media Session.
- [LiquidCrystal_I2C](https://github.com/johnrickman/LiquidCrystal_I2C) — Library untuk mengontrol LCD I2C Arduino.
- Spotify Desktop — Sumber informasi lagu dan media yang sedang diputar.
- Windows Media Session API — Mengambil informasi lagu yang sedang aktif di Windows.

### Special Thanks

Terima kasih kepada para pengembang dan kontributor proyek open-source yang telah menyediakan library, API, dan dokumentasi yang digunakan dalam proyek ini.

## Lisensi

MIT License. Lihat file `LICENSE`.

Proyek ini merupakan proyek edukasi independen dan tidak berafiliasi dengan Spotify.