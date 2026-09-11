# Spotify Lyric To LCD I2C

A Windows-based Python and Arduino project that displays synchronized lyrics from Spotify Desktop on a 16x2 I2C LCD.

## Features

- Detects the active Spotify Desktop session through Windows Media Session.
- Reads synchronized LRC lyrics from a local cache or LRCLIB.
- Selects the lyric line according to the current playback position.
- Sends lyric text to Arduino through USB Serial.
- Displays long lines using LCD scrolling.
- Handles instrumental songs and a music-note character.

## How It Works

```text
Spotify Desktop
      |
      v
Windows Media Session
      |
      v
Python application
  |       |       |
  |       |       +--> Parse LRC and select active line
  |       +----------> Download/cache lyrics from LRCLIB
  +------------------> Read artist, title, and playback position
      |
      v
USB Serial
      |
      v
Arduino + LCD 1602 I2C
```

## Requirements

### Hardware

- Arduino Uno, Nano, or Pro Micro.
- LCD 1602 with an I2C backpack, commonly PCF8574.
- USB data cable.
- Jumper wires and optionally a breadboard.

### Software

- Windows 10 or Windows 11.
- Spotify Desktop application. Spotify Web Player is not supported by this project.
- Python 3.10 or newer.
- Arduino IDE.
- Git, optional.

The Python application requires Windows because it uses Windows Runtime Media Session APIs.

## Wiring

### Arduino Uno / Nano

| LCD I2C | Arduino |
|---|---|
| VCC | 5V |
| GND | GND |
| SDA | A4 |
| SCL | A5 |

### Arduino Pro Micro

| LCD I2C | Arduino |
|---|---|
| VCC | VCC / 5V |
| GND | GND |
| SDA | D2 |
| SCL | D3 |

The most common LCD addresses are `0x27` and `0x3F`. If the LCD is blank, use an I2C scanner and update the address in the Arduino sketch.

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
│   └── .gitkeep
└── arduino/
    └── lcd_display/
        └── lcd_display.ino
```

| Path | Purpose |
|---|---|
| `main.py` | Spotify monitoring, lyric retrieval, timing, and serial output |
| `lyrics/` | Local cache for downloaded or manually added `.lrc` files |
| `arduino/lcd_display/lcd_display.ino` | Receives text and controls the LCD |
| `requirements.txt` | Python dependencies |
| `.env.example` | Configuration template |

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/hndll56/Spotify-Lyric-To-Lcd-l2c.git
cd Spotify-Lyric-To-Lcd-l2c
```

### 2. Choose a Python environment

There are two supported ways to run the application. Choose one.

#### Option A — Use a virtual environment (recommended)

A virtual environment keeps this project's Python packages separate from other projects and from the system Python installation.

```powershell
python -m venv .venv
.venv\Scripts\activate
```

If PowerShell blocks script activation, run the following in Command Prompt instead:

```cmd
.venv\Scripts\activate.bat
```

Install the dependencies inside the virtual environment:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the application:

```powershell
python main.py
```

When the terminal shows `(.venv)`, the virtual environment is active.

#### Option B — Run directly with the system Python

A virtual environment is optional. You can install the dependencies into your normal Python installation and run the application directly.

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Use this option only if you are comfortable sharing these packages with other Python projects on the computer. If you get `ModuleNotFoundError`, install the dependencies again using the same Python command that will run the application.

### 3. Install the Arduino library

1. Open Arduino IDE.
2. Open **Sketch > Include Library > Manage Libraries**.
3. Search for and install `LiquidCrystal_I2C`.
4. Open `arduino/lcd_display/lcd_display.ino`.
5. Select the correct board and Arduino COM port.
6. Confirm the LCD I2C address.
7. Upload the sketch.

### 4. Configure the application

Copy the example configuration:

```powershell
Copy-Item .env.example .env.local
```

Edit `.env.local`:

```env
SERIAL_PORT=COM5
BAUD_RATE=115200
LYRICS_FOLDER=lyrics
LRCLIB_URL=https://lrclib.net/api/get
```

Change `SERIAL_PORT` to the COM port assigned to your Arduino. The baud rate must match `Serial.begin()` in the Arduino sketch.

Do not commit `.env.local` to GitHub. It is ignored by `.gitignore`.

## Find the Arduino COM Port

Disconnect and reconnect the Arduino, then run:

```powershell
python -m serial.tools.list_ports
```

Use the port that belongs to the Arduino, for example `COM3` or `COM5`.

## Running the Application

1. Connect the Arduino and LCD.
2. Close Arduino Serial Monitor or other programs using the Arduino COM port.
3. Open Spotify Desktop and play a song.
4. Open a terminal in the repository root.
5. If using Option A, activate `.venv` first.
6. Run the program:

```powershell
python main.py
```

The program will display status messages in the terminal while sending the current lyric line to the LCD.

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `SERIAL_PORT` | `COM5` | Arduino serial port |
| `BAUD_RATE` | `115200` | Serial communication speed |
| `LYRICS_FOLDER` | `lyrics` | Local LRC cache directory |
| `LRCLIB_URL` | LRCLIB API URL | Synchronized lyric provider |

If a variable is not defined, the application uses its default value.

## Lyrics

When a new song starts, the application:

1. Reads the artist and title from Windows Media Session.
2. Searches the `lyrics/` folder for a matching `.lrc` file.
3. Requests synchronized lyrics from LRCLIB if no local file exists.
4. Saves successful downloads to the local cache.
5. Parses timestamps and chooses the active line.

Manually added LRC files can use this format:

```text
[00:12.340]First lyric line
[00:16.780]Second lyric line
[00:21.020]Third lyric line
```

The cache is local and downloaded `.lrc` files are excluded by `.gitignore`.

## Serial Protocol

Python sends one UTF-8 lyric line followed by a newline:

```text
CURRENT_LYRIC\n
```

The Arduino firmware receives the line and formats it for the 16x2 LCD.

## Troubleshooting

### `ModuleNotFoundError`

Make sure the dependencies are installed for the Python interpreter being used:

```powershell
python -m pip install -r requirements.txt
```

If using a virtual environment, activate it first. If running directly, do not use a different Python installation's `pip` command.

### `WinError 5: Access is denied: 'lyrics'`

Run the application from the repository root rather than opening `main.py` from an unrelated working directory in File Explorer:

```powershell
cd C:\path\to\Spotify-Lyric-To-Lcd-l2c
python main.py
```

The `lyrics` folder is used as the local lyric cache. Make sure it exists and is writable.

### Arduino cannot connect

- Confirm the USB cable supports data.
- Check the COM port in `.env.local`.
- Close Arduino Serial Monitor.
- Check that the Arduino is visible with `python -m serial.tools.list_ports`.
- Confirm the baud rate matches the Arduino sketch.

### LCD is blank

- Check VCC and GND.
- Check SDA and SCL wiring.
- Adjust the LCD contrast potentiometer.
- Run an I2C scanner.
- Try address `0x27` or `0x3F` in the sketch.

### Spotify is not detected

- Use Spotify Desktop, not the Web Player.
- Start playing a song before running `main.py`.
- Make sure Spotify is not paused indefinitely.
- Restart Spotify and the Python application if Windows Media Session does not update.

### Lyrics are not found

- Confirm the computer has internet access.
- Check the artist and title metadata.
- Some songs do not have synchronized lyrics on LRCLIB.
- Add a matching `.lrc` file manually to the `lyrics/` folder.

### Lyrics are out of sync

Playback position is obtained from Windows Media Session and may vary slightly between updates. Pause, seek, and resume operations can introduce small timing differences.

## Security

- Never commit API keys, passwords, tokens, or private credentials.
- Keep personal configuration in `.env.local`.
- Use `.env.example` only as a template.
- Downloaded lyric cache files are ignored by Git.

## Limitations

- Windows is required for the current media-session implementation.
- Spotify Desktop must expose the active media session.
- Not every song has synchronized lyrics.
- LCD output is limited by the 16x2 display size.
- Automatic COM port detection is not currently implemented.

## Future Improvements

- Automatic Arduino COM port detection.
- More accurate pause, resume, and seek synchronization.
- Better word wrapping and scrolling controls.
- Additional lyric providers.
- GUI-based configuration.
- OLED and other display support.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Credits

- [LRCLIB](https://lrclib.net) for synchronized lyric data.
- [pywinrt](https://github.com/pywinrt/pywinrt) for Windows Runtime access.
- [LiquidCrystal_I2C](https://github.com/johnrickman/LiquidCrystal_I2C) for Arduino LCD support.
- Spotify Desktop and Windows Media Session API.

## Disclaimer

This is an independent educational project and is not affiliated with or officially supported by Spotify. Spotify and related trademarks belong to their respective owners.
