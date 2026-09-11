#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define LCD_ADDRESS 0x27
#define LCD_COLS 16
#define LCD_ROWS 2

#define MAX_CHUNK_CHARS 32
#define CHUNK_DISPLAY_MS 2500

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
String chunks[10];

int totalChunks = 0;
int currentChunk = 0;

unsigned long lastChunkTime = 0;


// =====================================================
// SETUP
// =====================================================

void setup() {
  Serial.begin(115200);

  lcd.init();
  lcd.backlight();
  lcd.clear();

  // Buat karakter not musik
  lcd.createChar(0, noteChar);

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

  if (totalChunks > 1 &&
      millis() - lastChunkTime >= CHUNK_DISPLAY_MS) {

    currentChunk++;

    if (currentChunk >= totalChunks) {
      currentChunk = 0;
    }

    showChunk(currentChunk);
    lastChunkTime = millis();
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
// SET LIRIK BARU
// =====================================================

void setNewLyric(String text) {

  // ===================================================
  // CEK INSTRUMENTAL
  // ===================================================

  if (text.equalsIgnoreCase("INSTRUMENTAL")) {

    totalChunks = 1;
    currentChunk = 0;
    chunks[0] = "";

    showInstrumental();

    lastChunkTime = millis();

    return;
  }


  // ===================================================
  // KODE LIRIK LAMA
  // ===================================================

  totalChunks = 0;
  currentChunk = 0;

  String words[30];
  int wordCount = 0;

  int startIndex = 0;

  while (startIndex < text.length()) {
    int spaceIndex = text.indexOf(' ', startIndex);

    if (spaceIndex == -1) {
      spaceIndex = text.length();
    }

    String word = text.substring(startIndex, spaceIndex);
    word.trim();

    if (word.length() > 0 && wordCount < 30) {
      words[wordCount++] = word;
    }

    startIndex = spaceIndex + 1;
  }

  String currentChunkText = "";

  for (int i = 0; i < wordCount; i++) {
    String word = words[i];

    if (currentChunkText.length() == 0) {
      currentChunkText = word;
    }
    else if (currentChunkText.length() + 1 + word.length() <= MAX_CHUNK_CHARS) {
      currentChunkText += " ";
      currentChunkText += word;
    }
    else {
      if (totalChunks < 10) {
        chunks[totalChunks++] = currentChunkText;
      }

      currentChunkText = word;
    }
  }

  if (currentChunkText.length() > 0 && totalChunks < 10) {
    chunks[totalChunks++] = currentChunkText;
  }

  if (totalChunks == 0) {
    chunks[0] = "";
    totalChunks = 1;
  }

  lastChunkTime = millis();

  showChunk(currentChunk);
}


// =====================================================
// TAMPILKAN INSTRUMENTAL
// =====================================================

void showInstrumental() {

  clearLine(0);
  clearLine(1);

  // Baris 1
  lcd.setCursor(0, 0);

  for (int i = 0; i < 7; i++) {
    lcd.write(byte(0));
    lcd.print(" ");
  }

  // Baris 2
  lcd.setCursor(2, 1);
  lcd.print("Instrumental");
}


// =====================================================
// TAMPILKAN CHUNK
// =====================================================

void showChunk(int chunkIndex) {
  clearLine(0);
  clearLine(1);

  String chunk = chunks[chunkIndex];

  String line1 = "";
  String line2 = "";

  int startIndex = 0;

  while (startIndex < chunk.length()) {
    int spaceIndex = chunk.indexOf(' ', startIndex);

    if (spaceIndex == -1) {
      spaceIndex = chunk.length();
    }

    String word = chunk.substring(startIndex, spaceIndex);

    if (line1.length() == 0) {
      line1 = word;
    }
    else if (line1.length() + 1 + word.length() <= LCD_COLS) {
      line1 += " ";
      line1 += word;
    }
    else {
      line2 = word;
      startIndex = spaceIndex + 1;

      while (startIndex < chunk.length()) {
        spaceIndex = chunk.indexOf(' ', startIndex);

        if (spaceIndex == -1) {
          spaceIndex = chunk.length();
        }

        word = chunk.substring(startIndex, spaceIndex);

        if (line2.length() + 1 + word.length() <= LCD_COLS) {
          line2 += " ";
          line2 += word;
        }
        else {
          break;
        }

        startIndex = spaceIndex + 1;
      }

      break;
    }

    startIndex = spaceIndex + 1;
  }

  lcd.setCursor(0, 0);
  lcd.print(line1);

  lcd.setCursor(0, 1);
  lcd.print(line2);
}