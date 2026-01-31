"""Windows shutdown interception using a hidden Win32 window.

Listens for WM_QUERYENDSESSION to detect when the user initiates a shutdown
or restart, blocks it temporarily, and triggers the cleanup UI.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import logging
import threading
from collections.abc import Callable

logger = logging.getLogger("sessionclean")

# Windows constants
WM_QUERYENDSESSION = 0x0011
WM_ENDSESSION = 0x0012
WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
WM_USER_SHOW_REVIEW = 0x0400 + 1  # Custom message to trigger review

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_long,
    wintypes.HWND,
    ctypes.c_uint,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


class ShutdownHook:
    """Creates a hidden window to intercept Windows shutdown events.

    When WM_QUERYENDSESSION is received:
    1. Calls ShutdownBlockReasonCreate to show a message in Windows' shutdown UI
    2. Returns 0 to block the shutdown
    3. Invokes the on_shutdown_requested callback
    4. Waits until allow_shutdown() is called

    Usage:
        hook = ShutdownHook(on_shutdown_requested=my_callback)
        # Run the message loop on a background thread
        thread = threading.Thread(target=hook.run_message_loop, daemon=True)
        thread.start()
        # ... later, when cleanup is done ...
        hook.allow_shutdown()
    """

    def __init__(self, on_shutdown_requested: Callable[[], None]) -> None:
        self._callback = on_shutdown_requested
        self._hwnd: int | None = None
        self._shutdown_blocked = False
        self._ready_event = threading.Event()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run_message_loop(self) -> None:
        """Register a window class, create a hidden window, and pump messages.

        This method blocks until the message loop exits.
        """
        try:
            self._register_and_create()
            self._ready_event.set()
            self._pump_messages()
        except Exception as exc:
            logger.error("Shutdown hook failed: %s", exc)
            self._ready_event.set()

    def wait_until_ready(self, timeout: float = 10.0) -> bool:
        """Wait until the hidden window is created and ready."""
        return self._ready_event.wait(timeout=timeout)

    def allow_shutdown(self) -> None:
        """Remove the shutdown block and allow Windows to proceed."""
        if self._hwnd and self._shutdown_blocked:
            try:
                ctypes.windll.user32.ShutdownBlockReasonDestroy(self._hwnd)
                self._shutdown_blocked = False
                logger.info("Shutdown block removed. Windows may proceed.")
            except Exception as exc:
                logger.error("Failed to remove shutdown block: %s", exc)

    def request_review(self) -> None:
        """Send a custom message to trigger the review UI (e.g., from tray menu)."""
        if self._hwnd:
            ctypes.windll.user32.PostMessageW(
                self._hwnd, WM_USER_SHOW_REVIEW, 0, 0
            )

    def stop(self) -> None:
        """Post WM_CLOSE to gracefully exit the message loop."""
        if self._hwnd:
            ctypes.windll.user32.PostMessageW(self._hwnd, WM_CLOSE, 0, 0)

    # ------------------------------------------------------------------
    # Win32 internals
    # ------------------------------------------------------------------
    def _register_and_create(self) -> None:
        """Register the window class and create the hidden window."""
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        hinstance = kernel32.GetModuleHandleW(None)
        class_name = "SessionCleanShutdownHook"

        # Keep reference to prevent garbage collection
        self._wndproc_ref = WNDPROC(self._wnd_proc)

        wc = wintypes.WNDCLASS()
        wc.lpfnWndProc = self._wndproc_ref
        wc.hInstance = hinstance
        wc.lpszClassName = class_name

        atom = user32.RegisterClassW(ctypes.byref(wc))
        if not atom:
            raise RuntimeError(
                f"RegisterClassW failed: {ctypes.GetLastError()}"
            )

        self._hwnd = user32.CreateWindowExW(
            0,             # dwExStyle
            class_name,    # lpClassName
            "SessionClean Shutdown Hook",  # lpWindowName
            0,             # dwStyle (invisible)
            0, 0, 0, 0,   # x, y, width, height
            0,             # hWndParent
            0,             # hMenu
            hinstance,     # hInstance
            0,             # lpParam
        )

        if not self._hwnd:
            raise RuntimeError(
                f"CreateWindowExW failed: {ctypes.GetLastError()}"
            )

        logger.info("Hidden shutdown hook window created (hwnd=%s)", self._hwnd)

    def _wnd_proc(
        self,
        hwnd: int,
        msg: int,
        wparam: int,
        lparam: int,
    ) -> int:
        """Window procedure handling shutdown and custom messages."""
        user32 = ctypes.windll.user32

        if msg == WM_QUERYENDSESSION:
            logger.info("WM_QUERYENDSESSION received — blocking shutdown")
            self._block_shutdown(hwnd)
            # Trigger the cleanup UI on a separate thread to avoid blocking wndproc
            threading.Thread(
                target=self._safe_callback, daemon=True
            ).start()
            return 0  # Block shutdown

        elif msg == WM_ENDSESSION:
            if wparam:
                logger.warning("WM_ENDSESSION: session IS ending (forced)")
                self._emergency_save()
            return 0

        elif msg == WM_USER_SHOW_REVIEW:
            logger.info("Manual review requested via custom message")
            threading.Thread(
                target=self._safe_callback, daemon=True
            ).start()
            return 0

        elif msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0

        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _block_shutdown(self, hwnd: int) -> None:
        """Call ShutdownBlockReasonCreate to show reason in Windows UI."""
        try:
            reason = "SessionClean is reviewing your new files..."
            ctypes.windll.user32.ShutdownBlockReasonCreate(
                hwnd, reason
            )
            self._shutdown_blocked = True
            logger.info("Shutdown blocked: %s", reason)
        except Exception as exc:
            logger.error("ShutdownBlockReasonCreate failed: %s", exc)

    def _safe_callback(self) -> None:
        """Call the shutdown callback with error handling."""
        try:
            self._callback()
        except Exception as exc:
            logger.error("Shutdown callback error: %s", exc)
            # If callback fails, unblock shutdown to avoid locking the user
            self.allow_shutdown()

    def _emergency_save(self) -> None:
        """Minimal save if the user forces shutdown."""
        from sessionclean.constants import APP_DIR, INTERRUPTED_FLAG

        try:
            APP_DIR.mkdir(parents=True, exist_ok=True)
            INTERRUPTED_FLAG.write_text("interrupted", encoding="utf-8")
            logger.info("Emergency flag written: %s", INTERRUPTED_FLAG)
        except Exception as exc:
            logger.error("Emergency save failed: %s", exc)

    def _pump_messages(self) -> None:
        """Standard Win32 message pump."""
        user32 = ctypes.windll.user32
        msg = wintypes.MSG()

        while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        logger.info("Shutdown hook message loop exited")


# ---------------------------------------------------------------------------
# WNDCLASS structure (not provided by ctypes.wintypes by default)
# ---------------------------------------------------------------------------
if not hasattr(wintypes, "WNDCLASS"):

    class WNDCLASS(ctypes.Structure):
        _fields_ = [
            ("style", ctypes.c_uint),
            ("lpfnWndProc", WNDPROC),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", wintypes.HINSTANCE),
            ("hIcon", wintypes.HICON),
            ("hCursor", wintypes.HANDLE),
            ("hbrBackground", wintypes.HBRUSH),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
        ]

    wintypes.WNDCLASS = WNDCLASS  # type: ignore[attr-defined]
