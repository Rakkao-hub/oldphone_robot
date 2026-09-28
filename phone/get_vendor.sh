#!/usr/bin/env bash
# โหลด MediaPipe (ตัวจับหน้าของ Google, Apache-2.0) มาเก็บใน phone/vendor/ ครั้งเดียว
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
echo "โหลด MediaPipe เสร็จแล้ว"
