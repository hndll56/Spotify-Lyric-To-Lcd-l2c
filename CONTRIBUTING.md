# Contributing Guide

Terima kasih sudah tertarik mengembangkan proyek ini. Repository ini terbuka untuk fork, modifikasi, perbaikan bug, dan penambahan fitur.

## 1. Fork dan clone

1. Buka repository utama di GitHub.
2. Klik **Fork** untuk membuat salinan di akunmu.
3. Clone fork tersebut ke komputer:

```powershell
git clone https://github.com/USERNAME/Spotify-Lyric-To-Lcd-l2c.git
cd Spotify-Lyric-To-Lcd-l2c
```

## 2. Siapkan environment

Gunakan Python 3.10 atau lebih baru dan Arduino IDE.

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Upload sketch `arduino/lcd_display/lcd_display.ino` ke Arduino. Pastikan baud rate Python dan Arduino sama-sama `115200`.

## 3. Pahami alur program

Program utama berada di `main.py` dan berjalan sebagai satu pipeline:

```text
Spotify Desktop
    -> Windows Media Session
    -> get_session()
    -> get_lyrics_from_databases()
    -> parse_lyrics()
    -> get_current_lyric()
    -> send_to_arduino()
    -> USB Serial
    -> Arduino
    -> LCD I2C
```

### Bagian penting di `main.py`

- Konfigurasi: `PORT`, `BAUDRATE`, folder cache, interval, dan URL API.
- `get_session()`: membaca judul dan artis dari sesi media Windows.
- `get_lyrics_from_databases()`: mencari cache lokal, kemudian LRCLIB, lalu lyrics.ovh.
- `parse_lyrics()`: mengubah LRC menjadi pasangan timestamp dan teks; lirik biasa diberi interval buatan.
- `get_position()`: membaca posisi pemutaran lagu.
- `get_current_lyric()`: memilih lirik berdasarkan posisi lagu dan menampilkan `INSTRUMENTAL` saat perlu.
- `send_to_arduino()`: mengirim satu pesan teks berakhiran newline melalui Serial.
- `main()`: loop utama yang mendeteksi pergantian lagu dan memperbarui LCD.

## 4. Format komunikasi

Python mengirim pesan dalam bentuk teks UTF-8 yang diakhiri `\\n`:

```text
INSTRUMENTAL\\n
```

atau:

```text
teks lirik\\n
```

Arduino membaca pesan sampai newline. Sketch kemudian memecah teks menjadi beberapa bagian, membaginya ke dua baris LCD, dan menggulir bagian yang terlalu panjang.

## 5. Mengubah fitur

### Mengganti port Arduino

Ubah `PORT` di bagian konfigurasi `main.py`.

### Mengganti sumber lirik

Tambahkan fungsi baru dengan pola fungsi `get_lyrics_from_lrclib()` atau `get_lyrics_from_lyrics_ovh()`, lalu panggil dari `get_lyrics_from_databases()`.

### Mengubah tampilan LCD

Edit `arduino/lcd_display/lcd_display.ino`. Bagian yang paling relevan adalah:

- `setNewLyric()` untuk menerima dan memproses pesan.
- `showInstrumental()` untuk tampilan instrumental.
- `showChunk()` untuk membagi teks ke dua baris LCD.
- `MAX_CHUNK_CHARS` dan `CHUNK_DISPLAY_MS` untuk mengatur panjang dan kecepatan scrolling.

### Menambahkan jenis display

Buat sketch Arduino terpisah atau abstraksikan fungsi pengiriman di Python. Jangan mengubah format Serial tanpa memperbarui kedua sisi.

## 6. Pengujian sebelum commit

1. Jalankan `python main.py` dari root repository.
2. Uji lagu dengan lirik tersinkronisasi.
3. Uji lagu tanpa lirik atau dengan lirik plain text.
4. Uji pergantian lagu, pause, dan Spotify ditutup.
5. Pastikan LCD tetap menerima pesan dan tidak ada error Python.

## 7. Pull request

Buat branch fitur, commit perubahan secara terpisah, push ke fork, lalu buka Pull Request ke branch `main` repository utama.

Contoh:

```powershell
git checkout -b fitur-nama-fitur
git add .
git commit -m "Add nama fitur"
git push -u origin fitur-nama-fitur
```

Jelaskan perubahan, alasan perubahan, cara menguji, dan keterbatasan yang masih ada.

## Catatan

Jangan commit `.env.local`, kredensial, atau token. File lirik contoh sebaiknya hanya digunakan untuk pengujian dan harus memperhatikan hak cipta sumber lirik.
