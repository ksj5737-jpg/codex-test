# Face Library

A local photo organizer with face detection and **manual** person tags. It does
not identify people, compute identity embeddings, or automatically match faces.

## Run

On Windows, extract the complete project ZIP and double-click
**Start Face Library.bat**. It selects the project folder automatically, creates
the virtual environment, installs dependencies, and starts the server. Then
open `http://127.0.0.1:5000` in your browser. Keep the terminal open.

Requires 64-bit Python 3.12 (tested). The Windows launcher uses `.venv312`
and installs prebuilt wheels only. Python 3.15 is incompatible with the pinned
NumPy/Pillow versions; installing a compiler is not necessary. Install Python
3.12 alongside other versions with:

```powershell
winget install -e --id Python.Python.3.12 --architecture x64
```

**The HTML file preview is not the running app.** Importing needs the Python
server. Download or clone the whole project onto your computer, open a terminal
in that project folder, and use the commands below. Opening `templates/index.html`
directly cannot run face detection.

```sh
cd /path/to/codex-test
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

On Windows PowerShell, from the project folder:

```powershell
py -3.12 -m venv .venv312
.venv312\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
.venv312\Scripts\python.exe app.py
```

Keep that terminal running. In your browser on the same computer, enter
`http://127.0.0.1:5000`. The page should say **Connected · ready to import**.
If it shows connection instructions, you are viewing the wrong page or the
server is stopped. A server running in the cloud is separate from your own
computer's loopback address.

Open `http://127.0.0.1:5000` in a browser on the same machine. The server binds
only to loopback; do not expose it publicly. A remote cloud machine requires
your own supported secure port-forwarding mechanism to use its browser UI.

Select a small batch of JPEG, PNG, or WebP files and click **Import photos**.
Review each detected face, enter a person tag, and click **Save tag**. Use the
dropdown to filter photos by a tag. Click a photo to view its full stored image.
Clear a face's tag and save to remove that assignment.

Images and SQLite tags are retained in ignored `data/`, or the directory selected
by `PHOTO_DATA_DIR`. Images are resized to at most 2400 pixels per side and
re-encoded without original EXIF metadata. No photos are sent to an external API.
Keep original images separately. To erase this library, stop the app and remove
its data directory. Do not commit private photos to Git.

The bundled OpenCV detector can miss side profiles, small faces, and obscured
faces, and can produce false positives. No-face images are still imported.
Imports are synchronous; use small batches under 40 MB total and images under
30 megapixels. No labeled training set is required.

## Verify

```sh
.venv/bin/python -m unittest discover -s tests -v
```
