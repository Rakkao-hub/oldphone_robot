// mission.js : สอนแซนจำของ ภารกิจออกตามหาของ และเครื่องมือจดลายนิ้วมือของ (wonder.js ใช้ด้วย)
//
// ลายนิ้วมือภาพ = MediaPipe Image Embedder (MobileNet-V3 small, phone/vendor/embedder.tflite) แปลงภาพเป็นตัวเลขชุดหนึ่ง
// ภาพของชิ้นเดียวกันจะได้ตัวเลขคล้ายกัน (ความคล้าย = cosine 0 ถึง 1)
//
// สอน: ถือของให้กล้องดูราว 8 วิ จดลายนิ้วมือจากกลางภาพหลายมุม และตั้งเกณฑ์ "ใช่ของชิ้นนี้" ของแต่ละชิ้นเอง
//      (ระหว่างความคล้ายของภาพของกับตัวเอง และความคล้ายกับฉากรอบ ๆ ที่ขอบภาพ)
// หา: ตัดภาพเป็นหลายช่องหลายขนาด เทียบทุกช่องกับของที่จำไว้
//      ไม่เจอ -> หมุนทีละ 20 องศา หยุดมองทุกครั้ง จนครบรอบ แล้วเดินไปที่ใหม่ หมุนหาอีก
//      เห็นครั้งแรก -> หันเข้าหานิดหนึ่งแล้วมองซ้ำ เห็นซ้ำ = เจอแน่ หยุดทันที แล้วประกาศ (กันเห็นของคล้าย ๆ แวบเดียว)
import { sleep, randInt, side } from './motion.js';

const TEACH_ROUNDS = 18, TEACH_EVERY_MS = 450;
const TH_MIN = 0.55, TH_MAX = 0.9;   // เกณฑ์ "ใช่" ต้องอยู่ในช่วงนี้เสมอ
const MAX_MS = 180000, MAX_STEPS = 80;
const SCAN_TURN = 20, SCANS_PER_SPOT = 18;   // หมุนหาทีละ 20 องศา 18 ครั้ง = รอบตัว (ทีละน้อย ภาพไม่เบลอ ไม่ดูหมุนไว)
const SCAN_LOOK_MS = 600;                    // หมุนแต่ละครั้งแล้วหยุดนิ่งมองเพิ่มอีกเท่านี้
const CENTERED = 0.3;                        // ของอยู่ห่างกลางภาพไม่เกินนี้ ถือว่าตรงหน้าแล้ว
const HITS_TO_FOUND = 2;                     // ต้องเห็นติดกันกี่ครั้งถึงเชื่อ

// ช่องที่ใช้ดู: [กลาง x, กลาง y, ด้าน] เทียบกับความสูงภาพ (สี่เหลี่ยมจัตุรัส) size บอกว่าของน่าจะอยู่ใกล้แค่ไหน
const CROPS = [
  { cx: 0.5, cy: 0.5, s: 0.9, size: 'near' },
  ...[0.3, 0.5, 0.7].map(cx => ({ cx, cy: 0.5, s: 0.6, size: 'mid' })),
  ...[0.2, 0.4, 0.6, 0.8].map(cx => ({ cx, cy: 0.55, s: 0.4, size: 'far' })),
  ...[0.15, 0.32, 0.5, 0.68, 0.85].map(cx => ({ cx, cy: 0.55, s: 0.25, size: 'far' })),   // ของอยู่ไกล (ราว 1-2 เมตร)
];
const TEACH_CROPS = [{ cx: 0.5, cy: 0.5, s: 0.7 }, { cx: 0.5, cy: 0.5, s: 0.5 }];
const EDGE_CROPS = [{ cx: 0.12, cy: 0.2, s: 0.3 }, { cx: 0.88, cy: 0.2, s: 0.3 }, { cx: 0.12, cy: 0.8, s: 0.3 }, { cx: 0.88, cy: 0.8, s: 0.3 }];

let embedderP = null;
function getEmbedder() {
  embedderP ||= (async () => {
    const { FilesetResolver, ImageEmbedder } = await import('/vendor/vision_bundle.mjs');
    const files = await FilesetResolver.forVisionTasks('/vendor/wasm');
    const make = delegate => ImageEmbedder.createFromOptions(files, {
      baseOptions: { modelAssetPath: '/vendor/embedder.tflite', delegate },
      runningMode: 'IMAGE', l2Normalize: true, quantize: false,
    });
    return make('GPU').catch(() => make('CPU'));
  })();
  embedderP.catch(() => { embedderP = null; });   // โหลดไม่ได้ ครั้งหน้าลองใหม่
  return embedderP;
}

const canvas = document.createElement('canvas');
canvas.width = canvas.height = 224;
const ctx = canvas.getContext('2d', { willReadFrequently: true });

function cropRect(video, c) {
  const vw = video.videoWidth, vh = video.videoHeight, side = c.s * vh;
  const x = Math.max(0, Math.min(vw - side, c.cx * vw - side / 2));
  const y = Math.max(0, Math.min(vh - side, c.cy * vh - side / 2));
  return { x, y, w: side, h: side };
}

function embed(embedder, video, c) {
  const r = cropRect(video, c);
  ctx.drawImage(video, r.x, r.y, r.w, r.h, 0, 0, 224, 224);
  return Float32Array.from(embedder.embed(canvas).embeddings[0].floatEmbedding);
}

function dot(a, b) {
  let s = 0;
  for (let i = 0; i < a.length; i++) s += a[i] * b[i];
  return s;
}
const bestMatch = (e, vectors) => vectors.reduce((m, v) => Math.max(m, dot(e, v)), -1);
const mean = xs => xs.reduce((a, b) => a + b, 0) / Math.max(1, xs.length);

// ---------------------------------------------------------------- จดลายนิ้วมือของ (ใช้ทั้งตอนสอน และตอนแซนสงสัยของเอง)
// ดูช่อง crops ทุก every มิลลิวินาที rounds รอบ แล้วตั้งเกณฑ์ "ใช่ของชิ้นนี้"
// (ระหว่างความคล้ายของภาพของกับตัวเอง และความคล้ายกับฉากที่ขอบภาพ)
export async function capture({ video, crops = TEACH_CROPS, rounds = TEACH_ROUNDS, every = TEACH_EVERY_MS,
                                onProgress = () => { }, shouldStop = () => false }) {
  const embedder = await getEmbedder();
  const samples = [], edges = [], per = crops.length;
  for (let i = 0; i < rounds && !shouldStop(); i++) {
    for (const c of crops) samples.push(embed(embedder, video, c));
    if (i % 3 === 0) for (const c of EDGE_CROPS) edges.push(embed(embedder, video, c));
    onProgress((i + 1) / rounds);
    await sleep(every);
  }
  if (shouldStop() || samples.length < 6) return null;
  const self = [];   // ไม่นับคู่ที่มาจากรอบเดียวกัน
  for (let i = 0; i < samples.length; i += per) for (let j = i + per; j < samples.length; j += per) self.push(dot(samples[i], samples[j]));
  const selfSim = mean(self), edgeSim = mean(edges.map(e => bestMatch(e, samples)));
  const th = Math.max(TH_MIN, Math.min(TH_MAX, (selfSim + edgeSim) / 2));
  return { samples, th, selfSim, edgeSim, clear: selfSim - edgeSim > 0.05 };
}

// ลายนิ้วมือแบบส่งเป็น JSON ได้ (ปัดทศนิยม ลดขนาด)
export const toLists = samples => samples.map(v => Array.from(v, x => Math.round(x * 1e4) / 1e4));

// รูปของช่องหนึ่งในภาพ (JPEG เล็ก ๆ) ไว้โชว์ตอนถามคน
export function snapshot(video, c, size = 240) {
  const cv = document.createElement('canvas');
  cv.width = cv.height = size;
  const r = cropRect(video, c);
  cv.getContext('2d').drawImage(video, r.x, r.y, r.w, r.h, 0, 0, size, size);
  return cv.toDataURL('image/jpeg', 0.7);
}

// ---------------------------------------------------------------- สอน
export async function teach({ name, video, onProgress = () => { }, shouldStop = () => false, report = () => { } }) {
  const got = await capture({ video, onProgress, shouldStop });
  if (!got) return { ok: false, why: 'stopped' };
  report(`จำ${name}: คล้ายกันเอง ${got.selfSim.toFixed(2)} คล้ายฉากรอบ ๆ ${got.edgeSim.toFixed(2)} -> เกณฑ์ ${got.th.toFixed(2)}`);
  const r = await fetch('/api/items', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, th: got.th, vectors: toLists(got.samples) }),
  });
  const res = await r.json();
  return { ok: !!res.ok, ...got };
}

// ---------------------------------------------------------------- ภารกิจหา
// มองหนึ่งครั้ง: คืนช่องที่คล้ายของที่สุด { score, x (-1 ซ้ายภาพ .. 1 ขวาภาพ), size, rect }
async function look(video, vectors) {
  const embedder = await getEmbedder();
  let best = { score: -1 };
  for (const c of CROPS) {
    const score = bestMatch(embed(embedder, video, c), vectors);
    if (score > best.score) best = { score, x: c.cx * 2 - 1, size: c.size, rect: cropRect(video, c) };
  }
  return best;
}

export async function findItem({ item, video, motion, shouldStop = () => false, onSee = () => { }, report = () => { } }) {
  const vectors = item.vectors.map(v => Float32Array.from(v));
  const t0 = performance.now();
  let steps = 0, scans = 0, hits = 0, bestEver = 0;
  const go = async prog => {
    steps++;
    const r = await motion.step('mission', prog);
    if (!r.ok && r.why === 'busy') { await sleep(1000); return r; }
    if (!r.ok) throw new Error(r.why);
    return r;
  };
  try {
    await getEmbedder();
    while (steps < MAX_STEPS && performance.now() - t0 < MAX_MS) {
      if (shouldStop()) return { found: false, why: 'stopped' };
      const seen = await look(video, vectors);
      bestEver = Math.max(bestEver, seen.score);
      const hit = seen.score >= item.th;
      onSee(seen, hit);
      if (hit) {
        hits++;
        scans = 0;
        if (hits >= HITS_TO_FOUND) return { found: true, seen, score: seen.score, steps };   // เห็นซ้ำแล้ว เจอแน่ หยุดเลย
        if (Math.abs(seen.x) > CENTERED) await go((seen.x < 0 ? 'L' : 'R') + Math.round(5 + Math.abs(seen.x) * 25));
        else await sleep(SCAN_LOOK_MS);   // อยู่กลางภาพแล้ว มองซ้ำเฉย ๆ
        continue;
      }
      hits = 0;
      if (scans < SCANS_PER_SPOT) {
        scans++;
        await go('R' + SCAN_TURN);
        await sleep(SCAN_LOOK_MS);
      } else {   // หมุนครบรอบแล้วไม่เจอ ไปหาที่อื่น
        scans = 0;
        await go(side() + randInt(60, 120));
        const r = await go('F30');
        if (r.stuck) { await go('B15'); await go(side() + randInt(100, 160)); }
      }
    }
    return { found: false, why: 'timeout', best: bestEver };
  } catch (e) {
    return { found: false, why: e.message, best: bestEver };
  } finally {
    report(`ภารกิจหา${item.name}: ${steps} ท่า ความคล้ายสูงสุด ${bestEver.toFixed(2)} (เกณฑ์ ${item.th})`);
  }
}

export const warmUp = () => getEmbedder().then(() => true, e => { throw e; });
