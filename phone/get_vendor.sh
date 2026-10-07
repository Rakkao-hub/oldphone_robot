#!/usr/bin/env bash
# โหลด MediaPipe (ตัวจับหน้าและตัวจำของของ Google, Apache-2.0) และ face-api (จำหน้าคน, MIT) มาเก็บใน phone/vendor/ ครั้งเดียว
# หลังจากนั้นแซนจับหน้าได้แม้ไม่มีอินเทอร์เน็ต
set -e
cd "$(dirname "$0")"
VER=1.0.1
B=https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@$VER
mkdir -p vendor/wasm
curl -sfL -o vendor/vision_bundle.mjs "$B/vision_bundle.mjs"
curl -sfL -o vendor/wasm/vision_wasm_internal.js "$B/wasm/vision_wasm_internal.js"
curl -sfL -o vendor/wasm/vision_wasm_internal.wasm "$B/wasm/vision_wasm_internal.wasm"
curl -sfL -o vendor/face.tflite \
  https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite
# ตัวแปลงภาพเป็นลายนิ้วมือ (ใช้จำของและภารกิจหาของ)
curl -sfL -o vendor/embedder.tflite \
  https://storage.googleapis.com/mediapipe-models/image_embedder/mobilenet_v3_small/float32/1/mobilenet_v3_small.tflite
# จำหน้าคน: face-api (MIT) ตัวจับหน้า + จุดบนหน้า + ลายนิ้วมือหน้า (~8 MB)
F=https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.15
mkdir -p vendor/faceapi
curl -sfL -o vendor/faceapi/face-api.esm.js "$F/dist/face-api.esm.js"
for m in tiny_face_detector_model face_landmark_68_tiny_model face_recognition_model; do
  curl -sfL -o "vendor/faceapi/$m-weights_manifest.json" "$F/model/$m-weights_manifest.json"
  curl -sfL -o "vendor/faceapi/$m.bin" "$F/model/$m.bin"
done
echo "โหลด MediaPipe และ face-api เสร็จแล้ว"
