<h1><b><p align="center"> OwNaG3's Duplicate Files Project</p></h1></b>

<p align="center">This app was a small project to make an easy duplicate file deleter.<br> 
Only tested on Windows so far. The exe is for ease of use<br>
The .ico file is for the image on the program to load if running via Python<br>
If you want to run it via Python you will need these:</p>

<ul><h4>Requirements:</h4>
<li>pygames, ttkthemes, and send2trash. </li></ul>
<ul><h4>To install requirements use:</h4>
<li>pip install pygame ttkthemes send2trash<br></li>
<li>python3 -m pip install pygame ttkthemes send2trash<br></li>
<li>py -m pip install pygame ttkthemes send2trash<br></li></ul>

Once you have them installed you should be able to just run the .py script.<br>

<h3><p align="center">Features:</p></h3>

<ul><h4>✅ 🖥️ General Application Features</h4>
<li>Graphical User Interface (GUI) using tkinter + ttk</li>
<li>Themed UI support using ttkthemes (optional, with fallback if not installed)</li>
<li>Multi-threaded scanning (non-blocking file operations while UI remains responsive)</li>
<li>Resizable and movable windows</li>
<h4>Custom menu bar with:</h4>
<li>File, Edit, Export, Import, Settings, Tools, Help sections</li>
<li>Custom icons and optional audio cues</li></ul>

<ul><h4>🔍 🗂️ File Duplicate Scanning</h4>
<li>Fast hash-based duplicate finder (MD5 or SHA-256)</li>
<li>Scans folders recursively</li>
<li>Filters and groups duplicate files</li>
<h4>Tracks and displays:</h4>
<li>Total scanned files</li>
<li>Duplicate count</li>
<li>Duplicate groups</li>
<li>Progress label and multithreaded scan with status updates</li></ul>

<ul><h4>📂Export/Import Functionality</h4>
<h4>Export scan results as:</h4>
<li>CSV</li>
<li>JSON</li>
<h4>Import previous scans from:</h4>
<li>CSV</li>
<li>JSON</li></ul>

<ul><h4>📂Remove Empty Folders on Scan Checkbox Option</h4></ul>

<ul><h4>🧹Duplicate Management Tools</h4>
<li>Delete Duplicates option (with confirmation)</li>
<li>Move to Trash (Recycle Bin) using send2trash</li>
<li>Undo Delete History with a recovery option</li>
<li>Selective deletion via checkboxes per file</li>
<li>Ability to Move Duplicate Files to User Specified Location</li>
<li>Ability to Undo Moved/Deleted Files</li></ul>

<ul><h4>🎵Optional Music Player</h4>
<li>Integrated music playback using pygame.mixer</li>
<li>Play/Pause background music during scan sessions</li>
<li>Mute and Stop buttons</li>
<li>Fallback logic if pygame not installed</li></ul>

<ul><h4>⚙️Settings & Preferences</h4>
<li>Toggle for themes</li>
<li>Toggle for music/audio</li>
<li>Fast hash algorithm selection (optional)</li>
<li>Delete confirmation settings</li></ul>

<ul><h4>🖱️Context Menu & File Preview</h4>
<li>Right-click context menu with:</li>
<li>Open file</li>
<li>Open containing folder</li>
<li>Copy file path</li>
<li>Displays file previews (e.g., images, metadata) if supported</li></ul>

<ul><h4>📊Statistics & Logging</h4>
<h4>Displays:</h4>
<li>Total number of scanned files</li>
<li>Number of detected duplicate groups</li>
<li>Number of deleted or moved files</li>
<li>Logs or console outputs for debugging and scanning errors</li></ul>

<ul><h4>🧪Testing/Dev Features</h4>
<li>Multiple history_type systems: export, delete, scan</li>
<li>Hooks for analytics or usage tracking</li>
<li>Placeholder buttons for future tools (e.g., File Cleaner, Log Viewer)</li></ul>

<ul><h4>🌐Portability and Packaging</h4>
<li>PyInstaller-compatible</li>
<li>.ico icon set via PyInstaller for compiled .exe</li>
<li>Handles missing modules gracefully (try/except import blocks)</li>
<li>Prints debug info to console on errors (e.g., traceback logging)</li></ul>
