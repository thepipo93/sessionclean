"""Reusable custom widgets for the SessionClean GUI."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from sessionclean.utils.file_utils import format_size, get_file_category

# Color palette
COLORS = {
    "keep_bg": "#1a3a2a",
    "keep_border": "#2ecc71",
    "keep_hover": "#254d38",
    "delete_bg": "#3a1a1a",
    "delete_border": "#e74c3c",
    "delete_hover": "#4d2525",
    "neutral_bg": "#2b2b2b",
    "neutral_border": "#555555",
    "neutral_hover": "#383838",
    "text_primary": "#ffffff",
    "text_secondary": "#aaaaaa",
    "text_muted": "#777777",
    "success_green": "#2ecc71",
    "danger_red": "#e74c3c",
    "accent_blue": "#3498db",
}

# Category emoji/icons (text-based for simplicity)
CATEGORY_ICONS: dict[str, str] = {
    "Documents": "📄",
    "Images": "🖼️",
    "Videos": "🎬",
    "Audio": "🎵",
    "Archives": "📦",
    "Code": "💻",
    "Installers": "⚙️",
    "Other": "📁",
}


class FileCard(ctk.CTkFrame):
    """A card representing a single file with name, size, location, and action buttons.

    Displays:
    - Category icon + file name
    - File size + parent directory
    - "Keep" and "Delete" buttons to sort the file
    """

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        file_info: dict,
        on_keep: Callable[[dict], None] | None = None,
        on_delete: Callable[[dict], None] | None = None,
        show_buttons: bool = True,
        zone: str = "new",  # "new", "keep", or "delete"
        **kwargs,
    ) -> None:
        self._file_info = file_info
        self._on_keep = on_keep
        self._on_delete = on_delete
        self._zone = zone

        # Choose border color based on zone
        border_color = {
            "new": COLORS["neutral_border"],
            "keep": COLORS["keep_border"],
            "delete": COLORS["delete_border"],
        }.get(zone, COLORS["neutral_border"])

        bg_color = {
            "new": COLORS["neutral_bg"],
            "keep": COLORS["keep_bg"],
            "delete": COLORS["delete_bg"],
        }.get(zone, COLORS["neutral_bg"])

        super().__init__(
            parent,
            fg_color=bg_color,
            border_color=border_color,
            border_width=1,
            corner_radius=8,
            **kwargs,
        )

        self._build_ui(show_buttons)

    @property
    def file_info(self) -> dict:
        return self._file_info

    def _build_ui(self, show_buttons: bool) -> None:
        """Build the card layout."""
        # Top row: icon + name + size
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=8, pady=(6, 2))

        category = get_file_category(self._file_info["path"])
        icon = CATEGORY_ICONS.get(category, "📁")

        name_label = ctk.CTkLabel(
            top_frame,
            text=f"{icon}  {self._file_info['name']}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        name_label.pack(side="left", fill="x", expand=True)

        size_label = ctk.CTkLabel(
            top_frame,
            text=format_size(self._file_info["size"]),
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            anchor="e",
        )
        size_label.pack(side="right")

        # Bottom row: directory + buttons
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=8, pady=(0, 6))

        dir_label = ctk.CTkLabel(
            bottom_frame,
            text=self._file_info.get("directory", ""),
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        dir_label.pack(side="left", fill="x", expand=True)

        if show_buttons:
            if self._zone == "new":
                # Show both Keep and Delete buttons
                del_btn = ctk.CTkButton(
                    bottom_frame,
                    text="🗑️ Delete",
                    width=70,
                    height=26,
                    font=ctk.CTkFont(size=11),
                    fg_color=COLORS["danger_red"],
                    hover_color=COLORS["delete_hover"],
                    command=self._handle_delete,
                )
                del_btn.pack(side="right", padx=(4, 0))

                keep_btn = ctk.CTkButton(
                    bottom_frame,
                    text="✅ Keep",
                    width=70,
                    height=26,
                    font=ctk.CTkFont(size=11),
                    fg_color=COLORS["success_green"],
                    hover_color=COLORS["keep_hover"],
                    command=self._handle_keep,
                )
                keep_btn.pack(side="right")

            elif self._zone == "keep":
                # Show undo button
                undo_btn = ctk.CTkButton(
                    bottom_frame,
                    text="↩ Undo",
                    width=60,
                    height=26,
                    font=ctk.CTkFont(size=11),
                    fg_color=COLORS["neutral_border"],
                    hover_color=COLORS["neutral_hover"],
                    command=self._handle_delete,  # Move back to unsorted
                )
                undo_btn.pack(side="right")

            elif self._zone == "delete":
                # Show undo button
                undo_btn = ctk.CTkButton(
                    bottom_frame,
                    text="↩ Undo",
                    width=60,
                    height=26,
                    font=ctk.CTkFont(size=11),
                    fg_color=COLORS["neutral_border"],
                    hover_color=COLORS["neutral_hover"],
                    command=self._handle_keep,  # Move back to unsorted
                )
                undo_btn.pack(side="right")

    def _handle_keep(self) -> None:
        if self._on_keep:
            self._on_keep(self._file_info)

    def _handle_delete(self) -> None:
        if self._on_delete:
            self._on_delete(self._file_info)


class EmptyStateWidget(ctk.CTkFrame):
    """Displays the 'Your memory is clean!' congratulatory message."""

    def __init__(self, parent: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._build_ui()

    def _build_ui(self) -> None:
        # Big emoji
        emoji = ctk.CTkLabel(
            self,
            text="🎉",
            font=ctk.CTkFont(size=60),
        )
        emoji.pack(pady=(40, 10))

        title = ctk.CTkLabel(
            self,
            text="Your memory is clean!",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["success_green"],
        )
        title.pack(pady=(0, 8))

        subtitle = ctk.CTkLabel(
            self,
            text=(
                "No new files were created during this session.\n"
                "Nothing to review — you're all set!"
            ),
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"],
            justify="center",
        )
        subtitle.pack(pady=(0, 40))


class SummaryBar(ctk.CTkFrame):
    """Shows summary counts: total, keep, delete, and total size to free."""

    def __init__(self, parent: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._labels: dict[str, ctk.CTkLabel] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        for key, text, color in [
            ("total", "📋 New: 0", COLORS["accent_blue"]),
            ("keep", "✅ Keep: 0", COLORS["success_green"]),
            ("delete", "🗑️ Delete: 0", COLORS["danger_red"]),
            ("size", "💾 Free: 0 B", COLORS["text_secondary"]),
        ]:
            label = ctk.CTkLabel(
                self,
                text=text,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=color,
            )
            label.pack(side="left", padx=15)
            self._labels[key] = label

    def update_counts(
        self, total: int, keep: int, delete: int, delete_size: int
    ) -> None:
        """Update all summary labels."""
        self._labels["total"].configure(text=f"📋 New: {total}")
        self._labels["keep"].configure(text=f"✅ Keep: {keep}")
        self._labels["delete"].configure(text=f"🗑️ Delete: {delete}")
        self._labels["size"].configure(text=f"💾 Free: {format_size(delete_size)}")
