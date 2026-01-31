"""Main cleanup window — simple checklist interface.

All files checked by default (= keep). Uncheck what you want to delete.
Click on a file to see its details in the preview panel.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from datetime import datetime

import customtkinter as ctk
from send2trash import send2trash

from sessionclean.gui.widgets import COLORS, EmptyStateWidget
from sessionclean.utils.file_utils import format_size, get_file_category

logger = logging.getLogger("sessionclean")

CATEGORY_ICONS: dict[str, str] = {
    "Documents": "📄", "Images": "🖼️", "Videos": "🎬", "Audio": "🎵",
    "Archives": "📦", "Code": "💻", "Installers": "⚙️", "Other": "📁",
}


class CleanupWindow(ctk.CTkToplevel):
    """Cleanup interface: checklist + preview panel.

    - All files CHECKED by default (= keep).
    - Uncheck a file to DELETE it.
    - Click a file row to see details in the preview panel.
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
        self._check_vars: dict[str, ctk.BooleanVar] = {}
        self._selected_file: dict | None = None

        self.title("SessionClean")
        self.geometry("950x580")
        self.minsize(800, 450)
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
        EmptyStateWidget(self).pack(fill="both", expand=True)
        btn_text = "Shut Down" if self._is_shutdown else "Close"
        ctk.CTkButton(
            self, text=btn_text,
            font=ctk.CTkFont(size=15, weight="bold"), height=45,
            fg_color=COLORS["success_green"],
            hover_color=COLORS["keep_hover"],
            command=self._confirm_empty,
        ).pack(pady=(0, 20), padx=20)

    # ------------------------------------------------------------------
    # Main UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))

        ctk.CTkLabel(
            header, text="🧹 What did you download today?",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(side="left")

        total_size = sum(f.get("size", 0) for f in self._all_files)
        ctk.CTkLabel(
            header,
            text=f"{len(self._all_files)} files · {format_size(total_size)}",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"],
        ).pack(side="right")

        ctk.CTkLabel(
            self,
            text="Checked = KEEP.  Uncheck what you want to delete.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        ).pack(padx=20, anchor="w")

        # Quick actions
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=(8, 4))

        ctk.CTkButton(
            actions, text="Keep All", width=80, height=28,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["success_green"],
            hover_color=COLORS["keep_hover"],
            command=self._select_all,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            actions, text="Delete All", width=80, height=28,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["neutral_border"],
            hover_color=COLORS["neutral_hover"],
            command=self._deselect_all,
        ).pack(side="left")

        self._summary_label = ctk.CTkLabel(
            actions, text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["success_green"],
        )
        self._summary_label.pack(side="right")

        # Main content: file list (left) + preview (right)
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=8)
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        # Left: file list
        self._scroll = ctk.CTkScrollableFrame(
            content, fg_color=COLORS["neutral_bg"], corner_radius=10,
        )
        self._scroll.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Right: preview panel
        self._preview = ctk.CTkFrame(
            content, fg_color=COLORS["neutral_bg"], corner_radius=10,
        )
        self._preview.grid(row=0, column=1, sticky="nsew")
        self._build_preview_panel()

        # Render files
        self._render_file_list()

        # Confirm button
        btn_text = (
            "✅ Confirm & Clean"
            if self._is_shutdown
            else "✅ Confirm & Clean"
        )
        self._confirm_btn = ctk.CTkButton(
            self, text=btn_text,
            font=ctk.CTkFont(size=14, weight="bold"), height=45,
            fg_color=COLORS["success_green"],
            hover_color=COLORS["keep_hover"],
            command=self._confirm_and_close,
        )
        self._confirm_btn.pack(fill="x", padx=20, pady=(4, 15))

        self._update_summary()

    # ------------------------------------------------------------------
    # Preview panel
    # ------------------------------------------------------------------
    def _build_preview_panel(self) -> None:
        p = self._preview

        ctk.CTkLabel(
            p, text="File Preview",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_secondary"],
        ).pack(pady=(15, 10))

        self._preview_icon = ctk.CTkLabel(
            p, text="📁", font=ctk.CTkFont(size=48),
        )
        self._preview_icon.pack(pady=(10, 5))

        self._preview_name = ctk.CTkLabel(
            p, text="Select a file to preview",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"], wraplength=250,
        )
        self._preview_name.pack(pady=(5, 10))

        details_frame = ctk.CTkFrame(p, fg_color="transparent")
        details_frame.pack(fill="x", padx=20, pady=5)

        self._detail_labels: dict[str, ctk.CTkLabel] = {}
        for key, label_text in [
            ("size", "Size"), ("type", "Type"),
            ("location", "Location"), ("created", "Created"),
            ("status", "Status"),
        ]:
            row = ctk.CTkFrame(details_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(
                row, text=f"{label_text}:", width=70, anchor="w",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_muted"],
            ).pack(side="left")
            val = ctk.CTkLabel(
                row, text="—", anchor="w",
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_secondary"],
                wraplength=200,
            )
            val.pack(side="left", fill="x", expand=True)
            self._detail_labels[key] = val

    def _show_preview(self, file_info: dict) -> None:
        self._selected_file = file_info
        category = get_file_category(file_info["path"])
        icon = CATEGORY_ICONS.get(category, "📁")

        self._preview_icon.configure(text=icon)
        self._preview_name.configure(text=file_info["name"])
        self._detail_labels["size"].configure(
            text=format_size(file_info["size"])
        )
        self._detail_labels["type"].configure(
            text=f"{category} (.{file_info.get('file_type', '?')})"
        )
        self._detail_labels["location"].configure(
            text=file_info.get("directory", "")
        )

        created_dt = datetime.fromtimestamp(file_info["created_at"])
        self._detail_labels["created"].configure(
            text=created_dt.strftime("%Y-%m-%d  %I:%M %p")
        )

        is_kept = self._check_vars.get(
            file_info["path"], ctk.BooleanVar(value=True)
        ).get()
        if is_kept:
            self._detail_labels["status"].configure(
                text="✅ Keeping", text_color=COLORS["success_green"],
            )
        else:
            self._detail_labels["status"].configure(
                text="🗑️ Will be deleted", text_color=COLORS["danger_red"],
            )

    # ------------------------------------------------------------------
    # File list
    # ------------------------------------------------------------------
    def _render_file_list(self) -> None:
        for file_info in self._all_files:
            path = file_info["path"]
            var = ctk.BooleanVar(value=True)  # Checked = keep
            var.trace_add("write", lambda *_: self._update_summary())
            self._check_vars[path] = var

            row = ctk.CTkFrame(self._scroll, fg_color="transparent")
            row.pack(fill="x", pady=1)

            category = get_file_category(path)
            icon = CATEGORY_ICONS.get(category, "📁")

            ctk.CTkCheckBox(
                row, text=f"{icon}  {file_info['name']}",
                variable=var, font=ctk.CTkFont(size=13),
                text_color=COLORS["text_primary"],
            ).pack(side="left", padx=(8, 4), pady=4)

            ctk.CTkLabel(
                row, text=format_size(file_info["size"]),
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_muted"],
            ).pack(side="right", padx=(0, 10))

            created_dt = datetime.fromtimestamp(file_info["created_at"])
            ctk.CTkLabel(
                row, text=created_dt.strftime("%I:%M %p"),
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_muted"],
            ).pack(side="right", padx=(0, 8))

            # Click to preview
            handler = self._make_click_handler(file_info)
            row.bind("<Button-1>", handler)
            for child in row.winfo_children():
                child.bind("<Button-1>", handler, add="+")

    def _make_click_handler(self, fi: dict):
        def handler(event):
            self._show_preview(fi)
        return handler

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _select_all(self) -> None:
        for var in self._check_vars.values():
            var.set(True)

    def _deselect_all(self) -> None:
        for var in self._check_vars.values():
            var.set(False)

    def _update_summary(self) -> None:
        if not hasattr(self, "_summary_label"):
            return
        keeping = sum(1 for v in self._check_vars.values() if v.get())
        deleting = len(self._all_files) - keeping
        del_size = sum(
            f["size"] for f in self._all_files
            if not self._check_vars.get(
                f["path"], ctk.BooleanVar(value=True)
            ).get()
        )
        if deleting == 0:
            self._summary_label.configure(
                text=f"✅ Keeping all {keeping} files",
                text_color=COLORS["success_green"],
            )
        else:
            self._summary_label.configure(
                text=f"🗑️ {deleting} to delete · {format_size(del_size)}",
                text_color=COLORS["danger_red"],
            )
        if self._selected_file:
            self._show_preview(self._selected_file)

    # ------------------------------------------------------------------
    # Confirm / Close
    # ------------------------------------------------------------------
    def _confirm_and_close(self) -> None:
        keep = []
        delete = []
        for f in self._all_files:
            if self._check_vars[f["path"]].get():
                keep.append(f["path"])
            else:
                delete.append(f["path"])

        if delete:
            self._confirm_btn.configure(
                text="🔄 Cleaning up...", state="disabled",
            )
            threading.Thread(
                target=self._execute_deletions,
                args=(keep, delete), daemon=True,
            ).start()
        else:
            self._finish(keep, delete)

    def _execute_deletions(self, keep: list[str], delete: list[str]) -> None:
        deleted = []
        for path in delete:
            try:
                send2trash(path)
                deleted.append(path)
                logger.info("Sent to Recycle Bin: %s", path)
            except Exception as exc:
                logger.error("Failed to delete %s: %s", path, exc)
        self.after(0, lambda: self._finish(keep, deleted))

    def _finish(self, keep: list[str], delete: list[str]) -> None:
        self._on_complete(keep, delete)
        self.destroy()

    def _confirm_empty(self) -> None:
        self._on_complete([], [])
        self.destroy()

    def _on_close(self) -> None:
        all_paths = [f["path"] for f in self._all_files]
        self._on_complete(all_paths, [])
        self.destroy()
