"""Entry point for `python -m sessionclean`."""

import sys


def main() -> None:
    """Launch SessionClean."""
    # Ensure we're on Windows
    if sys.platform != "win32":
        print("SessionClean currently only supports Windows.")
        print("macOS and Linux support is planned for future versions.")
        sys.exit(1)

    import ctypes

    # Single-instance check: if already running, just open the review window
    _mutex = ctypes.windll.kernel32.CreateMutexW(None, True, "SessionClean_SingleInstance")
    last_error = ctypes.windll.kernel32.GetLastError()

    if last_error == 183:  # ERROR_ALREADY_EXISTS
        # Another instance is running — send it a message to show the review window
        hwnd = ctypes.windll.user32.FindWindowW("SessionCleanShutdownHook", None)
        if hwnd:
            ctypes.windll.user32.PostMessageW(hwnd, 0x0401, 0, 0)  # WM_USER_SHOW_REVIEW
        sys.exit(0)

    from sessionclean.app import SessionCleanApp

    app = SessionCleanApp()
    app.run()


if __name__ == "__main__":
    main()
