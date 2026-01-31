"""System tray icon with status updates and context menu."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

from sessionclean import __app_name__

logger = logging.getLogger("sessionclean")

ICON_SIZE = 64
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"


class TrayIcon:
    """System tray icon with a context menu for quick actions.

    Menu items:
    - "Review Files Now"  -> opens the cleanup window on demand
    - "Settings..."       -> opens the config window
    - "New files: N"      -> informational, greyed out
    - "Exit"              -> exits the app without cleanup
    """

    def __init__(
        self,
        on_review_now: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_exit: Callable[[], None],
    ) -> None:
        self._on_review_now = on_review_now
        self._on_open_settings = on_open_settings
        self._on_exit = on_exit
        self._icon: pystray.Icon | None = None
        self._new_files_count: int = 0
        self._status_text: str = "SessionClean — Monitoring"
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start the tray icon on a background thread."""
        self._icon = pystray.Icon(
            name=__app_name__,
            icon=self._load_icon(),
            title=self._status_text,
            menu=self._build_menu(),
        )
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()
        logger.info("Tray icon started")

    def stop(self) -> None:
        """Stop the tray icon."""
        if self._icon:
            try:
                self._icon.stop()
                logger.info("Tray icon stopped")
            except Exception as exc:
                logger.debug("Error stopping tray icon: %s", exc)

    # ------------------------------------------------------------------
    # Status updates
    # ------------------------------------------------------------------
    def update_status(self, new_files_count: int) -> None:
        """Update the tooltip and menu with the current file count."""
        self._new_files_count = new_files_count

        if new_files_count == 0:
            self._status_text = "SessionClean — No new files"
        else:
            self._status_text = f"SessionClean — {new_files_count} new files"

        if self._icon:
            self._icon.title = self._status_text
            # Rebuild menu to update the count display
            self._icon.menu = self._build_menu()

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------
    def _build_menu(self) -> pystray.Menu:
        """Build the context menu."""
        return pystray.Menu(
            pystray.MenuItem(
                f"New files: {self._new_files_count}",
                action=None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Review Files Now",
                action=lambda icon, item: self._on_review_now(),
                enabled=self._new_files_count > 0,
            ),
            pystray.MenuItem(
                "Settings...",
                action=lambda icon, item: self._on_open_settings(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Exit",
                action=lambda icon, item: self._on_exit(),
            ),
        )

    # ------------------------------------------------------------------
    # Icon
    # ------------------------------------------------------------------
    def _load_icon(self) -> Image.Image:
        """Load the app icon, or generate a simple one if not found."""
        icon_path = ASSETS_DIR / "icon.png"
        if icon_path.exists():
            try:
                return Image.open(icon_path).resize((ICON_SIZE, ICON_SIZE))
            except Exception as exc:
                logger.warning("Failed to load icon: %s. Using generated icon.", exc)

        return self._generate_icon()

    @staticmethod
    def _generate_icon() -> Image.Image:
        """Generate a simple icon programmatically (green circle with checkmark feel)."""
        img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background circle
        margin = 4
        draw.ellipse(
            [margin, margin, ICON_SIZE - margin, ICON_SIZE - margin],
            fill=(46, 204, 113, 255),  # Green
        )

        # Simple "S" letter in white
        draw.text(
            (ICON_SIZE // 2 - 8, ICON_SIZE // 2 - 12),
            "S",
            fill=(255, 255, 255, 255),
        )

        return img
