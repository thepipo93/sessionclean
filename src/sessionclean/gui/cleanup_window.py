"""Main cleanup window — the core user-facing interface.

Shows three columns:
  NEW FILES | KEEP | DELETE

Each file card has buttons to move it between zones.
A confirm button executes the deletions (to Recycle Bin) and allows shutdown.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

import customtkinter as ctk
from send2trash import send2trash

from sessionclean.gui.widgets import (
    COLORS,
    EmptyStateWidget,
    FileCard,
    SummaryBar,
)

logger = logging.getLogger("sessionclean")


class CleanupWindow(ctk.CTkToplevel):
    """The main cleanup interface shown at shutdown or on demand.

    Args:
        new_files: List of file info dicts from the database.
        on_complete: Callback invoked after the user confirms.
                     Receives (keep_list, delete_list) as arguments.
        is_shutdown: If True, the confirm button says "Confirm & Shut Down".
    """

    def __init__(
        self,
        new_files: list[dict],
        on_complete: Callable[[list[str], list[str]], None],
        is_shutdown: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self._all_files = new_files
        self._on_complete = on_complete
        self._is_shutdown = is_shutdown

        # File sorting state
        self._new_list: list[dict] = list(new_files)
        self._keep_list: list[dict] = []
        self._delete_list: list[dict] = []

        # Window config
        self.title("SessionClean — Session Review")
        self.geometry("1000x650")
        self.minsize(800, 500)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        ctk.set_appearance_mode("dark")

        if not new_files:
            self._show_empty_state()
        else:
            self._build_ui()

    # ------------------------------------------------------------------
    # Empty state
    # ------------------------------------------------------------------
    def _show_empty_state(self) -> None:
        """Display the congratulatory message when no new files exist."""
        empty = EmptyStateWidget(self)
        empty.pack(fill="both", expand=True)

        close_btn = ctk.CTkButton(
            self,
            text="Close" if not self._is_shutdown else "Shut Down",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            fg_color=COLORS["success_green"],
            hover_color=COLORS["keep_hover"],
            command=self._confirm_empty,
        )
        close_btn.pack(pady=(0, 20), padx=20)

    # ------------------------------------------------------------------
    # Main UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        """Build the three-column layout."""
        # Header with summary bar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(10, 5))

        title = ctk.CTkLabel(
            header,
            text="📋 Session Review",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text_primary"],
        )
        title.pack(side="left")

        self._summary_bar = SummaryBar(header)
        self._summary_bar.pack(side="right")

        # Quick action buttons
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=15, pady=(0, 5))

        keep_all_btn = ctk.CTkButton(
            actions,
            text="✅ Keep All",
            width=100,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS["success_green"],
            hover_color=COLORS["keep_hover"],
            command=self._move_all_to_keep,
        )
        keep_all_btn.pack(side="left", padx=(0, 8))

        del_all_btn = ctk.CTkButton(
            actions,
            text="🗑️ Delete All",
            width=100,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS["danger_red"],
            hover_color=COLORS["delete_hover"],
            command=self._move_all_to_delete,
        )
        del_all_btn.pack(side="left")

        # Three columns
        columns = ctk.CTkFrame(self, fg_color="transparent")
        columns.pack(fill="both", expand=True, padx=15, pady=5)
        columns.grid_columnconfigure(0, weight=2)
        columns.grid_columnconfigure(1, weight=1)
        columns.grid_columnconfigure(2, weight=1)

        # --- NEW FILES column ---
        new_frame = self._make_column(columns, "📥 New Files", 0)
        self._new_scroll = ctk.CTkScrollableFrame(
            new_frame, fg_color="transparent"
        )
        self._new_scroll.pack(fill="both", expand=True)

        # --- KEEP column ---
        keep_frame = self._make_column(columns, "✅ Keep", 1)
        self._keep_scroll = ctk.CTkScrollableFrame(
            keep_frame, fg_color="transparent"
        )
        self._keep_scroll.pack(fill="both", expand=True)

        # --- DELETE column ---
        del_frame = self._make_column(columns, "🗑️ Delete", 2)
        self._delete_scroll = ctk.CTkScrollableFrame(
            del_frame, fg_color="transparent"
        )
        self._delete_scroll.pack(fill="both", expand=True)

        # Confirm button
        confirm_text = "✅ Confirm & Shut Down" if self._is_shutdown else "✅ Confirm & Close"
        self._confirm_btn = ctk.CTkButton(
            self,
            text=confirm_text,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            fg_color=COLORS["accent_blue"],
            hover_color="#2980b9",
            command=self._confirm_and_close,
        )
        self._confirm_btn.pack(fill="x", padx=15, pady=(5, 15))

        # Render initial state
        self._refresh_all()

    def _make_column(
        self, parent: ctk.CTkFrame, title: str, col: int
    ) -> ctk.CTkFrame:
        """Create a labeled column frame."""
        frame = ctk.CTkFrame(parent, fg_color=COLORS["neutral_bg"], corner_radius=10)
        frame.grid(row=0, column=col, sticky="nsew", padx=5)

        label = ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"],
        )
        label.pack(pady=(8, 4))

        return frame

    # ------------------------------------------------------------------
    # File movement
    # ------------------------------------------------------------------
    def _move_to_keep(self, file_info: dict) -> None:
        """Move a file to the Keep zone."""
        self._remove_from_all_lists(file_info)
        self._keep_list.append(file_info)
        self._refresh_all()

    def _move_to_delete(self, file_info: dict) -> None:
        """Move a file to the Delete zone."""
        self._remove_from_all_lists(file_info)
        self._delete_list.append(file_info)
        self._refresh_all()

    def _move_to_new(self, file_info: dict) -> None:
        """Move a file back to the New zone (undo)."""
        self._remove_from_all_lists(file_info)
        self._new_list.append(file_info)
        self._refresh_all()

    def _move_all_to_keep(self) -> None:
        self._keep_list.extend(self._new_list)
        self._new_list.clear()
        self._refresh_all()

    def _move_all_to_delete(self) -> None:
        self._delete_list.extend(self._new_list)
        self._new_list.clear()
        self._refresh_all()

    def _remove_from_all_lists(self, file_info: dict) -> None:
        """Remove a file from whichever list it's currently in."""
        path = file_info["path"]
        self._new_list = [f for f in self._new_list if f["path"] != path]
        self._keep_list = [f for f in self._keep_list if f["path"] != path]
        self._delete_list = [f for f in self._delete_list if f["path"] != path]

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _refresh_all(self) -> None:
        """Clear and re-render all three columns."""
        self._render_zone(self._new_scroll, self._new_list, "new")
        self._render_zone(self._keep_scroll, self._keep_list, "keep")
        self._render_zone(self._delete_scroll, self._delete_list, "delete")
        self._update_summary()

    def _render_zone(
        self,
        scroll_frame: ctk.CTkScrollableFrame,
        file_list: list[dict],
        zone: str,
    ) -> None:
        """Clear and render file cards in a scrollable frame."""
        for widget in scroll_frame.winfo_children():
            widget.destroy()

        if not file_list:
            placeholder = ctk.CTkLabel(
                scroll_frame,
                text="Drop files here" if zone != "new" else "All sorted!",
                text_color=COLORS["text_muted"],
                font=ctk.CTkFont(size=12),
            )
            placeholder.pack(pady=20)
            return

        for file_info in file_list:
            if zone == "new":
                card = FileCard(
                    scroll_frame,
                    file_info,
                    on_keep=self._move_to_keep,
                    on_delete=self._move_to_delete,
                    zone="new",
                )
            elif zone == "keep":
                card = FileCard(
                    scroll_frame,
                    file_info,
                    on_keep=self._move_to_new,  # Undo in keep -> back to new
                    on_delete=self._move_to_delete,
                    zone="keep",
                )
            else:  # delete
                card = FileCard(
                    scroll_frame,
                    file_info,
                    on_keep=self._move_to_keep,
                    on_delete=self._move_to_new,  # Undo in delete -> back to new
                    zone="delete",
                )
            card.pack(fill="x", pady=3, padx=4)

    def _update_summary(self) -> None:
        """Update the summary bar counts."""
        if hasattr(self, "_summary_bar"):
            delete_size = sum(f.get("size", 0) for f in self._delete_list)
            self._summary_bar.update_counts(
                total=len(self._new_list),
                keep=len(self._keep_list),
                delete=len(self._delete_list),
                delete_size=delete_size,
            )

    # ------------------------------------------------------------------
    # Confirm / Close
    # ------------------------------------------------------------------
    def _confirm_and_close(self) -> None:
        """Execute deletions (to Recycle Bin) and invoke the callback."""
        # Files still in the "new" column are treated as "keep" by default
        final_keep = [f["path"] for f in self._keep_list + self._new_list]
        final_delete = [f["path"] for f in self._delete_list]

        if final_delete:
            self._confirm_btn.configure(text="🔄 Cleaning up...", state="disabled")
            # Run deletions in background to avoid freezing UI
            threading.Thread(
                target=self._execute_deletions,
                args=(final_keep, final_delete),
                daemon=True,
            ).start()
        else:
            self._finish(final_keep, final_delete)

    def _execute_deletions(self, keep: list[str], delete: list[str]) -> None:
        """Send files to Recycle Bin (safe deletion)."""
        deleted = []
        failed = []

        for path in delete:
            try:
                send2trash(path)
                deleted.append(path)
                logger.info("Sent to Recycle Bin: %s", path)
            except Exception as exc:
                logger.error("Failed to delete %s: %s", path, exc)
                failed.append(path)

        if failed:
            logger.warning(
                "%d files could not be deleted: %s", len(failed), failed
            )

        # Back to main thread
        self.after(0, lambda: self._finish(keep, deleted))

    def _finish(self, keep: list[str], delete: list[str]) -> None:
        """Final step: invoke callback and close."""
        self._on_complete(keep, delete)
        self.destroy()

    def _confirm_empty(self) -> None:
        """Handle confirmation when there are no files."""
        self._on_complete([], [])
        self.destroy()

    def _on_close(self) -> None:
        """Handle window close (X button) — treat all files as kept."""
        all_paths = [f["path"] for f in self._all_files]
        self._on_complete(all_paths, [])
        self.destroy()
