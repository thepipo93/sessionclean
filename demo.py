"""Quick demo to preview the SessionClean UI."""

import time
from datetime import datetime
import customtkinter as ctk
from sessionclean.utils.file_utils import format_size, get_file_category

# Fake file data — with different dates to show the feature
now = time.time()
FAKE_FILES = [
    {"path": "C:\\Users\\crist\\Downloads\\report_final_v2.pdf", "name": "report_final_v2.pdf", "size": 2_400_000, "created_at": now - 3600, "file_type": "pdf", "directory": "C:\\Users\\crist\\Downloads"},
    {"path": "C:\\Users\\crist\\Downloads\\vacation_photo.jpg", "name": "vacation_photo.jpg", "size": 4_800_000, "created_at": now - 7200, "file_type": "jpg", "directory": "C:\\Users\\crist\\Downloads"},
    {"path": "C:\\Users\\crist\\Desktop\\meeting_notes.txt", "name": "meeting_notes.txt", "size": 12_000, "created_at": now - 1800, "file_type": "txt", "directory": "C:\\Users\\crist\\Desktop"},
    {"path": "C:\\Users\\crist\\Downloads\\setup_installer.exe", "name": "setup_installer.exe", "size": 85_000_000, "created_at": now - 900, "file_type": "exe", "directory": "C:\\Users\\crist\\Downloads"},
    {"path": "C:\\Users\\crist\\Downloads\\dataset.zip", "name": "dataset.zip", "size": 350_000_000, "created_at": now - 5400, "file_type": "zip", "directory": "C:\\Users\\crist\\Downloads"},
    {"path": "C:\\Users\\crist\\Documents\\proyecto\\main.py", "name": "main.py", "size": 3_200, "created_at": now - 600, "file_type": "py", "directory": "C:\\Users\\crist\\Documents\\proyecto"},
    {"path": "D:\\Downloads\\tutorial_video.mp4", "name": "tutorial_video.mp4", "size": 1_200_000_000, "created_at": now - 10800, "file_type": "mp4", "directory": "D:\\Downloads"},
    {"path": "C:\\Users\\crist\\Downloads\\song_mix.mp3", "name": "song_mix.mp3", "size": 8_500_000, "created_at": now - 300, "file_type": "mp3", "directory": "C:\\Users\\crist\\Downloads"},
]

CATEGORY_ICONS = {
    "Documents": "📄", "Images": "🖼️", "Videos": "🎬", "Audio": "🎵",
    "Archives": "📦", "Code": "💻", "Installers": "⚙️", "Other": "📁",
}

# ── App ──────────────────────────────────────────────────────────────
root = ctk.CTk()
root.title("SessionClean")
root.geometry("950x580")
root.minsize(800, 450)
ctk.set_appearance_mode("dark")

check_vars: dict[str, ctk.BooleanVar] = {}
selected_file: dict | None = None

# ── Header ───────────────────────────────────────────────────────────
header = ctk.CTkFrame(root, fg_color="transparent")
header.pack(fill="x", padx=20, pady=(15, 5))

ctk.CTkLabel(
    header, text="🧹 What did you download today?",
    font=ctk.CTkFont(size=18, weight="bold"),
).pack(side="left")

total_size = sum(f["size"] for f in FAKE_FILES)
ctk.CTkLabel(
    header,
    text=f"{len(FAKE_FILES)} files · {format_size(total_size)}",
    font=ctk.CTkFont(size=13), text_color="#aaaaaa",
).pack(side="right")

# Instructions
ctk.CTkLabel(
    root,
    text="Checked = KEEP.  Uncheck what you want to delete.",
    font=ctk.CTkFont(size=12), text_color="#777777",
).pack(padx=20, anchor="w")

# ── Quick actions ────────────────────────────────────────────────────
actions = ctk.CTkFrame(root, fg_color="transparent")
actions.pack(fill="x", padx=20, pady=(8, 4))


def select_all():
    for v in check_vars.values():
        v.set(True)


def deselect_all():
    for v in check_vars.values():
        v.set(False)


ctk.CTkButton(
    actions, text="Keep All", width=80, height=28,
    font=ctk.CTkFont(size=11), fg_color="#2ecc71", hover_color="#254d38",
    command=select_all,
).pack(side="left", padx=(0, 6))

ctk.CTkButton(
    actions, text="Delete All", width=80, height=28,
    font=ctk.CTkFont(size=11), fg_color="#555555", hover_color="#383838",
    command=deselect_all,
).pack(side="left")

summary_label = ctk.CTkLabel(
    actions, text="", font=ctk.CTkFont(size=12, weight="bold"),
    text_color="#e74c3c",
)
summary_label.pack(side="right")

# ── Main content: file list (left) + preview (right) ────────────────
content = ctk.CTkFrame(root, fg_color="transparent")
content.pack(fill="both", expand=True, padx=20, pady=8)
content.grid_columnconfigure(0, weight=3)
content.grid_columnconfigure(1, weight=2)

# ── Left: file list ─────────────────────────────────────────────────
scroll = ctk.CTkScrollableFrame(content, fg_color="#2b2b2b", corner_radius=10)
scroll.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

# ── Right: preview panel ────────────────────────────────────────────
preview = ctk.CTkFrame(content, fg_color="#2b2b2b", corner_radius=10)
preview.grid(row=0, column=1, sticky="nsew")

preview_title = ctk.CTkLabel(
    preview, text="File Preview",
    font=ctk.CTkFont(size=14, weight="bold"), text_color="#aaaaaa",
)
preview_title.pack(pady=(15, 10))

preview_icon = ctk.CTkLabel(
    preview, text="📁", font=ctk.CTkFont(size=48),
)
preview_icon.pack(pady=(10, 5))

preview_name = ctk.CTkLabel(
    preview, text="Select a file to preview",
    font=ctk.CTkFont(size=14, weight="bold"), text_color="#ffffff",
    wraplength=250,
)
preview_name.pack(pady=(5, 10))

# Preview detail labels
preview_details_frame = ctk.CTkFrame(preview, fg_color="transparent")
preview_details_frame.pack(fill="x", padx=20, pady=5)

detail_labels: dict[str, ctk.CTkLabel] = {}
for key, label_text in [
    ("size", "Size"),
    ("type", "Type"),
    ("location", "Location"),
    ("created", "Created"),
    ("status", "Status"),
]:
    row = ctk.CTkFrame(preview_details_frame, fg_color="transparent")
    row.pack(fill="x", pady=2)
    ctk.CTkLabel(
        row, text=f"{label_text}:", width=70, anchor="w",
        font=ctk.CTkFont(size=12), text_color="#777777",
    ).pack(side="left")
    val = ctk.CTkLabel(
        row, text="—", anchor="w",
        font=ctk.CTkFont(size=12), text_color="#cccccc",
        wraplength=200,
    )
    val.pack(side="left", fill="x", expand=True)
    detail_labels[key] = val


def show_preview(file_info: dict):
    category = get_file_category(file_info["path"])
    icon = CATEGORY_ICONS.get(category, "📁")
    preview_icon.configure(text=icon)
    preview_name.configure(text=file_info["name"])

    detail_labels["size"].configure(text=format_size(file_info["size"]))
    detail_labels["type"].configure(
        text=f"{category} (.{file_info.get('file_type', '?')})"
    )
    detail_labels["location"].configure(text=file_info.get("directory", ""))

    created_dt = datetime.fromtimestamp(file_info["created_at"])
    detail_labels["created"].configure(
        text=created_dt.strftime("%Y-%m-%d  %I:%M %p")
    )

    is_kept = check_vars.get(file_info["path"], ctk.BooleanVar(value=False)).get()
    if is_kept:
        detail_labels["status"].configure(text="✅ Keeping", text_color="#2ecc71")
    else:
        detail_labels["status"].configure(text="🗑️ Will be deleted", text_color="#e74c3c")


def update_summary(*_):
    keeping = sum(1 for v in check_vars.values() if v.get())
    deleting = len(FAKE_FILES) - keeping
    del_size = sum(
        f["size"] for f in FAKE_FILES
        if not check_vars.get(f["path"], ctk.BooleanVar(value=True)).get()
    )
    if deleting == 0:
        summary_label.configure(
            text=f"✅ Keeping all {keeping} files",
            text_color="#2ecc71",
        )
    else:
        summary_label.configure(
            text=f"🗑️ {deleting} to delete · {format_size(del_size)}",
            text_color="#e74c3c",
        )
    # Update preview status if a file is selected
    if selected_file:
        show_preview(selected_file)


# ── Render file rows ─────────────────────────────────────────────────
for file_info in FAKE_FILES:
    path = file_info["path"]
    var = ctk.BooleanVar(value=True)  # Checked = keep by default
    var.trace_add("write", update_summary)
    check_vars[path] = var

    row = ctk.CTkFrame(scroll, fg_color="transparent")
    row.pack(fill="x", pady=1)

    category = get_file_category(path)
    icon = CATEGORY_ICONS.get(category, "📁")

    cb = ctk.CTkCheckBox(
        row, text=f"{icon}  {file_info['name']}",
        variable=var, font=ctk.CTkFont(size=13),
    )
    cb.pack(side="left", padx=(8, 4), pady=4)

    # Created time
    created_dt = datetime.fromtimestamp(file_info["created_at"])
    time_str = created_dt.strftime("%I:%M %p")

    ctk.CTkLabel(
        row, text=format_size(file_info["size"]),
        font=ctk.CTkFont(size=11), text_color="#777777",
    ).pack(side="right", padx=(0, 10))

    ctk.CTkLabel(
        row, text=time_str,
        font=ctk.CTkFont(size=11), text_color="#555555",
    ).pack(side="right", padx=(0, 8))

    # Click row to show preview
    def make_click_handler(fi=file_info):
        def handler(event):
            nonlocal selected_file
            selected_file = fi
            show_preview(fi)
        return handler

    row.bind("<Button-1>", make_click_handler())
    for child in row.winfo_children():
        child.bind("<Button-1>", make_click_handler(), add="+")

# ── Confirm button ───────────────────────────────────────────────────
ctk.CTkButton(
    root, text="✅ Confirm & Clean",
    font=ctk.CTkFont(size=14, weight="bold"), height=45,
    fg_color="#2ecc71", hover_color="#254d38",
    command=lambda: root.quit(),
).pack(fill="x", padx=20, pady=(4, 15))

update_summary()
root.mainloop()
