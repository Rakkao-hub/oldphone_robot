// people.js : จำหน้าคน (face-api, MIT: phone/vendor/faceapi/ โหลดด้วย get_vendor.sh)
//
//   เห็นหน้า -> ลายนิ้วมือหน้า 128 ตัว -> เทียบกับคนที่จำไว้ (ระยะห่างยิ่งน้อยยิ่งเป็นคนเดียวกัน)
//     ใกล้กว่า SAME ติดกัน 2 ครั้ง        -> onSeen(ชื่อ)        (face.html ทักทาย ไม่ทักคนเดิมซ้ำบ่อย ๆ)
//     ห่างกว่า DIFFERENT ติดกัน 3 ครั้ง  -> onStranger(หน้า)    (face.html ถามชื่อ แล้วส่งหน้าให้ brain.py รอคำตอบ)
//     อยู่ระหว่างกลาง                      -> ยังไม่แน่ใจ ไม่ทำอะไร
// ทำงานเฉพาะตอนกล้องเห็นหน้าคน (MediaPipe จับได้) และดูทุก ~1.2 วิ เพื่อไม่ให้มือถือร้อน
// หน้าที่เล็กเกินไป (คนอยู่ไกล) ไม่เอามาเทียบ เพราะลายนิ้วมือไม่แม่น

const MODEL = '/vendor/faceapi';
const SAME = 0.5;         // ระยะห่างน้อยกว่านี้ = คนเดียวกัน
const DIFFERENT = 0.6;    // มากกว่านี้กับทุกคน = ไม่รู้จัก
const MIN_FACE = 0.18;    // หน้าต้องสูงอย่างน้อยเท่านี้ของภาพ
const EVERY_MS = 1200;
const LOST_MS = 4000;     // ไม่เห็นหน้านานเท่านี้ = คนเดิมไปแล้ว เริ่มนับใหม่

export async function createPeople({ video, report = () => { }, faceVisible = () => true, canLook = () => true,
                                     onSeen = () => { }, onStranger = () => { } }) {
  const faceapi = await import('/vendor/faceapi/face-api.esm.js');
  await faceapi.tf.ready();
  await Promise.all([
    faceapi.nets.tinyFaceDetector.loadFromUri(MODEL),
    faceapi.nets.faceLandmark68TinyNet.loadFromUri(MODEL),
    faceapi.nets.faceRecognitionNet.loadFromUri(MODEL),
  ]);
  const options = new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 });
  let known = [];   // [{ name, vecs: [Float32Array] }]
  let track = newTrack(), busy = false, stopped = false;
  const stats = { looks: 0, ms: 0 };

  function newTrack() { return { samples: [], hits: {}, strange: 0, lastSeen: 0 }; }

  async function refresh() {
    try {
      const r = await fetch('/api/people/list', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
      const { people } = await r.json();
      known = Object.entries(people || {}).map(([name, vs]) => ({ name, vecs: vs.map(v => Float32Array.from(v)) }));
    } catch (_) { }
  }

  // ลายนิ้วมือของหน้าที่ใหญ่ที่สุดในภาพตอนนี้ หรือ null
  async function describe() {
    const t0 = performance.now();
    const det = await faceapi.detectSingleFace(video, options).withFaceLandmarks(true).withFaceDescriptor();
    stats.looks++; stats.ms += performance.now() - t0;
    if (!det || det.detection.box.height / video.videoHeight < MIN_FACE) return null;
    return det.descriptor;
  }

  function nearest(d) {
    let best = { name: null, dist: Infinity };
    for (const p of known) for (const v of p.vecs) {
      const dist = faceapi.euclideanDistance(d, v);
      if (dist < best.dist) best = { name: p.name, dist };
    }
    return best;
  }

  async function tick() {
    if (stopped) return;
    const now = performance.now();
    if (!busy && faceVisible() && canLook()) {
      busy = true;
      try {
        const d = await describe();
        if (d) {
          if (now - track.lastSeen > LOST_MS) track = newTrack();
          track.lastSeen = now;
          track.samples = [...track.samples, d].slice(-8);
          const best = nearest(d);
          if (best.dist < SAME) {
            track.strange = 0;
            track.hits[best.name] = (track.hits[best.name] || 0) + 1;
            if (track.hits[best.name] >= 2) onSeen(best.name, best.dist);
          } else if (best.dist > DIFFERENT && ++track.strange >= 3) {
            onStranger(track.samples.map(v => Array.from(v, x => Math.round(x * 1e5) / 1e5)));
          }
        }
      } catch (e) {
        report('จำหน้า: ' + (e.message || e));
      } finally { busy = false; }
    }
    setTimeout(tick, EVERY_MS);
  }

  await refresh();
  report(`จำหน้าพร้อม: รู้จัก ${known.length} คน`);
  tick();

  return {
    refresh,
    // เพิ่งได้ชื่อคนตรงหน้า (ตอบคำถาม) -> ถือว่าคนนี้คือคนนั้นแล้ว ไม่ถามซ้ำ
    async met(name) { await refresh(); track.hits[name] = 2; track.strange = 0; },
    // "ผมชื่อ..." -> เก็บหน้าคนตรงหน้า 5 ภาพ (ราว 3 วิ) แล้วจำคู่กับชื่อ
    async learn(name) {
      const vecs = [];
      for (let i = 0; i < 12 && vecs.length < 5; i++) {
        while (busy) await new Promise(r => setTimeout(r, 50));
        busy = true;
        try { const d = await describe(); if (d) vecs.push(Array.from(d, x => Math.round(x * 1e5) / 1e5)); }
        finally { busy = false; }
        await new Promise(r => setTimeout(r, 500));
      }
      if (vecs.length < 2) return false;
      const r = await fetch('/api/people', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, vectors: vecs })
      });
      const ok = !!(await r.json()).ok;
      if (ok) await this.met(name);
      return ok;
    },
    summary() {
      const t = `จำหน้า: ดู ${stats.looks} ครั้ง เฉลี่ย ${stats.looks ? (stats.ms / stats.looks).toFixed(0) : 0} ms`;
      stats.looks = 0; stats.ms = 0;
      return t;
    },
    stop() { stopped = true; },
  };
}
