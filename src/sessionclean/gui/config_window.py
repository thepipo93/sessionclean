"""Settings window for managing monitored paths and filter rules."""

from __future__ import annotations

import logging
from collections.abc import Callable
from tkinter import filedialog

import customtkinter as ctk

from sessionclean.config import AppConfig
from sessionclean.gui.widgets import COLORS
from sessionclean.utils.drive_utils import is_removable_drive

logger = logging.getLogger("sessionclean")


class ConfigWindow(ctk.CTkToplevel):
    """Settings window for SessionClean configuration.

    Allows users to:
    - Add / remove monitored paths
    - Toggle recursive scanning per path
    - Mark paths as removable (external drives)
    """

    def __init__(
        self,
        config: AppConfig,
        on_save: Callable[[AppConfig], None],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._config = config
        self._on_save = on_save

        self.title("SessionClean — Settings")
        self.geometry("600x500")
        self.minsize(500, 400)
        self.attributes("-topmost", True)

        self._build_ui()

    def _build_ui(self) -> None:
        """Construct the settings UI."""
        # Title
        title = ctk.CTkLabel(
            self,
            text="⚙️ Settings",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.pack(pady=(15, 10))

        # Monitored paths section
        paths_label = ctk.CTkLabel(
            self,
            text="Monitored Folders",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_secondary"],
        )
        paths_label.pack(anchor="w", padx=20)

        # Scrollable list of paths
        self._paths_frame = ctk.CTkScrollableFrame(self, height=250)
        self._paths_frame.pack(fill="both", expand=True, padx=20, pady=5)

        self._render_paths()

        # Add path button
        add_btn = ctk.CTkButton(
            self,
            text="➕ Add Folder",
            font=ctk.CTkFont(size=13),
            fg_color=COLORS["accent_blue"],
            hover_color="#2980b9",
            command=self._browse_folder,
        )
        add_btn.pack(pady=10)

        # Save / Cancel buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(5, 15))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            fg_color=COLORS["neutral_border"],
            hover_color=COLORS["neutral_hover"],
            command=self.destroy,
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Save",
            width=100,
            fg_color=COLORS["success_green"],
            hover_color=COLORS["keep_hover"],
            command=self._save_and_close,
        )
        save_btn.pack(side="right")

    def _render_paths(self) -> None:
        """Render the list of monitored paths."""
        for widget in self._paths_frame.winfo_children():
            widget.destroy()

        for i, mp in enumerate(self._config.monitored_paths):
            row = ctk.CTkFrame(self._paths_frame, fg_color=COLORS["neutral_bg"], corner_radius=6)
            row.pack(fill="x", pady=2)

            # Enable checkbox
            enabled_var = ctk.BooleanVar(value=mp.enabled)
            cb = ctk.CTkCheckBox(
                row,
                text="",
                variable=enabled_var,
                width=24,
                command=lambda idx=i, var=enabled_var: self._toggle_enabled(idx, var),
            )
            cb.pack(side="left", padx=(8, 4))

            # Path label
            path_label = ctk.CTkLabel(
                row,
                text=mp.path,
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_primary"] if mp.enabled else COLORS["text_muted"],
                anchor="w",
            )
            path_label.pack(side="left", fill="x", expand=True, padx=4)

            # Removable badge
            if mp.is_removable:
                badge = ctk.CTkLabel(
                    row,
                    text="USB",
                    font=ctk.CTkFont(size=10),
                    text_color=COLORS["accent_blue"],
                    fg_color="#1a3a5a",
                    corner_radius=4,
                    width=35,
                    height=20,
                )
                badge.pack(side="right", padx=4)

            # Remove button
            remove_btn = ctk.CTkButton(
                row,
                text="✕",
                width=30,
                height=26,
                fg_color=COLORS["danger_red"],
                hover_color=COLORS["delete_hover"],
                command=lambda idx=i: self._remove_path(idx),
            )
            remove_btn.pack(side="right", padx=(0, 8), pady=4)

    def _toggle_enabled(self, index: int, var: ctk.BooleanVar) -> None:
        """Toggle the enabled state of a monitored path."""
        self._config.monitored_paths[index].enabled = var.get()

    def _browse_folder(self) -> None:
        """Open a folder browser dialog to add a new path."""
        folder = filedialog.askdirectory(title="Select folder to monitor")
        if folder:
            removable = is_removable_drive(folder)
            self._config.add_path(folder, recursive=True, is_removable=removable)
            self._render_paths()

    def _remove_path(self, index: int) -> None:
        """Remove a monitored path by index."""
        if 0 <= index < len(self._config.monitored_paths):
            removed = self._config.monitored_paths.pop(index)
            logger.info("Removed monitored path: %s", removed.path)
            self._render_paths()

    def _save_and_close(self) -> None:
        """Save config and close the window."""
        self._config.save()
        self._on_save(self._config)
        self.destroy()
