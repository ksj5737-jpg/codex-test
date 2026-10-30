"""CPU face localization only; no identity embeddings or face matching."""
from pathlib import Path
import os
import threading

import cv2
import numpy as np
from legacy_detector import MODES
from model_assets import verified_path

DETECTORS = ('YuNet', 'SCRFD-2.5G', 'Legacy SSD')
THRESHOLDS = {
    'YuNet': {'Strict': .95, 'Balanced': .85, 'Sensitive': .65},
    'SCRFD-2.5G': {'Strict': .80, 'Balanced': .60, 'Sensitive': .35},
}
MODEL_DIR = Path(__file__).parent / 'models'


def letterbox(bgr, size=640):
    height, width = bgr.shape[:2]
    ratio = min(size / height, size / width)
    rw, rh = max(1, int(width * ratio)), max(1, int(height * ratio))
    padded = np.zeros((size, size, 3), dtype=np.uint8)
    padded[:rh, :rw] = cv2.resize(bgr, (rw, rh))
    return padded, rw / width, rh / height


class YuNet:
    def __init__(self):
        self.model = cv2.FaceDetectorYN.create(
            verified_path('YuNet'), '', (640, 640), .85, .3, 5000)

    def infer(self, bgr, threshold):
        padded, sx, sy = letterbox(bgr)
        self.model.setScoreThreshold(threshold)
        _, faces = self.model.detect(padded)
        if faces is None:
            return np.empty((0, 5))
        # Discard landmarks. Only rectangles and detection scores are used.
        rows = faces[:, [0, 1, 2, 3, 14]].copy()
        rows[:, 2:4] += rows[:, :2]
        rows[:, [0, 2]] /= sx
        rows[:, [1, 3]] /= sy
        return rows


class SCRFD:
    def __init__(self):
        import onnxruntime as ort
        options = ort.SessionOptions()
        options.intra_op_num_threads = min(4, os.cpu_count() or 1)
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(verified_path('SCRFD-2.5G'),
            sess_options=options, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        if len(self.session.get_outputs()) != 9:
            raise RuntimeError('Expected official SCRFD-2.5G model with 9 outputs.')

    def infer(self, bgr, threshold):
        padded, sx, sy = letterbox(bgr)
        blob = cv2.dnn.blobFromImage(padded, 1 / 128, (640, 640), (127.5, 127.5, 127.5), swapRB=True)
        outputs = self.session.run(None, {self.input_name: blob})
        found = []
        for level, stride in enumerate((8, 16, 32)):
            scores = outputs[level].reshape(-1)
            distances = outputs[level+3].reshape(-1, 4) * stride
            ys, xs = np.mgrid[:640//stride, :640//stride]
            anchors = np.stack((xs, ys), axis=-1).reshape(-1, 2) * stride
            anchors = np.repeat(anchors, 2, axis=0)
            if len(scores) != len(anchors) or len(distances) != len(anchors):
                raise RuntimeError('Unexpected SCRFD output dimensions.')
            keep = (scores >= threshold) & np.isfinite(scores) & np.isfinite(distances).all(axis=1)
            centers, d, s = anchors[keep], distances[keep], scores[keep]
            if not len(s):
                continue
            boxes = np.column_stack((centers[:, 0]-d[:, 0], centers[:, 1]-d[:, 1],
                centers[:, 0]+d[:, 2], centers[:, 1]+d[:, 3], s))
            boxes[:, [0, 2]] /= sx
            boxes[:, [1, 3]] /= sy
            found.append(boxes)
        return np.vstack(found) if found else np.empty((0, 5))


class FaceDetector:
    def __init__(self):
        self.models = {}
        self.lock = threading.Lock()

    def detect(self, image, mode='Balanced', model='YuNet'):
        if model not in DETECTORS or mode not in MODES:
            raise ValueError('Unknown detector or detection mode')
        if model == 'Legacy SSD':
            from legacy_detector import FaceDetector as LegacyDetector
            with self.lock:
                if model not in self.models:
                    self.models[model] = LegacyDetector()
                return self.models[model].detect(image, mode)
        threshold = THRESHOLDS[model][mode]
        bgr = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
        height, width = bgr.shape[:2]
        regions = [(0, 0, width, height)]
        if max(width, height) > 900:
            tile_w, tile_h = min(width, 640), min(height, 640)
            xs = sorted(set(range(0, width-tile_w+1, max(1, tile_w*3//4))) | {width-tile_w})
            ys = sorted(set(range(0, height-tile_h+1, max(1, tile_h*3//4))) | {height-tile_h})
            regions += [(x, y, tile_w, tile_h) for y in ys for x in xs]
        boxes, scores = [], []
        with self.lock:
            if model not in self.models:
                try:
                    self.models[model] = {'YuNet': YuNet, 'SCRFD-2.5G': SCRFD}[model]()
                except Exception as error:
                    raise RuntimeError(f'Could not load {model}. Check the models folder and installed dependencies: {error}') from error
            for ox, oy, rw, rh in regions:
                rows = self.models[model].infer(bgr[oy:oy+rh, ox:ox+rw], threshold)
                for row in rows:
                    x1, y1, x2, y2, score = row
                    if not np.isfinite(row).all() or score < threshold:
                        continue
                    x1, y1 = max(ox, int(x1)+ox), max(oy, int(y1)+oy)
                    x2, y2 = min(ox+rw, int(x2)+ox), min(oy+rh, int(y2)+oy)
                    if x2-x1 < 20 or y2-y1 < 20:
                        continue
                    boxes.append([x1, y1, x2-x1, y2-y1])
                    scores.append(float(score))
        if not boxes:
            return []
        indices = cv2.dnn.NMSBoxes(boxes, scores, threshold, .3)
        return [tuple(boxes[int(i)]) for i in np.asarray(indices).reshape(-1)]
