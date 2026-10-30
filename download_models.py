"""Fetch the tiny YuNet asset. SCRFD detection-only weights ship with the app."""
import hashlib
import os
import tempfile
import urllib.request
from pathlib import Path

from model_assets import ASSETS, MODEL_DIR, valid_model

YUNET_URL = ('https://github.com/opencv/opencv_zoo/raw/refs/heads/main/'
             'models/face_detection_yunet/face_detection_yunet_2023mar.onnx')


def install_yunet(url=YUNET_URL):
    if valid_model('YuNet'):
        return
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    filename, expected = ASSETS['YuNet']
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=MODEL_DIR, suffix='.download', delete=False) as output:
            temporary = Path(output.name)
            with urllib.request.urlopen(url, timeout=60) as response:
                content = response.read(1_000_001)
            if len(content) > 1_000_000 or hashlib.sha256(content).hexdigest() != expected:
                raise ValueError('YuNet checksum mismatch; the download was not installed.')
            output.write(content)
        os.replace(temporary, MODEL_DIR / filename)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    try:
        print('Checking models. SCRFD pretrained weights: non-commercial research only.')
        if not valid_model('SCRFD-2.5G'):
            raise RuntimeError('SCRFD weights are missing or damaged. Re-extract the complete app ZIP.')
        install_yunet()
        print('YuNet and SCRFD-2.5G weights verified. Future detection works offline.')
    except Exception as error:
        print(f'Model setup failed: {error}')
        raise SystemExit(1)
