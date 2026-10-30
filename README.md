# Face Library

A local photo organizer with face detection and **manual** person tags. It does
not identify people, compute identity embeddings, or automatically match faces.

## Run

On Windows, extract the complete project ZIP and double-click
**Start Face Library.bat**. It selects the project folder automatically, creates
the virtual environment, installs dependencies, and opens a native desktop
window. No browser, address bar, or listening HTTP server is needed.
This is a Python desktop app; a standalone Windows executable is not included.

Requires 64-bit Python 3.12 (tested). The Windows launcher uses `.venv312`
and installs prebuilt wheels only. Python 3.15 is incompatible with the pinned
NumPy/Pillow versions; installing a compiler is not necessary. Install Python
3.12 alongside other versions with:

```powershell
winget install -e --id Python.Python.3.12 --architecture x64
```

Download or clone the whole project onto your computer. To run manually, open
a terminal in the project folder and use the commands below. Standard Windows
Python includes Tkinter; Linux may need the OS package `python3-tk`.

```sh
cd /path/to/codex-test
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python desktop.py
```

On Windows PowerShell, from the project folder:

```powershell
py -3.12 -m venv .venv312
.venv312\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
.venv312\Scripts\python.exe desktop.py
```

Click **Import photos**, select JPEG, PNG, or WebP files, and select a photo
from the left list. Review the face thumbnails, type a person tag, and click
**Save tag**. The dropdown filters photos by tag. Clear a tag and save to remove
it. Imports run in the background; wait for completion before closing the app.
Close the desktop window when finished. Existing `data/` libraries are reused
when you launch the desktop app from the same project directory.

The earlier browser interface remains optional: run `app.py` instead of
`desktop.py` and open `http://127.0.0.1:5000` on the same machine. Opening the
HTML template directly does not run the app. Do not expose the web server publicly.

Images and SQLite tags are retained in ignored `data/`, or the directory selected
by `PHOTO_DATA_DIR`. Images are resized to at most 2400 pixels per side and
re-encoded without original EXIF metadata. No photos are sent to an external API.
Keep original images separately. To erase this library, stop the app and remove
its data directory. Do not commit private photos to Git.

The bundled OpenCV detector can miss side profiles, small faces, and obscured
faces, and can produce false positives. No-face images are still imported.
The desktop app imports one image at a time, up to 40 MB and 30 megapixels per
image. No labeled training set is required.

## Verify

```sh
.venv/bin/python -m unittest discover -s tests -v
```
