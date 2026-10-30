import threading
import unittest
from unittest.mock import Mock

import numpy as np
from PIL import Image
from face_detector import FaceDetector


class DetectorFiltering(unittest.TestCase):
    def test_scores_duplicates_and_invalid_boxes(self):
        detector = FaceDetector.__new__(FaceDetector)
        detector.lock = threading.Lock()
        detector.net = Mock()
        detector.net.forward.return_value = np.array([[[
            [0, 1, .98, .1, .1, .5, .5],
            [0, 1, .97, .11, .11, .51, .51],
            [0, 1, .7, .6, .6, .9, .9],
            [0, 1, .99, .9, .9, .1, .1],
            [0, 1, float('nan'), .2, .2, .6, .6],
        ]]], dtype=np.float32)
        image = Image.new('RGB', (200, 200), 'white')
        self.assertEqual(len(detector.detect(image, 'Strict')), 1)
        self.assertEqual(len(detector.detect(image, 'Balanced')), 1)
        self.assertEqual(len(detector.detect(image, 'Sensitive')), 2)


if __name__ == '__main__':
    unittest.main()
