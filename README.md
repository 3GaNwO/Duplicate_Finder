OwNaG3's Duplicate Files Project

This app was a small project to make an easy duplicate file deleter. 

If you want to run it via Python you will need these Requirements:

pygames, ttkthemes, and send2trash. 

To install use:

pip install pygame ttkthemes send2trash

or
 
python3 -m pip install pygame ttkthemes send2trash

or
 
py -m pip install pygame ttkthemes send2trash

Once you have them installed you should be able to just run the .py script.

Some Features:

✅ 🖥️ General Application Features
Graphical User Interface (GUI) using tkinter + ttk
Themed UI support using ttkthemes (optional, with fallback if not installed)
Multi-threaded scanning (non-blocking file operations while UI remains responsive)
Resizable and movable windows
Custom menu bar with:
File, Edit, Export, Import, Settings, Tools, Help sections
Custom icons and optional audio cues

🔍 🗂️ File Duplicate Scanning
Fast hash-based duplicate finder (MD5 or SHA-256)
Scans folders recursively
Filters and groups duplicate files
Tracks and displays:
Total scanned files
Duplicate count
Duplicate groups
Progress label and multithreaded scan with status updates

📂 Export/Import Functionality
Export scan results as:
CSV
JSON
Import previous scans from:
CSV
JSON

📂 Remove Empty Folders on Scan Checkbox Option

🧹 Duplicate Management Tools
Delete Duplicates option (with confirmation)
Move to Trash (Recycle Bin) using send2trash
Undo Delete History with a recovery option
Selective deletion via checkboxes per file
Ability to Move Duplicate Files to User Specified Location

🎵 Optional Music Player
Integrated music playback using pygame.mixer
Play/Pause background music during scan sessions
Mute and Stop buttons
Fallback logic if pygame not installed

⚙️ Settings & Preferences
Toggle for themes
Toggle for music/audio
Fast hash algorithm selection (optional)
Delete confirmation settings

🖱️ Context Menu & File Preview
Right-click context menu with:
Open file
Open containing folder
Copy file path
Displays file previews (e.g., images, metadata) if supported

📊 Statistics & Logging
Displays:
Total number of scanned files
Number of detected duplicate groups
Number of deleted or moved files
Logs or console outputs for debugging and scanning errors

🧪 Testing/Dev Features (In Progress or Stubbed)
Multiple history_type systems: export, delete, scan
Hooks for analytics or usage tracking
Placeholder buttons for future tools (e.g., File Cleaner, Log Viewer)

🌐 Portability and Packaging
PyInstaller-compatible
.ico icon set via PyInstaller for compiled .exe
Handles missing modules gracefully (try/except import blocks)
Prints debug info to console on errors (e.g., traceback logging)

Features I want to implement: 

Add Support for History on dialog box for Undo Delete and Undo Move. Currently only does 1 at a time. 
Would like to make it so when you click these options they bring up a dialog box with the files you moved
or deleted and allow the user to choose which ones to restore. 
