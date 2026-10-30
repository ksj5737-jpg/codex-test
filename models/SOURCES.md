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

## YuNet (default)

- Model: `face_detection_yunet_2023mar.onnx`, 232589 bytes.
- Official source: https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet
- SHA-256 from the official Git LFS pointer:
  `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`.
- The Windows launcher fetches this file through `download_models.py` and checks
  that exact hash before installation. No TLS or checksum checks are disabled.
- Model directory license: MIT, copyright Shiqi Yu; see `LICENSE-YuNet`.

## SCRFD-2.5G

- Official release: https://github.com/deepinsight/insightface/releases/tag/v0.7
- Pack: `buffalo_m.zip`. Only `buffalo_m/det_2.5g.onnx` is included here.
  Other models in that pack are not included or used by this app.
- Detector size: 3292009 bytes. SHA-256 of the extracted official asset:
  `041f73f47371333d1d17a6fee6c8ab4e6aecabefe398ff32cca4e2d5eaee0af9`.
- Model mapping and restrictions: https://github.com/deepinsight/insightface/blob/master/model_zoo/README.md
- Upstream states: **ALL models are available for non-commercial research
  purposes only.** This applies to the pretrained weights, independently of
  the license of the ONNX runtime or application code. Do not treat this download
  as permission for commercial deployment; obtain the appropriate model license.
- Preprocessing: RGB NCHW, `(pixel - 127.5) / 128`, 640x640 padded input.
  Only score and bounding-box heads are decoded; landmark outputs are ignored.
