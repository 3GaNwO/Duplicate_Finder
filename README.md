<h1><b> OwNaG3's Duplicate Files Project</h1></b>

This app was a small project to make an easy duplicate file deleter. 

If you want to run it via Python you will need these:

<b>Requirements:</b>
pygames, ttkthemes, and send2trash. 
<b>To install requirements use:</b>
pip install pygame ttkthemes send2trash
or
python3 -m pip install pygame ttkthemes send2trash
or 
py -m pip install pygame ttkthemes send2trash

Once you have them installed you should be able to just run the .py script.

<h3>Features:</h3>

✅ 🖥️ <h4>General Application Features</h4>
Graphical User Interface (GUI) using tkinter + ttk
Themed UI support using ttkthemes (optional, with fallback if not installed)
Multi-threaded scanning (non-blocking file operations while UI remains responsive)
Resizable and movable windows
Custom menu bar with:
File, Edit, Export, Import, Settings, Tools, Help sections
Custom icons and optional audio cues

🔍 🗂️ <h4>File Duplicate Scanning</h4>
Fast hash-based duplicate finder (MD5 or SHA-256)
Scans folders recursively
Filters and groups duplicate files
Tracks and displays:
Total scanned files
Duplicate count
Duplicate groups
Progress label and multithreaded scan with status updates

📂 <h4>Export/Import Functionality</h4>
Export scan results as:
CSV
JSON
Import previous scans from:
CSV
JSON

📂 <h4>Remove Empty Folders on Scan Checkbox Option</h4>

🧹 <h4>Duplicate Management Tools</h4>
Delete Duplicates option (with confirmation)
Move to Trash (Recycle Bin) using send2trash
Undo Delete History with a recovery option
Selective deletion via checkboxes per file
Ability to Move Duplicate Files to User Specified Location
Ability to Undo Moved/Deleted Files

🎵 <h4>Optional Music Player</h4>
Integrated music playback using pygame.mixer
Play/Pause background music during scan sessions
Mute and Stop buttons
Fallback logic if pygame not installed

⚙️ <h4>Settings & Preferences</h4>
Toggle for themes
Toggle for music/audio
Fast hash algorithm selection (optional)
Delete confirmation settings

🖱️ <h4>Context Menu & File Preview</h4>
Right-click context menu with:
Open file
Open containing folder
Copy file path
Displays file previews (e.g., images, metadata) if supported

📊 <h4>Statistics & Logging</h4>
Displays:
Total number of scanned files
Number of detected duplicate groups
Number of deleted or moved files
Logs or console outputs for debugging and scanning errors

🧪 <h4>Testing/Dev Features</h4>
Multiple history_type systems: export, delete, scan
Hooks for analytics or usage tracking
Placeholder buttons for future tools (e.g., File Cleaner, Log Viewer)

🌐 <h4>Portability and Packaging</h4>
PyInstaller-compatible
.ico icon set via PyInstaller for compiled .exe
Handles missing modules gracefully (try/except import blocks)
Prints debug info to console on errors (e.g., traceback logging)
