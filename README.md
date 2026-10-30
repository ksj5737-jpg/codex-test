# Face Library

A local photo organizer with face detection and **manual** person tags. It does
not identify people, compute identity embeddings, or automatically match faces.

## Run

On Windows, extract the complete project ZIP and double-click
**Start Face Library.bat**. It selects the project folder automatically, creates
the virtual environment, installs dependencies, and opens a native desktop
window. No browser, address bar, or listening HTTP server is needed.
This is a Python desktop app; a standalone Windows executable is not included.
First startup also downloads the 233 KB YuNet model from official OpenCV GitHub
hosting and verifies its SHA-256. SCRFD-2.5G detection weights are bundled.
After dependency/model setup, image processing works offline. If YuNet download
fails, the window selects SCRFD and explains how to retry model installation.

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
.venv/bin/python download_models.py
.venv/bin/python desktop.py
```

On Windows PowerShell, from the project folder:

```powershell
py -3.12 -m venv .venv312
.venv312\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
.venv312\Scripts\python.exe download_models.py
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

Choose **YuNet** or **SCRFD-2.5G** before importing. They run on the CPU; no GPU
is required. YuNet uses OpenCV and SCRFD uses ONNX Runtime. The previous
**Legacy SSD** detector remains available for comparison. The app does not
combine detections from different models. Each imported photo records its model
and mode, shown in the photo list and details.

Large photos also get overlapping tiled passes to help with smaller faces.
The model weights and detection results stay local; photos are not uploaded.

**Licensing:** YuNet's model directory includes its MIT license. InsightFace's
pretrained SCRFD weights are restricted to **non-commercial research purposes
only**, despite the runtime code's separate license. Commercial deployment needs
appropriate rights from the model owner. Only detection weights are included;
recognition, age/gender, and separate alignment models are not used.
See `models/SOURCES.md` for provenance and the upstream restriction.

Before importing, choose **Strict** for fewer false faces, **Balanced** (default),
or **Sensitive** for more detections. Thresholds are tuned separately per model:

| Detector | Strict | Balanced | Sensitive |
| --- | --- | --- | --- |
| YuNet | 0.95 | 0.85 | 0.65 |
| SCRFD-2.5G | 0.80 | 0.60 | 0.35 |
| Legacy SSD | 0.95 | 0.80 | 0.60 |

Scores are model outputs, not calibrated probabilities and not comparable across
models. Sensitive can add false
faces; Strict can miss real ones. **Not a face** removes a wrong thumbnail and
its tag while retaining the photo. This does not train or improve the model.
Changing the detector or mode affects new imports only. Re-import an original
image to compare another model or mode; this creates a separate photo and does
not move existing tags. Existing libraries and tags are retained when the new
version runs against the same `data/` directory. Back up that directory before
upgrading; copy it into the new project folder while both app versions are closed.

For best results, use sharp original images with well-lit, unobscured faces.
Detection can still miss profiles or tiny faces and can produce false positives.
No-face images are still imported. No accuracy percentage is claimed without
evaluating representative photos with manually marked faces.
The desktop app imports one image at a time, up to 40 MB and 30 megapixels per
image. No labeled training set is required.

## Verify

```sh
.venv/bin/python -m unittest discover -s tests -v
```

The real YuNet blank-image check is skipped explicitly if its verified model
is not installed. Run `download_models.py` first to enable it.
