# Spotify Lyric To LCD I2C

A Windows-based Python and Arduino project that displays synchronized lyrics from Spotify Desktop on a 16x2 I2C LCD.

## Overview

Spotify Lyric To LCD connects Spotify Desktop, Windows Media Session, Python, and an Arduino-powered LCD. The Python application detects the currently playing song, loads synchronized lyrics from a local cache or LRCLIB, and sends the active lyric line to Arduino through USB Serial. The Arduino displays the text on a 16x2 I2C LCD with automatic scrolling for long lines.

## Features

- Detects the active Spotify Desktop session through Windows Media Session API.
- Supports timestamped LRC lyrics.
- Uses a local `lyrics/` cache to avoid downloading the same lyrics repeatedly.
- Falls back to LRCLIB when a matching local lyric file is unavailable.
- Calculates the current lyric from playback position.
- Sends lyric text to Arduino over USB Serial.
- Displays text on a 16x2 I2C LCD.
- Includes instrumental-song handling and a custom music-note character.

## System Architecture

```text
Spotify Desktop
      |
      v
Windows Media Session API
      |
      v
Python Application
      |
      +--> Read artist and title
      +--> Load cached LRC lyrics
      +--> Fetch lyrics from LRCLIB if needed
      +--> Parse timestamps and select active line
      |
      v
USB Serial
      |
      v
Arduino Uno / Nano / Pro Micro
      |
      v
LCD 1602 with I2C Backpack
```

## Hardware Requirements

| Component | Description |
|---|---|
| Arduino Uno, Nano, or Pro Micro | Microcontroller for the LCD display |
| LCD 1602 with I2C backpack | 16 columns × 2 rows display, commonly using PCF8574 |
| USB data cable | Power and serial communication between the computer and Arduino |
| Jumper wires | Hardware connections |
| Breadboard | Optional for prototyping |

## LCD I2C Wiring

### Arduino Uno / Nano

| LCD I2C Pin | Arduino Pin |
|---|---|
| VCC | 5V |
| GND | GND |
| SDA | A4 |
| SCL | A5 |

### Arduino Pro Micro

| LCD I2C Pin | Arduino Pin |
|---|---|
| VCC | VCC / 5V |
| GND | GND |
| SDA | D2 |
| SCL | D3 |

### Wiring Diagram

```text
LCD I2C Backpack       Arduino Uno / Nano
----------------       ------------------
VCC  ----------------> 5V
GND  ----------------> GND
SDA  ----------------> A4
SCL  ----------------> A5
```

The common LCD I2C address is `0x27`, although some modules use `0x3F`. If the display does not respond, use an I2C scanner to find the correct address and update the Arduino sketch if necessary.

## Software Requirements

- Windows 10 or Windows 11.
- Spotify Desktop.
- Python 3.10 or newer.
- Arduino IDE.
- Git (optional, for development).

The Python component uses Windows Runtime Media Session APIs, so it requires Windows.

## Project Structure

```text
Spotify-Lyric-To-Lcd-l2c/
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
├── requirements.txt
├── main.py
├── lyrics/
│   └── *.lrc
├── arduino/
│   └── lcd_display/
│       ├── lcd_display.ino
│       └── .vscode/
└── docs/
```

### Main Files

| File / Folder | Purpose |
|---|---|
| `main.py` | Main Python application: Spotify monitoring, lyric retrieval, LRC parsing, timing, and serial output |
| `lyrics/` | Local cache for downloaded or manually added `.lrc` files |
| `arduino/lcd_display/lcd_display.ino` | Arduino firmware for receiving lyric text and controlling the LCD |
| `requirements.txt` | Python dependencies |
| `.env.example` | Example environment configuration template |

## Python Dependencies

Install the dependencies listed in `requirements.txt`:

```powershell
pip install -r requirements.txt
```

The project uses packages for:

- Windows Runtime Media Session access through `winrt`.
- HTTP requests through `requests`.
- USB Serial communication through `pyserial`.

## Installation

### 1. Clone the Repository

```powershell
git clone https://github.com/hndll56/Spotify-Lyric-To-Lcd-l2c.git
cd Spotify-Lyric-To-Lcd-l2c
```

### 2. Create a Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Upload the Arduino Firmware

1. Open Arduino IDE.
2. Open `arduino/lcd_display/lcd_display.ino`.
3. Install the required `LiquidCrystal_I2C` library.
4. Select the correct board and COM port.
5. Confirm the LCD I2C address in the sketch.
6. Upload the firmware.

## Configuration

Open `main.py` and adjust the serial configuration if necessary:

```python
PORT = "COM5"
BAUDRATE = 115200
```

`PORT` must match the COM port assigned to the Arduino. The baud rate must be identical to the value used by `Serial.begin()` in the Arduino sketch.

Other timing settings include:

```python
LYRICS_FOLDER = "lyrics"
CHECK_SONG_INTERVAL = 0.5
CHECK_POSITION_INTERVAL = 0.03
```

## Running the Application

1. Connect the Arduino to the computer.
2. Make sure the LCD is wired correctly.
3. Open Spotify Desktop and play a song.
4. Activate the Python virtual environment.
5. Run the application from the repository root:

```powershell
python main.py
```

The program will monitor the active Spotify session, retrieve or load synchronized lyrics, and send the current lyric line to the Arduino.

## How Lyrics Are Managed

When a new song is detected, the application:

1. Normalizes the artist and title.
2. Searches the `lyrics/` folder for a matching `.lrc` file.
3. If no local file is found, requests synchronized lyrics from LRCLIB.
4. Saves successfully retrieved lyrics to the local cache.
5. Parses timestamped lines from the LRC file.
6. Selects the line whose timestamp matches the current playback position.

## LRC File Format

Lyrics can also be added manually to the `lyrics/` folder.

Example:

```text
[00:12.34]First lyric line
[00:16.78]Second lyric line
[00:21.02]Third lyric line
```

Supported timestamps use the format `[mm:ss.xx]` or `[mm:ss.xxx]`.

## Serial Communication

The Python application sends UTF-8 text terminated by a newline character:

```text
CURRENT_LYRIC\n
```

The Arduino receives the lyric line and handles the LCD display formatting, including splitting long text into displayable chunks.

## Display Behavior

The LCD has a physical limit of 16 characters per line and two lines. Long lyrics are divided into chunks and displayed sequentially. The firmware also supports a music-note custom character and instrumental-song display behavior.

## Troubleshooting

| Problem | Possible Solution |
|---|---|
| Arduino cannot connect | Check the configured COM port and USB cable |
| LCD is blank | Check VCC, GND, SDA, SCL, contrast, and I2C address |
| Lyrics are not found | Check the song metadata, internet connection, or add an LRC file manually |
| Spotify is not detected | Open Spotify Desktop and start playback |
| Display is not synchronized | Confirm the Windows Media Session is reporting playback and position data |

## Security

Do not commit API keys, passwords, or private credentials. Keep local secrets in `.env` and use `.env.example` only as a template.

## Future Improvements

- Improved word wrapping and scrolling controls.
- More lyric providers and offline management tools.
- Automatic Arduino COM port detection.
- Additional display support such as OLED.
- More accurate pause, resume, and seeking synchronization.
- Configuration through a graphical user interface.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Credits

- [LRCLIB](https://lrclib.net) for synchronized lyric data.
- [pywinrt](https://github.com/pywinrt/pywinrt) for Windows Runtime access.
- [LiquidCrystal_I2C](https://github.com/johnrickman/LiquidCrystal_I2C) for Arduino LCD support.
- Spotify Desktop and Windows Media Session API.

## Disclaimer

This is an independent educational project and is not affiliated with or officially supported by Spotify. Spotify and related trademarks belong to their respective owners.
