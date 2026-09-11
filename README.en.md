# Spotify Lyric To LCD I2C

English documentation for the project.

**Language:** [Bahasa Indonesia](README.md) | **English**

A Windows-based Python and Arduino project that displays synchronized Spotify lyrics on a 16x2 I2C LCD.

## Features

- Reads the active Spotify Desktop session through Windows Media Session.
- Loads synchronized LRC lyrics from the local cache or LRCLIB.
- Selects lyric lines according to playback position.
- Sends lyric text to Arduino through USB Serial.
- Scrolls long lines on the LCD.

## Requirements

- Windows 10 or Windows 11.
- Python 3.10 or newer.
- Spotify Desktop application.
- Arduino Uno, Nano, or Pro Micro.
- LCD 1602 with an I2C backpack.
- Arduino IDE.

## Installation

### Option A — Virtual environment (recommended)

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

### Option B — Run directly with system Python

A virtual environment is optional. Install the dependencies into your active Python installation and run the application:

```powershell
python -m pip install -r requirements.txt
python main.py
```

Option B is convenient for a quick test, but a virtual environment is recommended to avoid dependency conflicts with other projects.

## Configuration

Copy `.env.example` to `.env.local` and edit the serial port:

```powershell
Copy-Item .env.example .env.local
```

Example:

```env
SERIAL_PORT=COM5
BAUD_RATE=115200
LYRICS_FOLDER=lyrics
LRCLIB_URL=https://lrclib.net/api/get
```

Do not commit `.env.local`.

## Arduino

Open `arduino/lcd_display/lcd_display.ino` in Arduino IDE, install `LiquidCrystal_I2C`, select the correct board and COM port, then upload the sketch. The default LCD address is commonly `0x27`; use an I2C scanner if the display is blank.

## Run

Connect the Arduino, close Serial Monitor, open Spotify Desktop, start a song, and run `python main.py` from the repository root.

## Troubleshooting

- `ModuleNotFoundError`: activate `.venv` or install `requirements.txt`.
- `WinError 5: Access is denied: 'lyrics'`: run the program from the repository root and ensure `lyrics` is a directory.
- Arduino connection failure: check the USB data cable, COM port, baud rate, and whether another program is using the port.
- Spotify not detected: use Spotify Desktop, start playback, and restart Spotify if Windows Media Session is not updating.
- Lyrics missing: check internet access or add a matching `.lrc` file to `lyrics/`.

## Project Structure

```text
main.py
lyrics/
arduino/lcd_display/lcd_display.ino
requirements.txt
.env.example
```

## License

MIT License. See `LICENSE`.

This is an independent educational project and is not affiliated with Spotify.