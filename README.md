
# OwNaG3's Duplicate File Cleaner

A powerful, fast, and customizable Python GUI tool to find and remove duplicate files from your system.  
Built with `tkinter`, `ttkthemes`, and `send2trash`.  
✅ Tested on Windows — standalone EXE included.

---

## 📥 How to Get Started

### 🔧 Requirements

Install dependencies using one of the following:
```bash
pip install pygame ttkthemes send2trash
# or
python3 -m pip install pygame ttkthemes send2trash
# or
py -m pip install pygame ttkthemes send2trash
```

Once installed, you can run the `.py` script directly, or use the bundled `.exe`.  
The `.ico` file is used for the program icon when running via Python.

---

## 🌟 Key Features

### 🖥️ GUI Interface
- ✅ Custom interface built using `tkinter`for responsive, native-feeling GUI
- 🎨 Optional theming via `ttkthemes`
- 🧵 Multi-threaded scanning for responsiveness
- 🪟 Resizable, draggable windows
- 🧭 Menu bar includes File, Edit, Export, Import, Settings, Tools, and About

### 🔍 Duplicate File Scanning
- 🔄 Recursively scans folders
- 📏 Detects duplicates using:
  - 📐 File size grouping
  - 📐 Partial or full MD5 hashing
- 🧾 Adjustable hash read size (512KB to full file)
- 🧠 Auto Scanning options
- 🗂️ Displays results in a sortable table view

### 📁 File & Folder Management
- 🗃️ Folder selection with dialog
- 👁️ File previews using system apps
- 📁 One-click open containing folder

### 📁 Treeview Interface
- 📋 Multi-column layout:
  - ✅ Checkbox
  - 📁 File path
  - 📐 Size
  - 🔢 Group number
- 🔍 Drag-select, Ctrl+Click, and Shift+Click
- 🔀 Sort by path, size, or group
- 🖱️ Right-click context menu

### 🗑️ File Deletion
- ⚠️ Confirm before deletion
- 🗃️ Delete permanently or send to Recycle Bin
- ♻️ Auto-clean empty folders (optional)
- 🛡️ Backups before deletion
- 🗑️ Undo history for all deletes

### 📦 File Moving
- 📤 Move selected files to custom folder
- 🧠 Auto-renames on name conflicts
- 🕘 Move history supports full undo

### 🔁 Undo System
- 🪄 Unified history for deletes and moves
- ✅ Resizable undo dialog
- 🔄 Restore multiple items at once
- 🔄 Remove entries after restore
- ✅ Select all checkbox
- 🖱️ Drag-select with live highlighting

### 🖱️ Context Menu & Preview
- 🖼️ Right-click actions include:
  - 📁 Open file
  - 📁 Open folder
  - 📁 Copy file path
- 🧠 Show file previews (images, metadata, etc.)

### 🎵 Music Player (Bonus Feature)
- 🎶 Loads and plays music from folder (.mp3, .wav, .ogg)
- ▶️ Play/Pause/Stop/Next controls
- 🔀 Shuffle and 🔁 repeat modes
- 🔊 Volume slider
- 🎧 Display current song

### ⚙️ Settings & Preferences
- 💾 Saved in `settings.json`
- 🔧 Configurable options:
  - 🧾 Hash read size
  - 🗑️ Use Recycle Bin (on/off)
  - 🗑️ Auto-clean folders (on/off)
  - 🧾 Undo retention days
  - 🧾 Undo backup location
  - 🎨 Theme selection
  - 🎵 Music volume & playback settings

### 📤 Export / Import
- 📄 Export scan results as:
  - CSV
  - JSON
- 📁 Import past scans from:
  - CSV
  - JSON

### 💾 Persistent Data
- ✅ Settings persist between sessions
- 🕘 Delete history stored in delete_history.json
- 📦 Move history stored in move_history.json

### 🛡️ Stability & Error Handling
- 🚫 Graceful handling of filesystem errors (e.g., permission denied, missing files)
- 🧾 Logs permission errors and missing files
- 🔐 Avoids re-adding restored files as duplicates

---

## 🔎 Related Keywords

Python duplicate file finder, tkinter GUI, send2trash Python, file deduplication, Python file cleaner, file hashing, Windows duplicate remover, OwNaG3, pygame, ttkthemes

---

## 📣 Feedback & Contributions

Have a bug report or feature idea?
➡️ Open an Issue or submit a Pull Request.
https://github.com/3GaNwO/OwNaG3s-Duplicate-Finder/issues

---

## 📜 License

This project is open-source and freely available for modification and use. See the `LICENSE` file.
