# Bundled detector assets

These assets localize generic faces. They do not provide identity recognition.

- `res10_300x300_ssd_iter_140000.caffemodel`: official OpenCV third-party
  repository, branch `dnn_samples_face_detector_20170830`, commit
  `b2bfc75f6aea5b1f834ff0f0b865a7c18ff1459f`.
  Source: https://github.com/opencv/opencv_3rdparty/tree/b2bfc75f6aea5b1f834ff0f0b865a7c18ff1459f
  SHA-256: `2a56a11a57a4a295956b0660b4a3d76bbdca2206c4961cea8efe7d95c7cb2f2d`.
- `deploy.prototxt`: OpenCV sample configuration from
  https://github.com/opencv/opencv/blob/master/samples/dnn/face_detector/deploy.prototxt
  SHA-256 of the bundled copy:
  `dcd661dc48fc9de0a341db1f666a2164ea63a67265c7f779bc12d6b3f2fa67e9`.

The model download was compared byte-for-byte against a separate checkout of
the official model repository. No downloads are made during detection.
