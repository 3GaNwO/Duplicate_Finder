#################################################################################
##                                                                             ##
##                         OwNaG3's Duplicate Finder                           ##
##                   Finds Duplicate Files to Delete or Move                   ##
##                        Copyright (C) 2025 OwNaG3                            ## 
##                                                                             ##
##    This program is free software: you can redistribute it and/or modify     ##
##    it under the terms of the GNU General Public License as published by     ##
##    the Free Software Foundation, either version 3 of the License, or        ##
##    (at your option) any later version.                                      ##
##                                                                             ##
##    This program is distributed in the hope that it will be useful,          ##
##    but WITHOUT ANY WARRANTY; without even the implied warranty of           ##
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            ##
##    GNU General Public License for more details.                             ##
##                                                                             ##
##    You should have received a copy of the GNU General Public License        ##
##    along with this program.  If not, see <https://www.gnu.org/licenses/>.   ##
##                                                                             ##
#################################################################################


import os
import hashlib
import threading
import queue
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog, messagebox, simpledialog
import subprocess
import csv
import json
import time
import sys
import shutil
import random
import datetime
import traceback
import uuid

try:
    from ttkthemes import ThemedStyle
    THEMES_AVAILABLE = True
except ImportError:
    THEMES_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    import send2trash
    SEND2TRASH_AVAILABLE = True
except ImportError:
    SEND2TRASH_AVAILABLE = False


class DuplicateFinderApp:
    SETTINGS_FILE = "settings.json"
    DELETE_HISTORY_MAX = 999999999
    DELETE_AUTO_CLEAN_DAYS_DEFAULT = 5

    def __init__(self, root):
        self.root = root
        self.root.title("OwNaG3s Duplicate Finder")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        self.auto_cleanup_enabled = tk.BooleanVar(value=True)
        self.auto_cleanup_days = tk.IntVar(value=7)

        self.scanning_thread = None
        self.scan_stop_event = threading.Event()
        self.scan_pause_event = threading.Event()  

        self.duplicates = {}
        self.selected_files = set()
        self.delete_history = []  
        self.delete_to_recycle = tk.BooleanVar(value=True)
        self.hash_size = tk.IntVar(value=8 * 1024 * 1024)
        self.hash_dict = {}
        self.tree_items = {}
        self.scan_queue = queue.Queue()
        self.move_history = []
        self.total_files_to_scan = 0
        self.files_scanned = 0

        self.music_files = []
        self.music_index = 0
        self.is_paused = False
        self.is_stopped = True
        self.repeat_current = tk.BooleanVar(value=False)
        self.shuffle_enabled = tk.BooleanVar(value=False)
        self.volume_level = tk.DoubleVar(value=0.5)
        self.current_song_label_var = tk.StringVar(value="No song playing")

        self.last_scan_folder = os.path.expanduser("~")
        self.last_import_folder = os.path.expanduser("~")
        self.last_export_folder = os.path.expanduser("~")
        self.last_music_folder = os.path.expanduser("~")

        self.is_closing = False

        self.size_sort_descending = False
        self.filepath_sort_descending = False
        self.group_sort_descending = False

        if PYGAME_AVAILABLE:
            pygame.mixer.init()
            pygame.mixer.music.set_volume(self.volume_level.get())

        if THEMES_AVAILABLE:
            self.style = ThemedStyle(self.root)
            available = list(self.style.theme_names())
            if "equilux" in available:
                default_theme = "equilux"
            else:
                default_theme = self.style.theme_use()
            self.available_themes = sorted(available)
            self.theme_var = tk.StringVar(value=default_theme)
            self.style.set_theme(self.theme_var.get())
        else:
            self.style = ttk.Style(self.root)
            self.available_themes = sorted(self.style.theme_names())
            self.theme_var = tk.StringVar(value=self.style.theme_use())

        self.checkbox_vars = {}
        self.tree_items = {}

        # For drag select toggle
        self.drag_select_start = None
        self.drag_last_selected = set()
        self.drag_deselect_mode = False 
        self.dragging = False		

        self.delete_auto_clean_days = self.DELETE_AUTO_CLEAN_DAYS_DEFAULT

        self.build_menu()
        self.build_gui()

        self.settings = self.load_settings()

        # Undo backup folder: fallback to default if not set in settings
        self.undo_backup_folder = self.settings.get(
            "undo_backup_folder", os.path.join(os.getcwd(), "undo_backups")
        )

        self.load_delete_history_and_cleanup()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(100, self.process_scan_results)
        if PYGAME_AVAILABLE:
            self.root.after(500, self.check_music_end)

    def build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Select Folder", command=self.select_folder)
        file_menu.add_command(label="Undo Move/Delete", command=self.show_undo_dialog)
        file_menu.add_separator()

        # Export submenu
        export_menu = tk.Menu(file_menu, tearoff=0)
        export_menu.add_command(label="Export as CSV", command=self.export_scan_csv)
        export_menu.add_command(label="Export as JSON", command=self.export_scan_json)
        file_menu.add_cascade(label="Export Scan", menu=export_menu)

        # Import submenu
        import_menu = tk.Menu(file_menu, tearoff=0)
        import_menu.add_command(label="Import from CSV", command=self.import_scan_csv)
        import_menu.add_command(label="Import from JSON", command=self.import_scan_json)
        file_menu.add_cascade(label="Import Scan", menu=import_menu)

        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        settings_menu = tk.Menu(menubar, tearoff=0)
        hash_menu = tk.Menu(settings_menu, tearoff=0)
        for label, val in [("512 KB", 512 * 1024), ("1 MB", 1024 * 1024), ("2 MB", 2 * 1024 * 1024), ("8 MB", 8 * 1024 * 1024), ("Full File", 0)]:
            hash_menu.add_radiobutton(label=label, value=val, variable=self.hash_size, command=self.on_hash_size_change)
        settings_menu.add_cascade(label="Hash Read Size", menu=hash_menu)
        settings_menu.add_checkbutton(label="Delete to Recycle Bin", variable=self.delete_to_recycle,
                                      command=self.sync_delete_recycle_checkbox)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Preferences", command=self.show_preferences_dialog)
        settings_menu.add_command(label="Move Duplicates to Folder", command=self.move_selected_files)

        theme_menu = tk.Menu(menubar, tearoff=0)
        for theme in self.available_themes:
            theme_menu.add_radiobutton(label=theme.title(), variable=self.theme_var, value=theme, command=self.change_theme)
        menubar.add_cascade(label="Themes", menu=theme_menu)

        music_menu = tk.Menu(menubar, tearoff=0)
        music_menu.add_command(label="Choose Song", command=self.choose_song)
        music_menu.add_separator()
        music_menu.add_command(label="Play", command=self.play_music)
        music_menu.add_command(label="Pause/Resume", command=self.toggle_pause_resume)
        music_menu.add_command(label="Stop", command=self.stop_music)
        music_menu.add_command(label="Next", command=self.next_music)
        music_menu.add_separator()
        music_menu.add_checkbutton(label="Repeat Current Song", variable=self.repeat_current)
        music_menu.add_checkbutton(label="Shuffle", variable=self.shuffle_enabled)
        menubar.add_cascade(label="Music", menu=music_menu)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Info", command=self.show_about_dialog)
        menubar.add_cascade(label="About", menu=help_menu)
        
        self.root.config(menu=menubar)

    def on_hash_size_change(self):
        self.save_settings()

    def sync_delete_recycle_checkbox(self):
        val = self.delete_to_recycle.get()
        self.delete_to_recycle.set(val)

    def build_gui(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        self.folder_path_var = tk.StringVar()
        folder_entry = ttk.Entry(top_frame, textvariable=self.folder_path_var)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        folder_entry.bind("<Return>", lambda e: self.start_scan())

        browse_btn = ttk.Button(top_frame, text="Browse...", command=self.select_folder)
        browse_btn.pack(side=tk.LEFT, padx=5)

        self.select_dupes_var = tk.BooleanVar()
        select_dupes_chk = ttk.Checkbutton(
            top_frame, text="Select all duplicates except one", variable=self.select_dupes_var,
            command=self.toggle_select_dupes
        )
        select_dupes_chk.pack(side=tk.LEFT, padx=5)

        scan_ctrl_frame = ttk.Frame(self.root)
        scan_ctrl_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        self.clean_empty_folders_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            scan_ctrl_frame, text="Clean empty folders after scan", variable=self.clean_empty_folders_var
        ).pack(side="left", padx=10)

        self.pause_scan_btn = ttk.Button(scan_ctrl_frame, text="Pause Scan", command=self.toggle_pause_resume_scan, state=tk.DISABLED)
        self.pause_scan_btn.pack(side=tk.LEFT, padx=5)

        self.cancel_scan_btn = ttk.Button(scan_ctrl_frame, text="Cancel Scan", command=self.cancel_scan, state=tk.DISABLED)
        self.cancel_scan_btn.pack(side=tk.LEFT, padx=5)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(scan_ctrl_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # -- Treeview with Scrollbars --
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("Select", "File Path", "Size", "Group")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="extended")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        def smooth_mousewheel(event):
            if event.delta:
                self.tree.yview_scroll(int(-1 * (event.delta / 120) * 3), "units")
            else:
                if event.num == 4:
                    self.tree.yview_scroll(-3, "units")
                elif event.num == 5:
                    self.tree.yview_scroll(3, "units")

        self.tree.bind("<MouseWheel>", smooth_mousewheel)  # Windows and macOS
        self.tree.bind("<Button-4>", smooth_mousewheel)    # Linux scroll up
        self.tree.bind("<Button-5>", smooth_mousewheel)    # Linux scroll down

        self.tree.heading("Select", text="✔", anchor=tk.CENTER)
        self.tree.column("Select", width=20, anchor=tk.CENTER)

        self.tree.heading("File Path", text="File Path", anchor=tk.CENTER, command=self.sort_by_filepath)
        self.tree.column("File Path", width=500, anchor=tk.W)

        self.tree.heading("Size", text="Size", anchor=tk.CENTER, command=self.sort_by_size)
        self.tree.column("Size", width=100, anchor=tk.CENTER)

        self.tree.heading("Group", text="Group", anchor=tk.CENTER, command=self.sort_by_group)
        self.tree.column("Group", width=20, anchor=tk.CENTER)

        self.tree.bind("<Button-1>", self.handle_click)
        self.tree.bind("<ButtonRelease-1>", self.handle_drag_release)
        self.tree.bind("<B1-Motion>", self.handle_drag_motion)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", self.handle_double_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        open_folder_btn = ttk.Button(btn_frame, text="Open Folder", command=self.open_selected_file_folder)
        open_folder_btn.pack(side=tk.LEFT, padx=5)

        preview_btn = ttk.Button(btn_frame, text="Preview Selected", command=self.preview_selected_files)
        preview_btn.pack(side=tk.LEFT, padx=5)

        delete_btn = ttk.Button(btn_frame, text="Delete Selected", command=self.delete_selected_files)
        delete_btn.pack(side=tk.LEFT, padx=5)

        move_btn = ttk.Button(btn_frame, text="Move Duplicates", command=self.move_selected_files)
        move_btn.pack(side=tk.LEFT, padx=5)

        undo_history_btn = ttk.Button(btn_frame, text="Undo Move/Delete", command=self.show_undo_dialog)
        undo_history_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = ttk.Label(self.root, text="Ready.")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

        if PYGAME_AVAILABLE:
            music_frame = ttk.Frame(self.root)
            music_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

            ttk.Button(music_frame, text="Choose Song", command=self.choose_song).pack(side=tk.LEFT, padx=2)
            ttk.Checkbutton(music_frame, text="Repeat", variable=self.repeat_current).pack(side=tk.LEFT, padx=5)
            ttk.Checkbutton(music_frame, text="Shuffle", variable=self.shuffle_enabled).pack(side=tk.LEFT, padx=5)
            self.pause_btn = ttk.Button(music_frame, text="Pause", command=self.toggle_pause_resume)
            self.pause_btn.pack(side=tk.LEFT, padx=2)
            ttk.Button(music_frame, text="Next", command=self.next_music).pack(side=tk.LEFT, padx=2)
            ttk.Label(music_frame, text="Volume").pack(side=tk.LEFT, padx=(20, 2))
            volume_slider = ttk.Scale(
                music_frame, from_=0, to=1, orient=tk.HORIZONTAL, variable=self.volume_level,
                command=self.change_volume
            )
            volume_slider.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
            self.current_song_label = ttk.Label(music_frame, textvariable=self.current_song_label_var, width=40, anchor=tk.W)
            self.current_song_label.pack(side=tk.LEFT, padx=10)

        self.tree.tag_configure("selected", background="#cce6ff")

    def show_about_dialog(self):
        messagebox.showinfo(
            "OwNaG3's Duplicate Finder",
            "OwNaG3's Duplicate Finder\nVersion 1.6.6.6\n\nDeveloped by OwNaG3\n© 2025 All Rights Reserved"
        )

    # -- Preferences Dialog --

    def show_preferences_dialog(self):
        pref_win = tk.Toplevel(self.root)
        pref_win.title("Preferences")
        pref_win.geometry("400x200")
        pref_win.resizable(True, True)  

        frame = ttk.Frame(pref_win, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")  

        pref_win.columnconfigure(0, weight=1)
        pref_win.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        # Widgets
        ttk.Checkbutton(
            frame,
            text="Enable automatic cleanup of undo backups",
           variable=self.auto_cleanup_enabled
        ).grid(row=0, column=0, sticky="w", pady=5)

        ttk.Label(frame, text="Days to keep undo delete backup:").grid(row=1, column=0, sticky="w", pady=(10, 0))

        days_spin = ttk.Spinbox(
            frame, from_=1, to=365, textvariable=self.auto_cleanup_days, width=5
        )
        days_spin.grid(row=2, column=0, sticky="w", pady=5)

        def choose_folder():
            path = filedialog.askdirectory(title="Select Undo Backup Folder")
            if path:
                auto_backup_path = os.path.join(path, "auto_backups")
                os.makedirs(auto_backup_path, exist_ok=True)
                self.undo_backup_folder = os.path.normpath(auto_backup_path)
                self.save_settings()
                print(f"Saved undo backup folder: {self.undo_backup_folder}")
                pref_win.destroy()

        # Button Frame
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, pady=(15, 0), sticky="e")

        ttk.Button(
            button_frame,
            text="Choose Undo Backup Folder",
            command=choose_folder
        ).pack(side="left", padx=(0, 10))

        done_font = tkfont.Font(size=12, weight="normal")
        style = ttk.Style()
        style.configure("Done.TButton", font=done_font)

        ttk.Button(
            button_frame,
            text="Done",
            width=10,
            command=pref_win.destroy,
            style="Done.TButton"
        ).pack(side="left")

    # -- Folder selection Logic --

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder", initialdir=self.last_scan_folder)
        if folder:
            self.last_scan_folder = folder
            self.folder_path_var.set(folder)
            self.start_scan()

    # -- Music Player Logic --

    def choose_song(self):
        initial_dir = self.last_music_folder if self.last_music_folder and os.path.exists(self.last_music_folder) else os.path.expanduser("~")
        filetypes = [("Audio Files", "*.mp3 *.wav *.ogg"), ("All Files", "*.*")]
        song = filedialog.askopenfilename(title="Choose Music File", initialdir=initial_dir, filetypes=filetypes)
        if song:
            self.last_music_folder = os.path.dirname(song)
            folder = self.last_music_folder
            exts = {".mp3", ".wav", ".ogg"}
            self.music_files = [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if os.path.splitext(f)[1].lower() in exts]
            try:
                self.music_index = self.music_files.index(song)
            except ValueError:
                self.music_index = 0
            self.play_music()

    def play_music(self):
        if not self.music_files:
            messagebox.showinfo("No Music", "No music loaded. Please choose a song first.")
            return
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.is_stopped = False
            self.pause_btn.config(text="Pause")
            self.update_current_song_label()
            return
        try:
            pygame.mixer.music.load(self.music_files[self.music_index])
            pygame.mixer.music.play()
            self.is_paused = False
            self.is_stopped = False
            self.pause_btn.config(text="Pause")
            self.update_current_song_label()
        except Exception as e:
            messagebox.showerror("Play Failed", f"Failed to play music:\n{e}")

    def toggle_pause_resume(self):
        if self.is_stopped:
            self.play_music()
            return
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.pause_btn.config(text="Pause")
            self.status_label.config(text="Music resumed.")
        else:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.pause_btn.config(text="Resume")
            self.status_label.config(text="Music paused.")

    def stop_music(self):
        if PYGAME_AVAILABLE:
            pygame.mixer.music.stop()
            self.is_paused = False
            self.is_stopped = True
            self.pause_btn.config(text="Pause")
            self.status_label.config(text="Music stopped.")
            self.current_song_label_var.set("No song playing")

    def next_music(self):
        if not self.music_files:
            return
        if self.shuffle_enabled.get():
            self.music_index = random.randint(0, len(self.music_files) - 1)
        else:
            self.music_index = (self.music_index + 1) % len(self.music_files)
        self.play_music()

    def check_music_end(self):
        if PYGAME_AVAILABLE and not self.is_stopped and not self.is_paused:
            if not pygame.mixer.music.get_busy():
                if self.repeat_current.get():
                    self.play_music()
                else:
                    self.next_music()
        self.root.after(500, self.check_music_end)

    def change_volume(self, _event=None):
        vol = self.volume_level.get()
        if PYGAME_AVAILABLE:
            pygame.mixer.music.set_volume(vol)

    def update_current_song_label(self):
        if self.music_files:
            filename = os.path.basename(self.music_files[self.music_index])
            self.current_song_label_var.set(f"Playing: {filename}")
        else:
            self.current_song_label_var.set("No song playing")

    # -- Scanning Logic --

    def start_scan(self):
        folder = self.folder_path_var.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("Invalid Folder", "Please select a valid folder to scan.")
            return

        if self.scanning_thread and self.scanning_thread.is_alive():
            self.scan_stop_event.set()
            self.scanning_thread.join(timeout=5)
            self.scanning_thread = None

        self.clear_scan_queue()
        self.scan_stop_event.clear()
        self.scan_pause_event.clear()

        self.duplicates = {}
        self.selected_files.clear()
        self.tree.delete(*self.tree.get_children())
        self.tree_items.clear()
        self.files_scanned = 0
        self.total_files_to_scan = 0
        self.progress_var.set(0)
        self.status_label.config(text="Scanning...")

        self.pause_scan_btn.config(state=tk.NORMAL, text="Pause Scan")
        self.cancel_scan_btn.config(state=tk.NORMAL)

        self.scanning_thread = threading.Thread(target=self.scan_folder, args=(folder,))
        self.scanning_thread.daemon = True
        self.scanning_thread.start()

    def scan_folder(self, folder):
        self.last_scan_folder = folder 

        size_dict = {}
        total_files_found = 0

        for root_dir, dirs, files in os.walk(folder):
            if self.scan_stop_event.is_set():
                self.scan_queue.put(("cancelled", None, total_files_found))
                print("Scan cancelled during folder walk.")
                return

            for file in files:
                if self.scan_stop_event.is_set():
                    self.scan_queue.put(("cancelled", None, total_files_found))
                    print("Scan cancelled during file iteration.")
                    return

                filepath = os.path.join(root_dir, file)
                total_files_found += 1
                try:
                    size = os.path.getsize(filepath)
                    size_dict.setdefault(size, []).append(filepath)
                except Exception:
                    pass

        self.total_files_found = total_files_found

        candidates = [files for files in size_dict.values() if len(files) > 1]
        files_to_hash = [f for group in candidates for f in group]
        total_files_hashed = len(files_to_hash)

        self.total_files_hashed = total_files_hashed
        self.total_files_to_scan = total_files_hashed
        self.files_scanned = 0
        self.status_label.config(text=f"Scanning {total_files_hashed} candidate files for duplicates...")

        hashes = {}
        for filepath in files_to_hash:
            if self.scan_stop_event.is_set():
                self.scan_queue.put(("cancelled", None, self.total_files_found))
                print("Scan cancelled during hashing.")
                return
            while self.scan_pause_event.is_set():
                time.sleep(0.1)
            try:
                file_hash = self.hash_file(filepath, self.hash_size.get())
            except Exception:
                file_hash = None
            if file_hash:
                hashes.setdefault(file_hash, []).append(filepath)
            self.files_scanned += 1
            self.scan_queue.put(("progress", self.files_scanned, self.total_files_to_scan))

        self.duplicates = {h: files for h, files in hashes.items() if len(files) > 1}
        self.scan_queue.put(("done", self.duplicates, self.total_files_found))
        print("Scan completed normally.")

    def clear_scan_queue(self):
        try:
            while True:
                self.scan_queue.get_nowait()
        except queue.Empty:
            pass

    def process_scan_results(self):
        try:
            while True:
                item = self.scan_queue.get_nowait()
                if item[0] == "progress":
                    scanned, total = item[1], item[2]
                    percent = (scanned / total) * 100 if total else 0
                    self.progress_var.set(percent)
                    self.status_label.config(text=f"Scanning files: {scanned} / {total}")
                elif item[0] == "done":
                    duplicates = item[1]
                    total_files_found = item[2] if len(item) > 2 else 0
                    duplicate_count = sum(len(v) for v in duplicates.values())
                    group_count = len(duplicates)

                    self.progress_var.set(100)
                    self.populate_tree(duplicates)
                    self.pause_scan_btn.config(state=tk.DISABLED)
                    self.cancel_scan_btn.config(state=tk.DISABLED)
                    status_text = (
                        f"Scan complete. Scanned: {total_files_found} files. "
                        f"Found {duplicate_count} duplicate files in {group_count} groups."
                    )

                    if self.clean_empty_folders_var.get() and self.last_scan_folder:
                        cleaned = self.clean_empty_folders(self.last_scan_folder)
                        status_text += f" Removed {cleaned} empty folders."
                    self.status_label.config(text=status_text)
        except queue.Empty:
            pass
        if not self.is_closing:
            self.root.after(100, self.process_scan_results)

    def clean_empty_folders(self, root_folder):
        removed_count = 0
        for dirpath, dirnames, filenames in os.walk(root_folder, topdown=False):
            try:
                if not os.listdir(dirpath):
                    lower_path = dirpath.lower()
                    skip_keywords = [".git", "windows", "system", "program files", "appdata", "temp", "cache"]
                    if any(skip_word in lower_path for skip_word in skip_keywords):
                        continue
                    os.rmdir(dirpath)
                    removed_count += 1
            except Exception as e:
                print(f"Failed to remove {dirpath}: {e}")
        return removed_count

    def cancel_scan(self):
        if messagebox.askyesno("Cancel Scan", "Are you sure you want to cancel the ongoing scan?"):
            self.scan_stop_event.set()  
            self.pause_scan_btn.config(state=tk.DISABLED)
            self.cancel_scan_btn.config(state=tk.DISABLED)
            self.status_label.config(text="Scan cancelled.")
            self.progress_var.set(0)

            if self.scanning_thread and self.scanning_thread.is_alive():
                self.scanning_thread.join(timeout=5)
                self.scanning_thread = None

            self.clear_scan_queue()

    def toggle_pause_resume_scan(self):
        if self.scan_pause_event.is_set():
            self.scan_pause_event.clear()
            self.pause_scan_btn.config(text="Pause Scan")
            self.status_label.config(text="Resuming scan...")
        else:
            self.scan_pause_event.set()
            self.pause_scan_btn.config(text="Resume Scan")
            self.status_label.config(text="Scan paused.")

    def hash_file(self, filepath, hash_size):
        hasher = hashlib.md5()
        with open(filepath, "rb") as f:
            if hash_size == 0:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    hasher.update(chunk)
            else:
                data = f.read(hash_size)
                hasher.update(data)
        return hasher.hexdigest()

    def populate_tree(self, duplicates):
        self.tree.delete(*self.tree.get_children())
        self.tree_items.clear()
        group_num = 1
        for group_id, files in duplicates.items():
            for i, filepath in enumerate(files):
                size_bytes = 0
                try:
                    size_bytes = os.path.getsize(filepath)
                except Exception:
                    pass
                size_str = self.format_size(size_bytes)
                select_val = ""
                tags = ()
                row_id = self.tree.insert("", "end", values=(select_val, filepath, size_str, group_num), tags=tags)
                self.tree_items[filepath] = row_id
            group_num += 1
        self.status_label.config(text=f"Loaded {sum(len(v) for v in duplicates.values())} duplicates in {len(duplicates)} groups.")
        self.toggle_select_dupes() 

    def format_size(self, size_bytes):
        try:
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 ** 2:
                return f"{size_bytes / 1024:.2f} KB"
            elif size_bytes < 1024 ** 3:
                return f"{size_bytes / (1024 ** 2):.2f} MB"
            else:
                return f"{size_bytes / (1024 ** 3):.2f} GB"
        except Exception:
            return "0 B"

    def toggle_select_dupes(self):
        if self.select_dupes_var.get():
            groups = {}
            for filepath, row_id in self.tree_items.items():
                group = self.tree.set(row_id, "Group")
                groups.setdefault(group, []).append((filepath, row_id))
            self.selected_files.clear()
            for group_files in groups.values():
                for filepath, row_id in group_files[1:]:
                    self.selected_files.add(filepath)
                    self.tree.set(row_id, "Select", "✔")
                    self.tree.item(row_id, tags=("selected",))
                filepath, row_id = group_files[0]
                self.tree.set(row_id, "Select", "")
                self.tree.item(row_id, tags=())
        else:
            self.selected_files.clear()
            for row_id in self.tree.get_children():
                self.tree.set(row_id, "Select", "")
                self.tree.item(row_id, tags=())

    # -- Treeview selection handling --

    def handle_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            return

        row_id = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not row_id:
            return

        filepath = self.tree.set(row_id, "File Path")
        ctrl_pressed = (event.state & 0x0004) != 0
        shift_pressed = (event.state & 0x0001) != 0

        if col == "#1":  
            current_val = self.tree.set(row_id, "Select")
            if current_val == "✔":
                self.tree.set(row_id, "Select", "")
                self.tree.item(row_id, tags=())
                self.selected_files.discard(filepath)
                self.tree.selection_remove(row_id)
            else:
                self.tree.set(row_id, "Select", "✔")
                self.tree.item(row_id, tags=("selected",))
                self.selected_files.add(filepath)
                self.tree.selection_add(row_id)
            return "break"  

        elif col == "#2":  
            if ctrl_pressed:
                if row_id in self.tree.selection():
                    self.tree.selection_remove(row_id)
                    self.tree.set(row_id, "Select", "")
                    self.tree.item(row_id, tags=())
                    self.selected_files.discard(filepath)
                else:
                    self.tree.selection_add(row_id)
                    self.tree.set(row_id, "Select", "✔")
                    self.tree.item(row_id, tags=("selected",))
                    self.selected_files.add(filepath)

            elif shift_pressed:
                current_index = self.tree.index(row_id)
                selected = self.tree.selection()
                if selected:
                    anchor_index = self.tree.index(selected[0])
                    low = min(anchor_index, current_index)
                    high = max(anchor_index, current_index)
                    range_ids = self.tree.get_children()[low:high+1]
                    self.tree.selection_set(range_ids)
                    for item in self.tree.get_children():
                        if item in range_ids:
                            self.tree.set(item, "Select", "✔")
                            self.tree.item(item, tags=("selected",))
                            self.selected_files.add(self.tree.set(item, "File Path"))
                        else:
                            self.tree.set(item, "Select", "")
                            self.tree.item(item, tags=())
                            self.selected_files.discard(self.tree.set(item, "File Path"))
                else:
                    self.tree.selection_set(row_id)
                    self.tree.set(row_id, "Select", "✔")
                    self.tree.item(row_id, tags=("selected",))
                    self.selected_files = {filepath}

            else:
                self.tree.selection_set(row_id)
                for item in self.tree.get_children():
                    if item == row_id:
                        self.tree.set(item, "Select", "✔")
                        self.tree.item(item, tags=("selected",))
                        self.selected_files = {filepath}
                    else:
                        self.tree.set(item, "Select", "")
                        self.tree.item(item, tags=())
                        self.selected_files.discard(self.tree.set(item, "File Path"))

            return "break"  

    def handle_drag_motion(self, event):
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return

        if self.drag_select_start is None:
            self.drag_select_start = row_id
            start_val = self.tree.set(row_id, "Select")
            self.drag_deselect_mode = (start_val == "✔")

        start_index = self.tree.index(self.drag_select_start)
        current_index = self.tree.index(row_id)
        low = min(start_index, current_index)
        high = max(start_index, current_index)

        range_ids = self.tree.get_children()[low:high+1]

        for item in self.tree.get_children():
            if item in range_ids:
                self.tree.set(item, "Select", "✔")
                self.tree.item(item, tags=("selected",))
                self.selected_files.add(self.tree.set(item, "File Path"))
            else:
                if not self.drag_deselect_mode:
                    continue
                self.tree.set(item, "Select", "")
                self.tree.item(item, tags=())
                self.selected_files.discard(self.tree.set(item, "File Path"))

        self.tree.selection_set(range_ids)

    def handle_drag_release(self, event):
        self.drag_select_start = None

    # -- Double click open file --

    def handle_double_click(self, event):
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
        filepath = self.tree.set(row_id, "File Path")
        self.open_files([filepath])

    # -- Context Menu Logic --

    def show_context_menu(self, event):
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return

        current_selection = self.tree.selection()
        if row_id not in current_selection:
            self.tree.selection_set(row_id)

        selected_items = self.tree.selection()
        filepaths = [self.tree.set(item, "File Path") for item in selected_items]

        checked_files = set()
        for item in self.tree.get_children():
            if self.tree.set(item, "Select") == "✔":
                checked_files.add(self.tree.set(item, "File Path"))

        if checked_files:
            self.selected_files = checked_files
        else:
            self.selected_files = set(filepaths)

        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Open File(s)", command=lambda: self.open_files(list(self.selected_files)))
        menu.add_command(label="Open Folder", command=lambda: self.open_folder(next(iter(self.selected_files))))
        menu.add_separator()
        menu.add_command(label="Delete File(s)", command=self.delete_selected_files)
        menu.add_separator()
        menu.add_command(label="Move File(s)", command=self.move_selected_files)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def delete_files_from_context(self, filepaths):
        self.selected_files = set(filepaths)
        self.delete_selected_files()

    def open_files(self, filepaths):
        for filepath in filepaths:
            if os.path.exists(filepath):
                try:
                    if sys.platform == "win32":
                        os.startfile(filepath)
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", filepath])
                    else:
                        subprocess.Popen(["xdg-open", filepath])
                except Exception as e:
                    messagebox.showwarning("Open Failed", f"Failed to open file:\n{filepath}\n{e}")
            else:
                messagebox.showwarning("File Not Found", f"File does not exist:\n{filepath}")

    def open_folder(self, filepath):
        folder = os.path.dirname(filepath)
        if os.path.exists(folder):
            try:
                if sys.platform == "win32":
                    os.startfile(folder)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", folder])
                else:
                    subprocess.Popen(["xdg-open", folder])
            except Exception as e:
                messagebox.showwarning("Open Folder Failed", f"Failed to open folder:\n{folder}\n{e}")
        else:
            messagebox.showwarning("Folder Not Found", f"Folder does not exist:\n{folder}")

    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        self.selected_files = set(self.tree.set(item, "File Path") for item in selected_items)
        for item in self.tree.get_children():
            self.tree.item(item, tags=())
        for item in selected_items:
            self.tree.item(item, tags=("selected",))

    # -- Selected files open folder and preview --

    def open_selected_file_folder(self):
        if not self.selected_files:
            messagebox.showinfo("No Selection", "No files selected to open folder.")
            return
        filepath = next(iter(self.selected_files))
        if not os.path.exists(filepath):
            messagebox.showwarning("File Not Found", f"File does not exist:\n{filepath}")
            return
        folder = os.path.dirname(filepath)
        try:
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showwarning("Open Folder Failed", f"Failed to open folder:\n{folder}\n{e}")

    def preview_selected_files(self, event=None):
        if not self.selected_files:
            messagebox.showinfo("No Selection", "No files selected to preview.")
            return
        for filepath in self.selected_files:
            if os.path.exists(filepath):
                try:
                    if sys.platform == "win32":
                        os.startfile(filepath)
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", filepath])
                    else:
                        subprocess.Popen(["xdg-open", filepath])
                except Exception as e:
                    messagebox.showwarning("Open Failed", f"Failed to open file:\n{filepath}\n{e}")

    # -- Delete single file --
	
    def normalize_path(self, path):
        try:
            if path.startswith('\\\\?\\'):
                path = path[4:]
            return os.path.normpath(path)
        except Exception:
            return path

    def delete_file(self, filepath):
        try:
            safe_path = self.normalize_path(filepath)
            if not os.path.exists(safe_path):
                messagebox.showwarning("File Not Found", f"File does not exist:\n{filepath}")
                return
            if self.delete_to_recycle.get() and SEND2TRASH_AVAILABLE:
                try:
                    send2trash.send2trash(safe_path)
                except Exception as e:
                    messagebox.showerror("Delete Failed", f"Failed to delete file:\n{filepath}\n{e}")
                    return
            else:
                try:
                    os.remove(safe_path)
                except Exception as e:
                    messagebox.showerror("Delete Failed", f"Failed to delete file:\n{filepath}\n{e}")
                    return

            if filepath in self.tree_items:
                row_id = self.tree_items.pop(filepath)
                self.tree.delete(row_id)
            if filepath in self.selected_files:
                self.selected_files.discard(filepath)

            self.status_label.config(text=f"Deleted file:\n{filepath}")

        except Exception as ex:
            messagebox.showerror("Delete Failed", f"Unexpected error deleting file:\n{filepath}\n{ex}")


    # -- Delete selected files with recycle bin support --

    def delete_selected_files(self):
        if not self.selected_files:
            messagebox.showinfo("No Selection", "No files selected to delete.")
            return
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {len(self.selected_files)} selected file(s)?")
        if not confirm:
            return
        failed = []
        deleted = []
        for filepath in list(self.selected_files):
            safe_path = self.normalize_path(filepath)
            if not os.path.exists(safe_path):
                self.selected_files.discard(filepath)
                continue
            try:
                backup_filename = f"{uuid.uuid4()}_{os.path.basename(safe_path)}"
                backup_path = os.path.join(self.undo_backup_folder, backup_filename)
                os.makedirs(self.undo_backup_folder, exist_ok=True)
                shutil.copy2(safe_path, backup_path)

                # Delete logic
                if self.delete_to_recycle.get() and SEND2TRASH_AVAILABLE:
                    try:
                        send2trash.send2trash(safe_path)
                    except Exception as e:
                        failed.append(filepath)
                        print(f"Failed to send to trash: {filepath}\n{e}")
                        continue
                else:
                    try:
                        os.remove(safe_path)
                    except Exception as e:
                        failed.append(filepath)
                        print(f"Failed to remove file: {filepath}\n{e}")
                        continue

                deleted.append(filepath)
                self.delete_history.append({
                    "original": safe_path,
                    "backup": backup_path,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                if len(self.delete_history) > self.DELETE_HISTORY_MAX:
                    self.delete_history.pop(0)

                self.selected_files.discard(filepath)
                row_id = self.tree_items.get(filepath)
                if row_id:
                    self.tree.delete(row_id)
                    self.tree_items.pop(filepath, None)
            except Exception as e:
                failed.append(filepath)
                print(f"Failed to delete file: {filepath}\n{e}")

        if deleted:
            self.save_delete_history()

        if failed:
            messagebox.showwarning("Delete Failed", f"Failed to delete {len(failed)} file(s). Check console for details.")
        else:
            messagebox.showinfo("Delete Success", f"Deleted {len(deleted)} file(s).")

        self.status_label.config(text=f"Deleted {len(deleted)} files.")

    def undo_delete(self):
        if not self.delete_history:
            messagebox.showinfo("Undo Delete", "No delete history to undo.")
            return

        last_deleted = self.delete_history.pop()
        original_path = last_deleted["original"]
        backup_path = last_deleted["backup"]

        if not os.path.exists(backup_path):
            messagebox.showwarning("Undo Failed", "Backup for the deleted file was not found.")
            return

        try:
            os.makedirs(os.path.dirname(original_path), exist_ok=True)
            shutil.move(backup_path, original_path)

            # START - Rehash and update duplicates list
            file_hash = self.get_file_hash(original_path)
            if file_hash:
                normalized_path = os.path.normcase(os.path.normpath(original_path))
                if file_hash in self.duplicates:
                    self.duplicates[file_hash] = [
                        p for p in self.duplicates[file_hash]
                        if os.path.normcase(os.path.normpath(p)) != normalized_path
                    ]
                    self.duplicates[file_hash].append(normalized_path)
                else:
                    self.duplicates[file_hash] = [normalized_path]
                self.populate_tree(self.duplicates)
            # END

            messagebox.showinfo("Undo Delete", f"Restored file:\n{original_path}")
            self.status_label.config(text="File restored and re-checked for duplicates.")

        except Exception as e:
            messagebox.showerror("Undo Failed", f"Failed to restore file:\n{str(e)}")

    def get_file_hash(self, filepath, block_size=65536):
        try:
            hasher = hashlib.md5()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(block_size), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            print(f"Hashing failed for {filepath}: {e}")
            return None

    # -- Move Duplicates Logic --

    def move_selected_files(self):
        if not self.selected_files:
            messagebox.showinfo("No Selection", "No files selected to move.")
            return

        target_folder = filedialog.askdirectory(title="Select Folder to Move Files To")
        if not target_folder:
            return

        moved = []
        failed = []

        for filepath in list(self.selected_files):
            if not os.path.exists(filepath):
                self.selected_files.discard(filepath)
                continue

            try:
                filename = os.path.basename(filepath)
                target_path = os.path.join(target_folder, filename)

                if os.path.exists(target_path):
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(target_path):
                        filename = f"{base}_{counter}{ext}"
                        target_path = os.path.join(target_folder, filename)
                        counter += 1

                shutil.move(filepath, target_path)

                self.move_history.append({
                    "original": filepath,
                    "moved_to": target_path,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                if len(self.move_history) > self.DELETE_HISTORY_MAX:
                    self.move_history.pop(0)

                moved.append(filepath)
                self.selected_files.discard(filepath)

                row_id = self.tree_items.get(filepath)
                if row_id:
                    self.tree.delete(row_id)
                    self.tree_items.pop(filepath, None)

            except Exception as e:
                failed.append(filepath)
                print(f"Failed to move file: {filepath}\n{e}")

        if moved:
            messagebox.showinfo("Move Success", f"Moved {len(moved)} file(s).")
            self.status_label.config(text=f"Moved {len(moved)} file(s).")

        if failed:
            messagebox.showwarning("Move Failed", f"Failed to move {len(failed)} file(s). Check console for details.")

    def undo_move(self):
        if not self.move_history:
            messagebox.showinfo("Undo Move", "No move history to undo.")
            return

        last_move = self.move_history.pop()
        original_path = last_move["original"]
        moved_path = last_move["moved_to"]

        if not os.path.exists(moved_path):
            messagebox.showwarning("Undo Failed", "Moved file no longer exists.")
            return

        try:
            os.makedirs(os.path.dirname(original_path), exist_ok=True)
            shutil.move(moved_path, original_path)

            file_hash = self.get_file_hash(original_path)
            if file_hash:
                normalized_path = os.path.normcase(os.path.normpath(original_path))
                if file_hash in self.duplicates:
                    self.duplicates[file_hash] = [
                        p for p in self.duplicates[file_hash]
                        if os.path.normcase(os.path.normpath(p)) != normalized_path
                    ]
                    self.duplicates[file_hash].append(normalized_path)
                else:
                    self.duplicates[file_hash] = [normalized_path]

                self.populate_tree(self.duplicates)

            messagebox.showinfo("Undo Move", f"Restored file:\n{original_path}")
            self.status_label.config(text="File restored and re-checked for duplicates.")

        except Exception as e:
            messagebox.showerror("Undo Move Failed", f"Failed to restore file:\n{str(e)}")

    # -- Undo and Delete History Logic -- 
	
    def show_undo_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Undo Move/Delete History")
        dialog.geometry("800x400")
        dialog.resizable(True, True)
        dialog.grab_set()

        dialog.drag_start_row = None
        dialog.dragging = False
        dialog.selected_rows = set()

        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tree = ttk.Treeview(tree_frame,
            columns=("Type", "Original", "Backup/Moved To", "Timestamp"),
            show="headings", selectmode="extended", yscrollcommand=tree_scrollbar.set
        )
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tree_scrollbar.config(command=tree.yview)

        tree.heading("Type", text="Type")
        tree.heading("Original", text="Original Path")
        tree.heading("Backup/Moved To", text="Backup/Moved Path")
        tree.heading("Timestamp", text="Timestamp")

        tree.column("Type", width=100, anchor=tk.CENTER)
        tree.column("Original", width=250)
        tree.column("Backup/Moved To", width=250)
        tree.column("Timestamp", width=150)

        tree.bind("<Button-1>", lambda e: self.undo_tree_click(e, tree, dialog))
        tree.bind("<B1-Motion>", lambda e: self.undo_tree_drag(e, tree, dialog))
        tree.bind("<ButtonRelease-1>", lambda e: self.undo_tree_release(e, tree, dialog))

        # Load data
        for item in self.delete_history:
            tree.insert("", "end", values=("Delete", item["original"], item["backup"], item["timestamp"]))

        for item in self.move_history:
            tree.insert("", "end", values=("Move", item["original"], item["moved_to"], item["timestamp"]))

        def restore_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showinfo("Restore", "No items selected to restore.")
                return

            restored = 0
            to_delete_ids = []

            for row_id in selected:
                vals = tree.item(row_id)["values"]
                type_, original, backup_or_moved, timestamp = vals

                try:
                    if os.path.exists(backup_or_moved):
                        os.makedirs(os.path.dirname(original), exist_ok=True)
                        shutil.move(backup_or_moved, original)
                        restored += 1
                        to_delete_ids.append(row_id)

                        # Remove from delete_history or move_history
                        if type_ == "Delete":
                            self.delete_history = [
                                h for h in self.delete_history if not (
                                    h["original"] == original and h["backup"] == backup_or_moved
                                )
                            ]
                        elif type_ == "Move":
                            self.move_history = [
                                h for h in self.move_history if not (
                                    h["original"] == original and h["moved_to"] == backup_or_moved
                                )
                            ]
                except Exception as e:
                    print(f"Failed to restore: {original}\n{e}")
                    continue

            for row_id in to_delete_ids:
                tree.delete(row_id)

            self.save_delete_history()

            if restored:
                messagebox.showinfo("Restore Complete", f"Restored {restored} item(s).")
                self.populate_tree(self.duplicates)

        # Bottom Frame
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        select_all_var = tk.BooleanVar()

        def toggle_select_all():
            if select_all_var.get():
                tree.selection_set(tree.get_children())
                for item in tree.get_children():
                    tree.item(item, tags=("selected",))
            else:
                tree.selection_remove(tree.get_children())
                for item in tree.get_children():
                    tree.item(item, tags=())

        ttk.Checkbutton(btn_frame, text="Select All", variable=select_all_var, command=toggle_select_all).pack(side=tk.LEFT)

        restore_btn = ttk.Button(btn_frame, text="Restore Selected", command=restore_selected)
        restore_btn.pack(side=tk.RIGHT, padx=5)

        close_btn = ttk.Button(btn_frame, text="Close", command=dialog.destroy)
        close_btn.pack(side=tk.RIGHT)

    def undo_tree_click(self, event, tree, dialog):
        row = tree.identify_row(event.y)
        if not row:
            return
        dialog.drag_start_row = row
        dialog.dragging = True
        dialog.selected_rows = {row}
        tree.tag_configure("selected", background="#cce6ff")
        tree.selection_set(row)
        tree.item(row, tags=("selected",))

    def undo_tree_drag(self, event, tree, dialog):
        if not dialog.dragging or not dialog.drag_start_row:
            return
        start_idx = tree.index(dialog.drag_start_row)
        current_row = tree.identify_row(event.y)
        if not current_row:
            return
        end_idx = tree.index(current_row)

        low, high = sorted([start_idx, end_idx])
        children = tree.get_children()
        selected_range = children[low:high + 1]

        dialog.selected_rows = set(selected_range)
        tree.selection_set(selected_range)
        for item in children:
            tree.item(item, tags=("selected",) if item in dialog.selected_rows else ())

    def undo_tree_release(self, event, tree, dialog):
        dialog.dragging = False
        dialog.drag_start_row = None

    # -- Export and Import CSV / JSON --

    def export_scan_csv(self):
        if not self.duplicates:
            messagebox.showinfo("No Data", "No scan results to export.")
            return
        path = filedialog.asksaveasfilename(title="Export Scan as CSV", defaultextension=".csv",
                                            filetypes=[("CSV files", "*.csv")],
                                            initialdir=self.last_export_folder)
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Group", "File Path", "Size"])
                group_id = 1
                for files in self.duplicates.values():
                    for filepath in files:
                        try:
                            size_bytes = os.path.getsize(filepath) if os.path.exists(filepath) else 0
                        except Exception:
                            size_bytes = 0
                        size_str = self.format_size(size_bytes)
                        writer.writerow([group_id, filepath, size_str])
                    group_id += 1
            self.last_export_folder = os.path.dirname(path)
            messagebox.showinfo("Export Complete", f"Scan results exported to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export CSV:\n{e}")

    def export_scan_json(self):
        if not self.duplicates:
            messagebox.showinfo("No Data", "No scan results to export.")
            return
        path = filedialog.asksaveasfilename(title="Export Scan as JSON", defaultextension=".json",
                                            filetypes=[("JSON files", "*.json")],
                                            initialdir=self.last_export_folder)
        if not path:
            return
        try:
            export_data = {}
            group_id = 1
            for files in self.duplicates.values():
                export_data[str(group_id)] = files
                group_id += 1
            with open(path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)
            self.last_export_folder = os.path.dirname(path)
            messagebox.showinfo("Export Complete", f"Scan results exported to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export JSON:\n{e}")

    def import_scan_csv(self):
        path = filedialog.askopenfilename(title="Import Scan CSV",
                                          filetypes=[("CSV files", "*.csv"), ("All Files", "*.*")],
                                          initialdir=self.last_import_folder)
        if not path:
            return
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                duplicates = {}
                for row in reader:
                    group = row.get("Group")
                    filepath = row.get("File Path")
                    duplicates.setdefault(group, []).append(filepath)
            self.duplicates = {str(i): files for i, files in enumerate(duplicates.values(), 1)}
            self.populate_tree(self.duplicates)
            self.last_import_folder = os.path.dirname(path)
            messagebox.showinfo("Import Complete", "Scan results imported successfully.")
        except Exception as e:
            messagebox.showerror("Import Failed", f"Failed to import CSV:\n{e}")

    def import_scan_json(self):
        path = filedialog.askopenfilename(title="Import Scan JSON",
                                          filetypes=[("JSON files", "*.json"), ("All Files", "*.*")],
                                          initialdir=self.last_import_folder)
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                duplicates = json.load(f)
            self.duplicates = duplicates
            self.populate_tree(self.duplicates)
            self.last_import_folder = os.path.dirname(path)
            messagebox.showinfo("Import Complete", "Scan results imported successfully.")
        except Exception as e:
            messagebox.showerror("Import Failed", f"Failed to import JSON:\n{e}")

    # -- Save/load settings --

    def save_settings(self):
        data = {
            "last_scan_folder": self.last_scan_folder,
            "last_import_folder": self.last_import_folder,
            "last_export_folder": self.last_export_folder,
            "last_music_folder": self.last_music_folder,
            "delete_to_recycle": self.delete_to_recycle.get(),
            "hash_size": self.hash_size.get(),
            "auto_cleanup_enabled": self.auto_cleanup_enabled.get(),
            "auto_cleanup_days": self.auto_cleanup_days.get(),
            "undo_backup_folder": self.undo_backup_folder,
            "theme": self.theme_var.get(),
            "repeat_current": self.repeat_current.get(),
            "shuffle_enabled": self.shuffle_enabled.get(),
            "volume_level": self.volume_level.get(),
            "delete_auto_clean_days": self.delete_auto_clean_days,
        }
        try:
            with open(self.SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"Settings saved: {data}")
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_settings(self):
        if not os.path.exists(self.SETTINGS_FILE):
            return {}

        try:
            with open(self.SETTINGS_FILE, encoding="utf-8") as f:
                data = json.load(f)

            self.last_scan_folder = data.get("last_scan_folder", self.last_scan_folder)
            self.last_import_folder = data.get("last_import_folder", self.last_import_folder)
            self.last_export_folder = data.get("last_export_folder", self.last_export_folder)
            self.last_music_folder = data.get("last_music_folder", self.last_music_folder)
            self.delete_to_recycle.set(data.get("delete_to_recycle", True))
            self.hash_size.set(data.get("hash_size", 8 * 1024 * 1024))
            self.auto_cleanup_enabled.set(data.get("auto_cleanup_enabled", True))
            self.auto_cleanup_days.set(data.get("auto_cleanup_days", 7))

            path = data.get("undo_backup_folder")
            self.undo_backup_folder = os.path.normpath(path) if path else os.path.join(os.getcwd(), "undo_backups")
            print(f"Loaded undo backup folder: {self.undo_backup_folder}")

            theme = data.get("theme")
            if theme and theme in self.available_themes:
                self.theme_var.set(theme)
                if THEMES_AVAILABLE:
                    self.style.set_theme(theme)

            self.repeat_current.set(data.get("repeat_current", False))
            self.shuffle_enabled.set(data.get("shuffle_enabled", False))
            self.volume_level.set(data.get("volume_level", 0.25))
            self.delete_auto_clean_days = data.get("delete_auto_clean_days", self.DELETE_AUTO_CLEAN_DAYS_DEFAULT)

            if PYGAME_AVAILABLE:
                pygame.mixer.music.set_volume(self.volume_level.get())

            return data
        except Exception as e:
            print(f"Error loading settings: {e}")
            return {}

    def select_auto_backup_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.undo_backup_folder = folder
            self.save_settings()

        # -- Delete and Move history persistence --

    def save_delete_history(self):
        path = "delete_history.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.delete_history, f, indent=2)
        except Exception:
            pass

    def load_delete_history_and_cleanup(self):
        path = "delete_history.json"
        if not os.path.exists(path):
            self.delete_history = []
            return
        try:
            with open(path, encoding="utf-8") as f:
                history = json.load(f)
            self.delete_history = history
            self.clean_old_delete_history()
        except Exception:
            self.delete_history = []

    def clean_old_delete_history(self):
        now = datetime.datetime.now()
        cutoff = now - datetime.timedelta(days=self.delete_auto_clean_days)
        new_history = []
        for record in self.delete_history:
            try:
                ts = datetime.datetime.fromisoformat(record.get("timestamp"))
                if ts > cutoff:
                    new_history.append(record)
            except Exception:
                pass
        if len(new_history) != len(self.delete_history):
            self.delete_history = new_history
            self.save_delete_history()
	
    def save_move_history(self):
        try:
            with open("move_history.json", "w", encoding="utf-8") as f:
                json.dump(self.move_history, f, indent=2)
        except Exception as e:
            print(f"Error saving move history: {e}")

    def load_move_history(self):
        try:
            if os.path.exists("move_history.json"):
                with open("move_history.json", "r", encoding="utf-8") as f:
                    self.move_history = json.load(f)
        except Exception as e:
            print(f"Error loading move history: {e}")
            self.move_history = []

    # -- Sorting --

    def sort_by_size(self):
        children = list(self.tree.get_children())
        children_with_size = []
        for c in children:
            size_str = self.tree.set(c, "Size")
            size_bytes = self.size_str_to_bytes(size_str)
            children_with_size.append((c, size_bytes))
        children_with_size.sort(key=lambda x: x[1], reverse=self.size_sort_descending)
        for index, (c, _) in enumerate(children_with_size):
            self.tree.move(c, "", index)
        self.size_sort_descending = not self.size_sort_descending

    def size_str_to_bytes(self, size_str):
        try:
            parts = size_str.split()
            num = float(parts[0])
            unit = parts[1] if len(parts) > 1 else "B"
            unit = unit.upper()
            if unit == "B":
                return num
            elif unit == "KB":
                return num * 1024
            elif unit == "MB":
                return num * 1024 * 1024
            elif unit == "GB":
                return num * 1024 * 1024 * 1024
            else:
                return num
        except Exception:
            return 0

    def sort_by_filepath(self):
        children = list(self.tree.get_children())
        children_with_path = []
        for c in children:
            path = self.tree.set(c, "File Path").lower()
            children_with_path.append((c, path))
        children_with_path.sort(key=lambda x: x[1], reverse=self.filepath_sort_descending)
        for index, (c, _) in enumerate(children_with_path):
            self.tree.move(c, "", index)
        self.filepath_sort_descending = not self.filepath_sort_descending

    def sort_by_group(self):
        children = list(self.tree.get_children())
        children_with_group = []
        for c in children:
            group_str = self.tree.set(c, "Group")
            try:
                group_num = int(group_str)
            except Exception:
                group_num = 0
            children_with_group.append((c, group_num))
        children_with_group.sort(key=lambda x: x[1], reverse=self.group_sort_descending)
        for index, (c, _) in enumerate(children_with_group):
            self.tree.move(c, "", index)
        self.group_sort_descending = not self.group_sort_descending

    def change_theme(self):
        new_theme = self.theme_var.get()
        if THEMES_AVAILABLE:
            try:
                self.style.set_theme(new_theme)
            except Exception as e:
                messagebox.showwarning("Theme Change Failed", f"Failed to apply theme:\n{e}")
        self.save_settings()

    def on_close(self):
        self.is_closing = True
        if hasattr(self, 'scan_stop_event'):
            self.scan_stop_event.set()
        if hasattr(self, 'scanning_thread') and self.scanning_thread and self.scanning_thread.is_alive():
            self.scanning_thread.join(timeout=5)
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except Exception as e:
                print(f"Error stopping pygame: {e}")
        try:
            self.save_settings()
            self.save_delete_history()
        except Exception as e:
            print(f"Error saving data on close: {e}")
        self.root.destroy()


def main():
    root = tk.Tk()
    root.iconbitmap('ownages_duplicate_finder.ico')
    app = DuplicateFinderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
