# Dokumentasi Proyek Spotify Lyric To LCD I2C

## 1. Identitas Proyek

**Nama Proyek:** Spotify Lyric To LCD I2C

**Jenis Proyek:** Internet of Things (IoT), Embedded System, dan Desktop Automation.

**Platform:**
- Windows
- Spotify Desktop
- Python
- Arduino Uno/Nano
- LCD I2C 16x2

Proyek ini dibuat untuk menghubungkan aplikasi Spotify Desktop dengan perangkat Arduino. Informasi lagu yang sedang diputar akan diproses oleh program Python, kemudian lirik lagu dikirim melalui komunikasi serial USB dan ditampilkan pada LCD I2C 16x2.

---

# 2. Latar Belakang

Pada umumnya, lirik lagu ditampilkan melalui layar komputer atau smartphone. Proyek ini mencoba membuat alternatif sederhana menggunakan perangkat keras mikrokontroler.

Dengan memanfaatkan Spotify Desktop dan Arduino, pengguna dapat menampilkan lirik lagu pada LCD kecil tanpa harus terus melihat layar komputer.

Proyek ini juga menjadi contoh penerapan beberapa teknologi secara bersamaan, yaitu:

- Pemrograman Python.
- Pengambilan data dari aplikasi desktop.
- Pemrosesan teks.
- Komunikasi Serial.
- Mikrokontroler Arduino.
- LCD I2C.
- Git dan GitHub.

---

# 3. Tujuan Proyek

Tujuan utama proyek ini adalah:

1. Membaca informasi lagu yang sedang diputar di Spotify Desktop.
2. Mengambil lirik lagu secara otomatis.
3. Mengolah lirik agar sesuai dengan ukuran LCD 16x2.
4. Mengirimkan data dari komputer ke Arduino melalui USB Serial.
5. Menampilkan lirik pada LCD I2C.
6. Membuat sistem yang dapat diperbarui secara otomatis ketika lagu berganti.

---

# 4. Cara Kerja Sistem

Sistem bekerja menggunakan beberapa tahap.

```text
Spotify Desktop
      |
      v
Windows Media Session API
      |
      v
Program Python
      |
      +--> Membaca judul lagu dan artis
      |
      +--> Mencari lirik lagu
      |
      +--> Memformat teks menjadi dua baris
      |
      v
USB Serial Communication
      |
      v
Arduino Uno/Nano
      |
      v
LCD I2C 16x2
```

### Penjelasan Alur

#### Tahap 1: Spotify Desktop

Pengguna memutar lagu melalui Spotify Desktop pada komputer Windows.

Informasi yang dibutuhkan meliputi:

* Judul lagu.
* Nama artis.
* Status pemutaran lagu.

#### Tahap 2: Windows Media Session API

Program Python menggunakan Windows Media Session API untuk membaca metadata media yang sedang aktif pada Windows.

API ini memungkinkan program mengetahui informasi lagu tanpa harus mengambil data langsung dari tampilan Spotify.

#### Tahap 3: Program Python

Python berfungsi sebagai pusat pengendali sistem.

Tugas utama Python:

* Membaca lagu yang sedang diputar.
* Mendeteksi perubahan lagu.
* Mengambil lirik.
* Memotong dan mengatur teks.
* Mengirim data ke Arduino.

#### Tahap 4: Pencarian Lirik

Setelah judul dan artis diketahui, program mencari lirik menggunakan lyrics API atau sumber lirik yang telah dikonfigurasi.

Contoh data:

```text
Title  : Bohemian Rhapsody
Artist : Queen
```

Kemudian program mengambil lirik yang sesuai dengan lagu tersebut.

#### Tahap 5: Komunikasi Serial

Python mengirim data melalui kabel USB yang terhubung ke Arduino.

Format data yang digunakan:

```text
baris pertama|baris kedua\n
```

Contoh:

```text
Is this the real life?|Is this just fantasy?\n
```

Karakter `|` digunakan sebagai pemisah antara baris pertama dan baris kedua LCD.

Karakter `\n` digunakan sebagai tanda bahwa satu pesan telah selesai dikirim.

#### Tahap 6: Arduino dan LCD

Arduino menerima data melalui Serial Monitor USB.

Arduino kemudian:

1. Membaca pesan sampai karakter newline.
2. Mencari karakter pemisah `|`.
3. Memisahkan teks menjadi dua bagian.
4. Membersihkan layar LCD.
5. Menampilkan teks pada baris pertama dan kedua.

---

# 5. Komponen Hardware

Komponen yang digunakan:

| No. | Komponen         | Fungsi                              |
| --- | ---------------- | ----------------------------------- |
| 1   | Arduino Uno/Nano | Mikrokontroler pengendali LCD       |
| 2   | LCD 16x2 I2C     | Menampilkan lirik lagu              |
| 3   | Kabel USB        | Komunikasi komputer dengan Arduino  |
| 4   | Kabel jumper     | Menghubungkan komponen              |
| 5   | Breadboard       | Media perakitan rangkaian, opsional |

---

# 6. Wiring Hardware

LCD I2C dihubungkan ke Arduino Uno atau Nano sebagai berikut:

| Pin LCD I2C | Pin Arduino Uno/Nano |
| ----------- | -------------------- |
| VCC         | 5V                   |
| GND         | GND                  |
| SDA         | A4                   |
| SCL         | A5                   |

Diagram sederhana:

```text
LCD I2C              Arduino Uno/Nano
--------             ----------------
VCC       ----------> 5V
GND       ----------> GND
SDA       ----------> A4
SCL       ----------> A5
```

LCD I2C umumnya memiliki alamat:

```text
0x27
```

atau:

```text
0x3F
```

Alamat tersebut dapat berbeda tergantung modul I2C yang digunakan.

Jika LCD menyala tetapi tidak menampilkan teks, alamat I2C perlu diperiksa menggunakan program I2C Scanner.

---

# 7. Komponen Software

Software yang digunakan:

| Software        | Fungsi                                 |
| --------------- | -------------------------------------- |
| Windows         | Sistem operasi utama                   |
| Spotify Desktop | Sumber informasi lagu                  |
| Python          | Membaca lagu dan mengambil lirik       |
| Arduino IDE     | Meng-upload program ke Arduino         |
| VSCodium        | Editor kode dan manajemen proyek       |
| Git             | Version control                        |
| GitHub          | Penyimpanan repository dan dokumentasi |

---

# 8. Struktur Repository

Struktur repository yang disarankan:

```text
spotify-lyric-to-lcd-i2c/
│
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
│
├── python/
│   ├── main.py
│   ├── spotify_monitor.py
│   ├── lyrics_fetcher.py
│   └── serial_display.py
│
├── arduino/
│   └── spotify_lcd/
│       └── spotify_lcd.ino
│
└── docs/
    └── dokumentasi.md
```

---

# 9. Penjelasan Struktur Program

## 9.1 `main.py`

Merupakan program utama yang mengatur seluruh proses.

Tugasnya:

1. Menjalankan monitoring Spotify.
2. Mengambil lagu yang sedang diputar.
3. Mendeteksi jika lagu berubah.
4. Memanggil lyrics fetcher.
5. Mengirim lirik ke Arduino.

Alur sederhananya:

```python
while True:
    current_song = get_current_song()

    if current_song_changed(current_song):
        lyrics = fetch_lyrics(
            current_song["title"],
            current_song["artist"]
        )

        send_to_arduino(lyrics)

    sleep(1)
```

---

## 9.2 `spotify_monitor.py`

File ini bertanggung jawab membaca metadata lagu dari Spotify Desktop melalui Windows Media Session API.

Data yang diharapkan:

```python
{
    "title": "Judul Lagu",
    "artist": "Nama Artis"
}
```

Fungsi utama yang dapat digunakan:

```python
get_current_song()
```

Fungsi ini sebaiknya mengembalikan data kosong atau `None` jika tidak ada lagu yang sedang diputar.

---

## 9.3 `lyrics_fetcher.py`

File ini digunakan untuk mengambil lirik berdasarkan judul lagu dan nama artis.

Fungsi utama:

```python
fetch_lyrics(title, artist)
```

Tugasnya:

* Mengirim permintaan ke lyrics API.
* Membaca respons API.
* Mengambil teks lirik.
* Menangani error.
* Mengembalikan hasil yang dapat diproses oleh program utama.

Contoh:

```python
lyrics = fetch_lyrics(
    "Bohemian Rhapsody",
    "Queen"
)
```

---

## 9.4 `serial_display.py`

File ini menangani komunikasi Python dengan Arduino.

Fungsi utama:

```python
send_to_arduino(text)
```

Contoh data yang dikirim:

```text
Hello world      |This is a test
```

Pada implementasi sebenarnya, data harus menggunakan karakter pemisah:

```text
Hello world|This is a test\n
```

Baud rate yang digunakan harus sama antara Python dan Arduino.

Contoh:

```python
SERIAL_PORT = "COM3"
BAUD_RATE = 9600
```

---

## 9.5 `spotify_lcd.ino`

Program Arduino bertugas menerima data dari Python dan menampilkan data tersebut ke LCD.

Logika dasarnya:

```cpp
if (Serial.available()) {
    String data = Serial.readStringUntil('\n');

    int separator = data.indexOf('|');

    String line1 = data.substring(0, separator);
    String line2 = data.substring(separator + 1);

    lcd.clear();

    lcd.setCursor(0, 0);
    lcd.print(line1);

    lcd.setCursor(0, 1);
    lcd.print(line2);
}
```

---

# 10. Dependency Python

Dependency yang diperlukan dapat disimpan dalam file:

```text
requirements.txt
```

Contoh isi:

```text
winrt-runtime
winrt-Windows.Foundation
winrt-Windows.Media
winrt-Windows.Media.Control
pyserial
requests
```

Instalasi dependency:

```powershell
pip install -r requirements.txt
```

Disarankan menggunakan virtual environment:

```powershell
python -m venv .venv
```

Aktivasi pada Windows:

```powershell
.venv\Scripts\activate
```

---

# 11. Instalasi dan Persiapan

## Langkah 1: Clone Repository

```powershell
git clone https://github.com/USERNAME/spotify-lyric-to-lcd-i2c.git
```

Masuk ke folder project:

```powershell
cd spotify-lyric-to-lcd-i2c
```

## Langkah 2: Membuat Virtual Environment

```powershell
python -m venv .venv
```

Aktifkan:

```powershell
.venv\Scripts\activate
```

## Langkah 3: Install Dependency

```powershell
pip install -r requirements.txt
```

## Langkah 4: Menyiapkan Arduino

1. Buka Arduino IDE.
2. Buka file:

```text
arduino/spotify_lcd/spotify_lcd.ino
```

3. Pilih board Arduino yang digunakan.
4. Pilih COM Port Arduino.
5. Pastikan library LCD I2C telah terpasang.
6. Upload program ke Arduino.

## Langkah 5: Menghubungkan Hardware

Hubungkan LCD I2C ke Arduino sesuai wiring.

Kemudian hubungkan Arduino ke komputer menggunakan kabel USB.

## Langkah 6: Menentukan COM Port

Periksa COM Port melalui Device Manager Windows.

Contoh:

```text
COM3
```

Sesuaikan konfigurasi Python:

```python
SERIAL_PORT = "COM3"
```

---

# 12. Cara Menjalankan Program

Pastikan:

* Spotify Desktop sedang terbuka.
* Ada lagu yang sedang diputar.
* Arduino terhubung ke komputer.
* LCD mendapatkan daya.
* COM Port telah benar.
* Dependency Python telah terpasang.

Jalankan program:

```powershell
python python/main.py
```

Jika program berhasil:

1. Python membaca lagu dari Spotify.
2. Judul dan artis diproses.
3. Lirik dicari.
4. Data dikirim melalui USB Serial.
5. Arduino menampilkan lirik pada LCD.

---

# 13. Format Komunikasi Serial

Format komunikasi antara Python dan Arduino:

```text
LINE1|LINE2\n
```

Contoh:

```text
Hello from Spotify|Arduino LCD Display\n
```

Penjelasan:

| Bagian  | Fungsi                       |                   |
| ------- | ---------------------------- | ----------------- |
| `LINE1` | Teks untuk baris pertama LCD |                   |
| `       | `                            | Pemisah dua baris |
| `LINE2` | Teks untuk baris kedua LCD   |                   |
| `\n`    | Penanda akhir pesan          |                   |

Karena LCD hanya memiliki lebar 16 karakter, teks yang terlalu panjang harus dipotong atau dibagi menjadi beberapa bagian.

---

# 14. Pengolahan Teks Lirik

LCD 16x2 memiliki keterbatasan:

* Hanya 2 baris.
* Setiap baris maksimal 16 karakter.
* Tidak semua karakter Unicode dapat ditampilkan dengan sempurna.

Oleh karena itu, sistem perlu melakukan formatting teks.

Contoh lirik panjang:

```text
Is this the real life, is this just fantasy
```

Dapat dibagi menjadi:

```text
Is this the real
life, is this
```

Atau ditampilkan menggunakan scrolling text.

Fitur scrolling dapat dikembangkan pada tahap berikutnya.

---

# 15. Penanganan Error

Program sebaiknya menangani beberapa kondisi berikut:

## Spotify Tidak Sedang Memutar Lagu

Jika tidak ada lagu yang aktif, program tidak perlu mengirim data baru ke Arduino.

LCD dapat menampilkan:

```text
Spotify Paused
No song playing
```

## Lirik Tidak Ditemukan

Jika API tidak menemukan lirik:

```text
Lyrics not found
```

## Internet Tidak Tersedia

Jika koneksi internet gagal, program sebaiknya tidak berhenti secara tiba-tiba.

Contoh:

```text
Connection error
Retrying...
```

## Arduino Tidak Terhubung

Jika COM Port tidak ditemukan atau sedang digunakan program lain, Python harus menampilkan pesan error yang jelas.

Contoh:

```text
Unable to connect to Arduino on COM3
```

---

# 16. Keamanan API Key

Jika program menggunakan API key, token, atau kredensial lainnya, data tersebut tidak boleh dimasukkan langsung ke GitHub.

Gunakan file `.env` untuk menyimpan konfigurasi lokal.

Contoh:

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
LYRICS_API_KEY=your_api_key
```

Tambahkan `.env` ke `.gitignore`:

```gitignore
.env
```

Yang boleh di-upload adalah:

```text
.env.example
```

Contoh:

```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
LYRICS_API_KEY=your_api_key_here
```

---

# 17. Troubleshooting

## LCD Tidak Menampilkan Tulisan

Periksa:

* VCC terhubung ke 5V.
* GND terhubung ke GND.
* SDA terhubung ke A4.
* SCL terhubung ke A5.
* Alamat I2C sudah benar.
* Kontras LCD sudah diatur.

## LCD Menyala tetapi Hanya Kotak Hitam

Kemungkinan penyebab:

* Alamat I2C salah.
* Library LCD tidak sesuai.
* Kontras terlalu tinggi atau terlalu rendah.
* Kabel SDA/SCL bermasalah.

## Arduino Tidak Menerima Data

Periksa:

* Kabel USB mendukung transfer data.
* COM Port benar.
* Baud rate sama.
* Tidak ada aplikasi lain yang memakai COM Port.

## Python Tidak Membaca Spotify

Periksa:

* Spotify Desktop sedang berjalan.
* Lagu sedang diputar.
* Dependency WinRT sudah terpasang.
* Python menggunakan versi yang kompatibel dengan library yang digunakan.

## Lirik Tidak Muncul

Periksa:

* Judul lagu dan artis terbaca dengan benar.
* API lirik dapat diakses.
* Koneksi internet tersedia.
* Lagu memiliki data lirik pada sumber yang digunakan.

---

# 18. Pengembangan Selanjutnya

Fitur yang dapat ditambahkan:

1. Scrolling teks otomatis.
2. Sinkronisasi lirik berdasarkan waktu lagu.
3. Deteksi pause dan resume Spotify.
4. Deteksi pergantian lagu secara lebih cepat.
5. Dukungan OLED display.
6. Dukungan LCD dengan ukuran lebih besar.
7. GUI untuk konfigurasi COM Port.
8. Deteksi COM Port Arduino otomatis.
9. Cache lirik agar tidak selalu meminta API.
10. Dukungan berbagai sumber lirik.
11. Animasi teks pada LCD.
12. Pengaturan kecepatan scrolling.

---

# 19. Manfaat Pembelajaran

Proyek ini dapat digunakan untuk mempelajari:

* Dasar Python.
* Pemrograman Arduino.
* Komunikasi Serial UART.
* Protokol I2C.
* Penggunaan API.
* Pengambilan data dari aplikasi desktop.
* Pemrosesan string dan teks.
* Manajemen dependency Python.
* Version control menggunakan Git.
* Publikasi proyek menggunakan GitHub.

---

# 20. Kesimpulan

Spotify Lyric To LCD I2C adalah proyek integrasi antara software dan hardware yang memanfaatkan Spotify Desktop, Python, Arduino, dan LCD I2C.

Python bertindak sebagai penghubung antara komputer dan Arduino. Python membaca lagu yang sedang diputar, mengambil lirik, lalu mengirimkan data melalui USB Serial. Arduino menerima data tersebut dan menampilkannya pada LCD 16x2.

Proyek ini merupakan contoh sederhana bagaimana perangkat lunak desktop dapat berkomunikasi dengan mikrokontroler untuk menghasilkan perangkat elektronik yang interaktif.