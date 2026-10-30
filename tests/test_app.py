import io
import os
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

storage = tempfile.TemporaryDirectory()
os.environ['PHOTO_DATA_DIR'] = storage.name
import app as module


class PhotoWorkflow(unittest.TestCase):
    def setUp(self):
        self.client = module.app.test_client()
        with module.db() as conn:
            conn.execute('DELETE FROM faces')
            conn.execute('DELETE FROM photos')

    def image(self):
        data = io.BytesIO()
        Image.new('RGB', (100, 100), 'white').save(data, format='PNG')
        data.seek(0)
        return data

    def test_import_tag_and_persistence(self):
        with patch.object(module, 'detector') as detector:
            detector.detectMultiScale.return_value = [(10, 10, 40, 40)]
            response = self.client.post('/api/upload', data={'images': (self.image(), 'sample.png')})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]['faces'], 1)
        photo = self.client.get('/api/photos').json[0]
        with self.client.get('/media/' + photo['id']) as response:
            self.assertEqual(response.status_code, 200)
        face = photo['faces'][0]
        with self.client.get('/media/' + face['id']) as response:
            self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.post('/api/faces/' + face['id'] + '/tag', json={'tag': 'Alex'}).status_code, 200)
        self.assertEqual(module.app.test_client().get('/api/photos').json[0]['faces'][0]['tag'], 'Alex')
        self.client.post('/api/faces/' + face['id'] + '/tag', json={'tag': ''})
        self.assertEqual(self.client.get('/api/photos').json[0]['faces'][0]['tag'], '')

    def test_real_detector_no_face(self):
        response = self.client.post('/api/upload', data={'images': (self.image(), 'blank.png')})
        self.assertEqual(response.json[0]['faces'], 0)
        self.assertTrue(response.json[0]['ok'])

    def test_invalid_upload(self):
        self.assertEqual(self.client.post('/api/upload').status_code, 400)
        response = self.client.post('/api/upload', data={'images': (io.BytesIO(b'invalid'), 'bad.png')})
        self.assertFalse(response.json[0]['ok'])
        self.assertEqual(self.client.get('/api/photos').json, [])

    def test_local_security_and_tag_validation(self):
        self.assertEqual(self.client.get('/api/health').json, {'service': 'face-library', 'ready': True})
        self.assertEqual(self.client.get('/', headers={'Host': 'example.com'}).status_code, 403)
        self.assertEqual(self.client.post('/api/upload', headers={'Origin': 'https://example.com'}).status_code, 403)
        self.assertEqual(self.client.post('/api/faces/unknown/tag', json={'tag': ['bad']}).status_code, 400)
        self.assertEqual(self.client.post('/api/faces/unknown/tag', json={'tag': 'Alex'}).status_code, 404)
        self.assertEqual(self.client.get('/media/not-a-valid-id').status_code, 404)
        self.assertEqual(self.client.get('/').status_code, 200)


if __name__ == '__main__':
    unittest.main()
