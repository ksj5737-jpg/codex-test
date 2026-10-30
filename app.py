"""Local face detection and manual photo tagging. No identity matching."""
import os
import sqlite3
import uuid
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, send_file
from PIL import Image, ImageOps, UnidentifiedImageError
from face_detector import FaceDetector, MODES, DETECTORS

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 40 * 1024 * 1024
DATA = Path(os.environ.get('PHOTO_DATA_DIR', Path(__file__).parent / 'data'))
DATA.mkdir(parents=True, exist_ok=True)
detector = FaceDetector()


def db():
    conn = sqlite3.connect(DATA / 'photos.sqlite3')
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


with db() as conn:
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS photos(id TEXT PRIMARY KEY, name TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS faces(id TEXT PRIMARY KEY, photo_id TEXT NOT NULL
        REFERENCES photos(id), tag TEXT NOT NULL DEFAULT '');
    ''')
    columns = {row['name'] for row in conn.execute('PRAGMA table_info(photos)')}
    for column, default in [('detector', 'Legacy SSD'), ('detection_mode', 'Balanced')]:
        if column not in columns:
            conn.execute(f"ALTER TABLE photos ADD COLUMN {column} TEXT NOT NULL DEFAULT '{default}'")


@app.before_request
def local_requests_only():
    # Block cross-site writes and unexpected Host headers on this local service.
    if request.host.split(':')[0] not in ('localhost', '127.0.0.1'):
        abort(403)
    if request.method != 'GET' and request.headers.get('Origin'):
        if request.headers['Origin'] != request.host_url.rstrip('/'):
            abort(403)


@app.get('/')
def index():
    return render_template('index.html')


@app.get('/api/health')
def health():
    return jsonify(service='face-library', ready=True)


@app.get('/api/photos')
def photos():
    with db() as conn:
        result = []
        for photo in conn.execute('SELECT * FROM photos ORDER BY rowid DESC'):
            item = dict(photo)
            item['faces'] = [dict(f) for f in conn.execute(
                'SELECT id, tag FROM faces WHERE photo_id=? ORDER BY rowid', (photo['id'],))]
            result.append(item)
    return jsonify(result)


@app.post('/api/upload')
def upload():
    mode = request.form.get('mode', 'Balanced')
    model = request.form.get('detector', 'YuNet')
    if model not in DETECTORS:
        return jsonify(error='Choose YuNet, SCRFD-2.5G, or Legacy SSD.'), 400
    if mode not in MODES:
        return jsonify(error='Choose Strict, Balanced, or Sensitive detection.'), 400
    files = request.files.getlist('images')
    if not files:
        return jsonify(error='Select at least one image.'), 400
    results = []
    for file in files:
        try:
            with Image.open(file.stream) as original:
                if original.width * original.height > 30_000_000:
                    raise ValueError('Image exceeds 30 megapixels')
                img = ImageOps.exif_transpose(original).convert('RGB')
                img.thumbnail((2400, 2400))
            boxes = detector.detect(img, mode, model)
            photo_id = uuid.uuid4().hex
            img.save(DATA / f'{photo_id}.jpg', quality=90)
            face_ids = []
            try:
                with db() as conn:
                    conn.execute('INSERT INTO photos(id,name,detector,detection_mode) VALUES (?,?,?,?)',
                        (photo_id, file.filename or 'Photo', model, mode))
                    for x, y, w, h in boxes:
                        face_id = uuid.uuid4().hex
                        face_ids.append(face_id)
                        pad = int(max(w, h) * .18)
                        crop = img.crop((max(0, int(x)-pad), max(0, int(y)-pad),
                                         min(img.width, int(x+w)+pad), min(img.height, int(y+h)+pad)))
                        crop.thumbnail((240, 240))
                        crop.save(DATA / f'{face_id}.jpg', quality=90)
                        conn.execute('INSERT INTO faces(id, photo_id) VALUES (?,?)', (face_id, photo_id))
            except Exception:
                for item in [photo_id, *face_ids]:
                    (DATA / f'{item}.jpg').unlink(missing_ok=True)
                raise
            results.append(dict(name=file.filename, faces=len(boxes), ok=True))
        except RuntimeError as error:
            return jsonify(error=str(error)), 503
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            results.append(dict(name=file.filename, ok=False, error='Unsupported, damaged, or oversized image.'))
    return jsonify(results)


@app.get('/media/<item_id>')
def media(item_id):
    if len(item_id) != 32 or any(c not in '0123456789abcdef' for c in item_id):
        abort(404)
    path = DATA / f'{item_id}.jpg'
    if not path.is_file():
        abort(404)
    return send_file(path, mimetype='image/jpeg')


@app.post('/api/faces/<face_id>/tag')
def tag(face_id):
    payload = request.get_json(silent=True) or {}
    value = payload.get('tag', '')
    if not isinstance(value, str) or len(value) > 80:
        return jsonify(error='Tags must be text, up to 80 characters.'), 400
    with db() as conn:
        if not conn.execute('UPDATE faces SET tag=? WHERE id=?', (value.strip(), face_id)).rowcount:
            abort(404)
    return jsonify(ok=True)


@app.delete('/api/faces/<face_id>')
def remove_face(face_id):
    with db() as conn:
        row = conn.execute('SELECT id FROM faces WHERE id=?', (face_id,)).fetchone()
        if row is None:
            abort(404)
        conn.execute('DELETE FROM faces WHERE id=?', (face_id,))
    (DATA / (row['id'] + '.jpg')).unlink(missing_ok=True)
    return jsonify(ok=True)


@app.errorhandler(413)
def too_large(error):
    return jsonify(error='Upload is too large. Keep each batch below 40 MB.'), 413


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
