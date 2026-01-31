"""Entry point for `python -m sessionclean`."""

import sys


def main() -> None:
    """Launch SessionClean."""
    # Ensure we're on Windows
    if sys.platform != "win32":
        print("SessionClean currently only supports Windows.")
        print("macOS and Linux support is planned for future versions.")
        sys.exit(1)

    from sessionclean.app import SessionCleanApp

    app = SessionCleanApp()
    app.run()


if __name__ == "__main__":
    main()
