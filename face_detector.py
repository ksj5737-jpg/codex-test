"""Generic face localization only; no identity embeddings or face matching."""
from pathlib import Path
import threading

import cv2
import numpy as np

MODES = {'Strict': 0.95, 'Balanced': 0.80, 'Sensitive': 0.60}


class FaceDetector:
    def __init__(self):
        models = Path(__file__).parent / 'models'
        self.net = cv2.dnn.readNetFromCaffe(str(models / 'deploy.prototxt'),
            str(models / 'res10_300x300_ssd_iter_140000.caffemodel'))
        self.lock = threading.Lock()

    def detect(self, image, mode='Balanced'):
        threshold = MODES[mode]
        bgr = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
        height, width = bgr.shape[:2]
        # Full-frame pass plus overlapping tiles for smaller faces in large photos.
        regions = [(0, 0, width, height)]
        if max(width, height) > 900:
            tile_w, tile_h = min(width, 640), min(height, 640)
            xs = sorted(set(range(0, width-tile_w+1, max(1, tile_w*3//4))) | {width-tile_w})
            ys = sorted(set(range(0, height-tile_h+1, max(1, tile_h*3//4))) | {height-tile_h})
            regions += [(x, y, tile_w, tile_h) for y in ys for x in xs]
        boxes, scores = [], []
        with self.lock:
            for ox, oy, rw, rh in regions:
                crop = bgr[oy:oy+rh, ox:ox+rw]
                blob = cv2.dnn.blobFromImage(crop, 1.0, (300, 300), (104, 177, 123), crop=False)
                self.net.setInput(blob)
                detections = self.net.forward().reshape(-1, 7)
                for detection in detections:
                    score = float(detection[2])
                    if not np.isfinite(detection).all() or score < threshold:
                        continue
                    x1, y1, x2, y2 = detection[3:7] * [rw, rh, rw, rh]
                    x1, y1 = max(ox, int(x1)+ox), max(oy, int(y1)+oy)
                    x2, y2 = min(ox+rw, int(x2)+ox), min(oy+rh, int(y2)+oy)
                    if x2-x1 < 20 or y2-y1 < 20:
                        continue
                    boxes.append([x1, y1, x2-x1, y2-y1])
                    scores.append(score)
        if not boxes:
            return []
        indices = cv2.dnn.NMSBoxes(boxes, scores, threshold, .3)
        return [tuple(boxes[int(i)]) for i in np.asarray(indices).reshape(-1)]
