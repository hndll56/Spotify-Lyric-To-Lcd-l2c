#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define LCD_ADDRESS 0x27
#define LCD_COLS 16
#define LCD_ROWS 2

#define SCROLL_INTERVAL_MS 200   // makin kecil, makin cepat gesernya
#define NOTE_COUNT 9             // jumlah not musik dalam satu deret

#define MAX_PAGE_WORDS 24        // batas aman jumlah kata per "halaman" lirik

LiquidCrystal_I2C lcd(LCD_ADDRESS, LCD_COLS, LCD_ROWS);

// =====================================================
// CUSTOM CHARACTER NOT MUSIK
// =====================================================

byte noteChar[] = {
  B00100,
  B00110,
  B00101,
  B00101,
  B00100,
  B01100,
  B11100,
  B01000
};


String receivedText = "";

// Kata-kata yang sedang ditampilkan di "halaman" LCD saat ini.
// Kalau kata baru sudah tidak muat di 2 baris (16x2), halaman
// dibersihkan dan dimulai lagi dari kata itu (BUKAN kata dibuang).
String pageWords[MAX_PAGE_WORDS];
int pageWordCount = 0;

// Pola deret not musik (dibangun sekali di setup()), lalu discroll
// terus-menerus pakai indexing modulo -> loop mulus tanpa batas,
// tidak perlu buffer yang terus tumbuh.
String notePattern = "";
int notePatternLen = 0;
int scrollPos = 0;
unsigned long lastScrollTime = 0;

bool isInstrumental = false;


// =====================================================
// SETUP
// =====================================================

void setup() {
  Serial.begin(115200);

  lcd.init();
  lcd.backlight();
  lcd.clear();

  lcd.createChar(1, noteChar);  // slot 1 (byte 0x00 tidak aman dipakai di dalam String)

  // Bangun deret 9 not musik dipisah spasi, ditambah jeda di akhir
  // supaya satu putaran deret terlihat jelas sebelum mengulang lagi.
  notePattern = "";
  for (int i = 0; i < NOTE_COUNT; i++) {
    notePattern += "\x01";
    notePattern += " ";
  }
  notePattern += "   "; // jeda antar putaran

  notePatternLen = notePattern.length();

  lcd.setCursor(0, 0);
  lcd.print("Spotify Lyrics");

  lcd.setCursor(0, 1);
  lcd.print("Waiting...");
}


// =====================================================
// LOOP
// =====================================================

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      receivedText.trim();

      if (receivedText.length() > 0) {
        setNewLyric(receivedText);
      }

      receivedText = "";
    }
    else if (c != '\r') {
      receivedText += c;
    }
  }

  if (isInstrumental) {
    updateScroll();
  }
}


// =====================================================
// CLEAR LCD
// =====================================================

void clearLine(byte row) {
  lcd.setCursor(0, row);
  lcd.print("                ");
}


// =====================================================
// COBA SUSUN word[0..count-1] JADI 2 BARIS (MAX 16 KOL/BARIS)
// Return true kalau SEMUA kata berhasil ditempatkan (muat).
// Return false kalau ada sisa kata yang tidak muat.
// =====================================================

bool wrapWords(String words[], int count, String &line1, String &line2) {
  line1 = "";
  line2 = "";

  int idx = 0;

  // ---- baris 1 ----
  while (idx < count) {
    String w = words[idx];

    if (line1.length() == 0) {
      if (w.length() > LCD_COLS) {
        return false; // satu kata saja sudah lebih panjang dari layar
      }
      line1 = w;
      idx++;
    }
    else if (line1.length() + 1 + w.length() <= LCD_COLS) {
      line1 += " ";
      line1 += w;
      idx++;
    }
    else {
      break;
    }
  }

  // ---- baris 2 ----
  while (idx < count) {
    String w = words[idx];

    if (line2.length() == 0) {
      if (w.length() > LCD_COLS) {
        return false;
      }
      line2 = w;
      idx++;
    }
    else if (line2.length() + 1 + w.length() <= LCD_COLS) {
      line2 += " ";
      line2 += w;
      idx++;
    }
    else {
      break;
    }
  }

  return idx >= count;
}


// =====================================================
// TAMPILKAN pageWords[0..pageWordCount-1] KE LCD
// =====================================================

void renderPage() {
  String line1, line2;

  wrapWords(pageWords, pageWordCount, line1, line2);

  clearLine(0);
  clearLine(1);

  lcd.setCursor(0, 0);
  lcd.print(line1);

  lcd.setCursor(0, 1);
  lcd.print(line2);
}


// =====================================================
// MULAI HALAMAN BARU DIMULAI DARI SATU KATA
// =====================================================

void startNewPage(String firstWord) {
  pageWordCount = 0;
  pageWords[0] = firstWord;
  pageWordCount = 1;

  renderPage();
}


// =====================================================
// SET LIRIK / KATA BARU
// =====================================================

void setNewLyric(String text) {

  // ===================================================
  // CEK INSTRUMENTAL
  // ===================================================

  if (text.equalsIgnoreCase("INSTRUMENTAL")) {

    if (!isInstrumental) {
      isInstrumental = true;
      pageWordCount = 0;
      scrollPos = 0;

      clearLine(0);
      clearLine(1);

      lcd.setCursor(2, 1);
      lcd.print("Instrumental");
    }

    return;
  }


  // ===================================================
  // PENANDA BARIS LIRIK BARU -> BERSIHKAN, MULAI DARI KOSONG
  // ===================================================

  if (text.equalsIgnoreCase("NEWLINE")) {

    isInstrumental = false;
    pageWordCount = 0;

    clearLine(0);
    clearLine(1);

    return;
  }


  // ===================================================
  // KALAU SEBELUMNYA INSTRUMENTAL, BERSIHKAN DULU
  // ===================================================

  if (isInstrumental) {
    isInstrumental = false;
    pageWordCount = 0;
    scrollPos = 0;

    clearLine(0);
    clearLine(1);
  }


  // ===================================================
  // COBA TAMBAHKAN KATA KE HALAMAN SEKARANG.
  // KALAU SUDAH TIDAK MUAT DI 2 BARIS -> GANTI HALAMAN BARU,
  // LANJUTKAN DARI KATA INI (BUKAN DIBUANG/DIPOTONG).
  // ===================================================

  if (pageWordCount < MAX_PAGE_WORDS) {

    pageWords[pageWordCount] = text;
    int tentativeCount = pageWordCount + 1;

    String line1, line2;
    bool fits = wrapWords(pageWords, tentativeCount, line1, line2);

    if (fits) {
      pageWordCount = tentativeCount;

      clearLine(0);
      clearLine(1);

      lcd.setCursor(0, 0);
      lcd.print(line1);

      lcd.setCursor(0, 1);
      lcd.print(line2);

      return;
    }
  }

  // Tidak muat (atau buffer kata penuh) -> halaman baru
  startNewPage(text);
}


// =====================================================
// UPDATE ANIMASI SCROLL DERET 9 NOT MUSIK (LOOP TERUS)
// =====================================================

void updateScroll() {
  if (millis() - lastScrollTime < SCROLL_INTERVAL_MS) {
    return;
  }

  lastScrollTime = millis();

  String window = "";

  for (int i = 0; i < LCD_COLS; i++) {
    window += notePattern[(scrollPos + i) % notePatternLen];
  }

  lcd.setCursor(0, 0);
  lcd.print(window);

  scrollPos++;

  if (scrollPos >= notePatternLen) {
    scrollPos = 0;
  }
}
