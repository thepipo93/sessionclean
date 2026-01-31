"""Application orchestrator — wires all subsystems together."""

from __future__ import annotations

import logging
import threading

import customtkinter as ctk

from sessionclean import __app_name__, __version__
from sessionclean.config import AppConfig
from sessionclean.constants import APP_DIR, INTERRUPTED_FLAG
from sessionclean.database import SnapshotDatabase
from sessionclean.filter_engine import FilterEngine
from sessionclean.gui.cleanup_window import CleanupWindow
from sessionclean.gui.config_window import ConfigWindow
from sessionclean.monitor import FileMonitor
from sessionclean.scanner import Scanner
from sessionclean.shutdown_hook import ShutdownHook
from sessionclean.tray import TrayIcon
from sessionclean.utils.logging_setup import setup_logging

logger = logging.getLogger("sessionclean")


class SessionCleanApp:
    """Top-level coordinator. Owns the lifecycle of all subsystems.

    Threading model:
        Main thread:      CustomTkinter mainloop (hidden root window)
        Background #1:    Win32 shutdown hook message loop
        Background #2:    pystray tray icon
        Background #3:    Initial snapshot scan
        Background #4..N: watchdog observers (one per monitored path)
    """

    def __init__(self) -> None:
        setup_logging()
        logger.info("Starting %s v%s", __app_name__, __version__)

        self._config = AppConfig.load()
        self._db = SnapshotDatabase()
        self._filter = FilterEngine(self._config)
        self._scanner = Scanner(self._config, self._db, self._filter)
        self._monitor: FileMonitor | None = None
        self._tray: TrayIcon | None = None
        self._shutdown_hook: ShutdownHook | None = None
        self._root: ctk.CTk | None = None
        self._cleanup_window: CleanupWindow | None = None
        self._tray_update_interval = 5000  # ms

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Start all subsystems and enter the main loop."""
        APP_DIR.mkdir(parents=True, exist_ok=True)
        self._check_interrupted_flag()

        # Initialize database
        self._db.initialize()

        # Create hidden root window for CustomTkinter
        self._root = ctk.CTk()
        self._root.withdraw()  # Hidden
        ctk.set_appearance_mode(self._config.theme)

        # Start subsystems
        self._start_shutdown_hook()
        self._start_tray()
        self._start_scan_and_monitor()

        # Periodic tray update
        self._schedule_tray_update()

        # Auto-open the review window after a short delay (let scan start first)
        self._root.after(2000, lambda: self._show_cleanup(is_shutdown=False))

        logger.info("All subsystems started. Entering main loop.")
        self._root.mainloop()

    # ------------------------------------------------------------------
    # Startup
    # ------------------------------------------------------------------
    def _check_interrupted_flag(self) -> None:
        """Check if the previous session was interrupted."""
        if INTERRUPTED_FLAG.exists():
            logger.warning(
                "Previous session was interrupted. Some files may not have been reviewed."
            )
            try:
                INTERRUPTED_FLAG.unlink()
            except OSError:
                pass

    def _start_shutdown_hook(self) -> None:
        """Start the Win32 shutdown hook on a background thread."""
        self._shutdown_hook = ShutdownHook(
            on_shutdown_requested=self._on_shutdown_requested,
            on_review_requested=self._on_review_now,
        )
        hook_thread = threading.Thread(
            target=self._shutdown_hook.run_message_loop,
            name="ShutdownHook",
            daemon=True,
        )
        hook_thread.start()
        self._shutdown_hook.wait_until_ready()
        logger.info("Shutdown hook ready")

    def _start_tray(self) -> None:
        """Start the system tray icon."""
        self._tray = TrayIcon(
            on_review_now=self._on_review_now,
            on_open_settings=self._on_open_settings,
            on_exit=self._on_exit,
        )
        self._tray.start()

    def _start_scan_and_monitor(self) -> None:
        """Start the snapshot scan in background, then start the file monitor."""

        def _scan_then_monitor():
            try:
                count = self._scanner.take_snapshot()
                logger.info("Snapshot complete: %d files", count)
            except Exception as exc:
                logger.error("Snapshot scan failed: %s", exc)

            # Start monitoring after scan completes
            self._monitor = FileMonitor(
                config=self._config,
                db=self._db,
                filter_engine=self._filter,
                scan_start_time=self._scanner.scan_start_time,
            )
            self._monitor.start()

        scan_thread = threading.Thread(
            target=_scan_then_monitor,
            name="Scanner",
            daemon=True,
        )
        scan_thread.start()

    # ------------------------------------------------------------------
    # Periodic updates
    # ------------------------------------------------------------------
    def _schedule_tray_update(self) -> None:
        """Periodically update the tray icon with the current file count."""
        if self._tray and self._db:
            try:
                count = self._db.get_new_files_count()
                self._tray.update_status(count)
            except Exception:
                pass

        if self._root:
            self._root.after(self._tray_update_interval, self._schedule_tray_update)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _on_shutdown_requested(self) -> None:
        """Called when Windows shutdown is detected."""
        logger.info("Shutdown requested — preparing review")
        # Schedule UI on the main thread
        if self._root:
            self._root.after(0, lambda: self._show_cleanup(is_shutdown=True))

    def _on_review_now(self) -> None:
        """Called from tray menu 'Review Files Now'."""
        logger.info("Manual review requested")
        if self._root:
            self._root.after(0, lambda: self._show_cleanup(is_shutdown=False))

    def _on_open_settings(self) -> None:
        """Called from tray menu 'Settings...'."""
        if self._root:
            self._root.after(0, self._show_settings)

    def _on_exit(self) -> None:
        """Called from tray menu 'Exit'."""
        logger.info("User requested exit")
        self._teardown()

    # ------------------------------------------------------------------
    # UI windows
    # ------------------------------------------------------------------
    def _show_cleanup(self, is_shutdown: bool) -> None:
        """Show the cleanup window with all new files."""
        if self._cleanup_window is not None:
            try:
                self._cleanup_window.focus()
                return
            except Exception:
                self._cleanup_window = None

        # Stop monitor to prevent new events during review
        if self._monitor:
            self._monitor.stop()

        new_files = self._db.get_all_new_files()
        logger.info("Showing cleanup window with %d files", len(new_files))

        # Keep root hidden but ensure it exists for toplevel windows
        self._root.deiconify()
        self._root.withdraw()

        self._cleanup_window = CleanupWindow(
            new_files=new_files,
            on_complete=lambda keep, delete: self._on_cleanup_complete(
                keep, delete, is_shutdown
            ),
            is_shutdown=is_shutdown,
        )
        # Force the cleanup window to appear on top
        self._cleanup_window.after(100, self._cleanup_window.lift)

    def _show_settings(self) -> None:
        """Show the settings window."""
        self._root.deiconify()
        self._root.withdraw()
        ConfigWindow(
            config=self._config,
            on_save=self._on_config_saved,
        )

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------
    def _on_cleanup_complete(
        self, keep: list[str], delete: list[str], is_shutdown: bool
    ) -> None:
        """Called after the user confirms cleanup."""
        logger.info(
            "Cleanup complete: %d kept, %d deleted", len(keep), len(delete)
        )
        self._cleanup_window = None
        self._root.withdraw()

        if is_shutdown:
            # Allow Windows to proceed with shutdown
            if self._shutdown_hook:
                self._shutdown_hook.allow_shutdown()
            self._teardown()
        else:
            # Restart monitoring for continued use
            self._monitor = FileMonitor(
                config=self._config,
                db=self._db,
                filter_engine=self._filter,
                scan_start_time=self._scanner.scan_start_time,
            )
            self._monitor.start()

    def _on_config_saved(self, new_config: AppConfig) -> None:
        """Called when settings are saved."""
        self._config = new_config
        self._filter = FilterEngine(self._config)
        logger.info("Configuration updated")

        # Restart monitor with new config
        if self._monitor:
            self._monitor.stop()
            self._monitor = FileMonitor(
                config=self._config,
                db=self._db,
                filter_engine=self._filter,
                scan_start_time=self._scanner.scan_start_time,
            )
            self._monitor.start()

    # ------------------------------------------------------------------
    # Teardown
    # ------------------------------------------------------------------
    def _teardown(self) -> None:
        """Gracefully shut down all subsystems."""
        logger.info("Shutting down %s", __app_name__)

        if self._monitor:
            self._monitor.stop()
        if self._tray:
            self._tray.stop()
        if self._db:
            self._db.close()
        if self._shutdown_hook:
            self._shutdown_hook.stop()
        if self._root:
            self._root.quit()

        logger.info("%s stopped", __app_name__)
