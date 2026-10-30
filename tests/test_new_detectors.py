import hashlib
import io
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

import numpy as np
from PIL import Image
from face_detector import FaceDetector, YuNet, SCRFD
from model_assets import valid_model


class AdapterTests(unittest.TestCase):
    def test_yunet_coordinates_and_threshold(self):
        detector = YuNet.__new__(YuNet)
        detector.model = Mock()
        row = np.zeros((1, 15), dtype=np.float32)
        row[0, [0, 1, 2, 3, 14]] = [64, 32, 128, 96, .9]
        detector.model.detect.return_value = (1, row)
        result = detector.infer(np.zeros((100, 200, 3), np.uint8), .85)
        np.testing.assert_allclose(result[0], [20, 10, 60, 40, .9], rtol=1e-6)
        detector.model.setScoreThreshold.assert_called_once_with(.85)
        detector.model.detect.return_value = (0, None)
        self.assertEqual(detector.infer(np.zeros((100, 200, 3), np.uint8), .85).shape, (0, 5))

    def test_scrfd_anchor_decoding_and_rgb_normalization(self):
        detector = SCRFD.__new__(SCRFD)
        detector.session = Mock()
        detector.input_name = 'input.1'
        sizes = [(640//stride)**2 * 2 for stride in (8, 16, 32)]
        scores = [np.zeros((n, 1), np.float32) for n in sizes]
        distances = [np.zeros((n, 4), np.float32) for n in sizes]
        index = (10 * 80 + 20) * 2
        scores[0][index] = .9
        distances[0][index] = [1, 2, 3, 4]
        detector.session.run.return_value = scores + distances + [np.zeros((n, 10), np.float32) for n in sizes]
        image = np.full((640, 640, 3), [0, 127, 255], dtype=np.uint8)
        result = detector.infer(image, .6)
        np.testing.assert_allclose(result[0], [152, 64, 184, 112, .9], rtol=1e-6)
        tensor = detector.session.run.call_args.args[1]['input.1']
        np.testing.assert_allclose(tensor[0, :, 0, 0], (np.array([255, 127, 0])-127.5)/128)

    def test_nms_and_model_specific_thresholds(self):
        detector = FaceDetector()
        model = Mock()
        model.infer.return_value = np.array([[20, 20, 100, 100, .99],
            [22, 22, 102, 102, .98], [130, 130, 180, 180, .7]])
        detector.models['YuNet'] = model
        image = Image.new('RGB', (200, 200))
        self.assertEqual(len(detector.detect(image, 'Strict', 'YuNet')), 1)
        self.assertEqual(len(detector.detect(image, 'Sensitive', 'YuNet')), 2)
        self.assertEqual(model.infer.call_args.args[1], .65)

    @unittest.skipUnless(valid_model('YuNet'), 'Verified YuNet model is not installed; run download_models.py')
    def test_real_yunet_blank_image(self):
        self.assertEqual(FaceDetector().detect(Image.new('RGB', (320, 240), 'white'), model='YuNet'), [])


class ModelDownloadTests(unittest.TestCase):
    def test_hash_verification_and_atomic_install(self):
        import model_assets
        import download_models
        data = b'test model bytes'
        with tempfile.TemporaryDirectory() as directory:
            assets = {'YuNet': ('test.onnx', hashlib.sha256(data).hexdigest())}
            with patch.object(model_assets, 'MODEL_DIR', Path(directory)), patch.object(download_models, 'MODEL_DIR', Path(directory)), patch.dict(model_assets.ASSETS, assets):
                with patch('urllib.request.urlopen', return_value=io.BytesIO(b'bad download')):
                    with self.assertRaises(ValueError):
                        download_models.install_yunet()
                self.assertEqual(list(Path(directory).iterdir()), [])
                with patch('urllib.request.urlopen', return_value=io.BytesIO(data)):
                    download_models.install_yunet()
                self.assertTrue(model_assets.valid_model('YuNet'))
                with patch('urllib.request.urlopen') as fetch:
                    download_models.install_yunet()
                    fetch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
