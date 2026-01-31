# SessionClean 🧹

**Review and clean files created during your Windows session — before shutdown.**

Ever noticed your computer slowly filling up with files you downloaded once and never used again? SessionClean solves this by showing you exactly what's new at the end of every session, letting you decide what stays and what goes.

## The Problem

Remember internet cafés? Every time your session ended, the computer wiped everything clean. The problem was it deleted *everything* without asking.

**SessionClean is the smart evolution of that idea.** Instead of deleting blindly, it gives you control:

1. 📸 Takes a snapshot of your files when you start your PC
2. 👁️ Silently monitors for new files throughout the day
3. 📋 Shows you a summary when you shut down
4. ✅ You decide what to **keep** and what to **delete**
5. 🗑️ Deleted files go to the Recycle Bin (safe for 30 days)

## Features

- **Full disk monitoring** — Tracks Downloads, Desktop, Documents, and any folder you configure
- **External drive support** — Monitor your USB drives and external HDDs too
- **Smart filtering** — Ignores system files, temp files, and cache (shows only YOUR files)
- **Safe deletion** — Files go to the Recycle Bin, never permanently deleted
- **System tray** — Runs silently in the background with real-time file count
- **Shutdown interception** — Catches Windows shutdown to show your review before powering off
- **"Review Now" option** — Don't want to wait? Review files anytime from the tray menu
- **Clean session message** — If you didn't download anything, you get a 🎉 congratulations!

## Quick Start

### Requirements
- Windows 10/11
- Python 3.10+

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/sessionclean.git
cd sessionclean

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Run

```bash
python -m sessionclean
```

The app will:
1. Appear in your system tray (look for the green "S" icon)
2. Start scanning your default folders (Desktop, Downloads, Documents, etc.)
3. Monitor for new files in the background
4. Show the cleanup window when you shut down your PC

### Configuration

Right-click the tray icon → **Settings** to:
- Add/remove monitored folders
- Add external drives (USB, HDD)
- Enable/disable specific paths

Config is stored at `%USERPROFILE%\.sessionclean\config.json`

## How It Works

```
┌──────────────────────────────────────────────────┐
│  PC Starts → SessionClean takes snapshot 📸      │
│                                                  │
│  During the day → Silently monitors new files 👁️  │
│                                                  │
│  Shutdown → Shows review window 📋               │
│                                                  │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐        │
│  │NEW FILES│→ │  KEEP ✅ │  │ DELETE 🗑️│        │
│  │         │  │         │  │          │        │
│  │file1.pdf│  │         │  │          │        │
│  │file2.zip│  │         │  │          │        │
│  │img3.png │  │         │  │          │        │
│  └─────────┘  └─────────┘  └──────────┘        │
│                                                  │
│  [Confirm & Shut Down] → Recycle Bin → Power Off │
└──────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| GUI | CustomTkinter |
| File monitoring | watchdog |
| Database | SQLite |
| System tray | pystray + Pillow |
| Shutdown hook | pywin32 (Win32 API) |
| Safe deletion | send2trash |

## Project Structure

```
src/sessionclean/
├── app.py              # Main orchestrator
├── config.py           # Configuration management
├── constants.py        # Default filters and paths
├── database.py         # SQLite storage
├── filter_engine.py    # Smart file filtering
├── monitor.py          # Real-time file watching
├── scanner.py          # Startup snapshot
├── shutdown_hook.py    # Windows shutdown interception
├── tray.py             # System tray icon
├── gui/
│   ├── cleanup_window.py   # Main review UI
│   ├── config_window.py    # Settings UI
│   └── widgets.py          # Reusable components
└── utils/
    ├── drive_utils.py      # Drive detection
    ├── file_utils.py       # File helpers
    └── logging_setup.py    # Logging config
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linter
ruff check src/
```

## Roadmap

- [x] Core file monitoring and snapshot system
- [x] Cleanup UI with Keep/Delete zones
- [x] System tray integration
- [x] Windows shutdown interception
- [x] Smart file filtering
- [x] External drive support
- [ ] Drag-and-drop file sorting
- [ ] Session statistics and history
- [ ] Auto-categorization (group by file type)
- [ ] Whitelist rules ("always keep files from X")
- [ ] Windows installer (.exe)
- [ ] macOS support
- [ ] Linux support

## Contributing

Contributions are welcome! Please check out [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the **GNU General Public License v3.0** — see the [LICENSE](LICENSE) file for details.

You are free to use, modify, and distribute this software. Any derivative work must also be open source under the same license.

## Why "SessionClean"?

Because every session deserves a clean ending. 🧹
