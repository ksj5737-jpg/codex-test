"""Pinned face-detection assets; all downloads use HTTPS with verification."""
import hashlib
from pathlib import Path

MODEL_DIR = Path(__file__).parent / 'models'
ASSETS = {
    'YuNet': ('face_detection_yunet_2023mar.onnx',
        '8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4'),
    'SCRFD-2.5G': ('det_2.5g.onnx',
        '041f73f47371333d1d17a6fee6c8ab4e6aecabefe398ff32cca4e2d5eaee0af9'),
}


def valid_model(name):
    filename, expected = ASSETS[name]
    path = MODEL_DIR / filename
    return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected


def verified_path(name):
    if not valid_model(name):
        raise RuntimeError(f'{name} weights are missing or failed verification. Run download_models.py from the project folder.')
    return str(MODEL_DIR / ASSETS[name][0])
